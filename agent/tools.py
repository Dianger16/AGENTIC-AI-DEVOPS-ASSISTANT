# agent/tools.py
# LangChain tools the agent can call:
#   - analyze_logs       → scan pod logs for errors
#   - get_metrics        → query Prometheus for CPU/memory
#   - get_pod_status     → list pods and their states
#   - restart_pod        → delete a failing pod (K8s restarts it)
#   - scale_deployment   → scale replicas up or down
#   - trigger_pipeline   → trigger GitHub Actions workflow
#   - suggest_fix        → AI-generated fix recommendation

import os
import json
import logging
import requests
import base64
from datetime import datetime, timezone
from typing import Optional
from kubernetes import client, config
from langchain.tools import tool

logger = logging.getLogger(__name__)

# ── EKS Programmatic Auth & Token Caching ──────────────────────────────────────
import time
import yaml
import boto3
from botocore.signers import RequestSigner

_cached_token = None
_token_expiry = 0

def get_eks_token(cluster_name: str, region_name: str) -> str:
    global _cached_token, _token_expiry
    now = time.time()
    if _cached_token and now < _token_expiry - 60:
        return _cached_token
        
    session = boto3.Session()
    sts_client = session.client('sts', region_name=region_name)
    service_id = sts_client.meta.service_model.service_id
    event_emitter = session._session.get_component('event_emitter')
    
    signer = RequestSigner(
        service_id,
        region_name,
        'sts',
        'v4',
        session.get_credentials(),
        event_emitter
    )
    
    params = {
        'method': 'GET',
        'url': f'https://sts.{region_name}.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15',
        'body': {},
        'headers': {
            'x-k8s-aws-id': cluster_name
        },
        'context': {}
    }
    
    signed_url = signer.generate_presigned_url(
        params,
        region_name=region_name,
        expires_in=60,
        operation_name='GetCallerIdentity'
    )
    
    base64_url = base64.urlsafe_b64encode(signed_url.encode('utf-8')).decode('utf-8').rstrip('=')
    _cached_token = 'k8s-aws-v1.' + base64_url
    _token_expiry = now + 14 * 60
    
    try:
        update_local_kubeconfig(cluster_name, region_name, _cached_token)
    except Exception as e:
        logger.warning(f"Failed to update local kubeconfig: {e}")
        
    return _cached_token

def update_local_kubeconfig(cluster_name: str, region_name: str, token: str):
    kubeconfig_path = os.path.expanduser("~/.kube/config")
    try:
        import base64
        import boto3
        eks_client = boto3.client('eks', region_name=region_name)
        cluster_info = eks_client.describe_cluster(name=cluster_name)['cluster']
        endpoint = cluster_info['endpoint']
        ca_data = cluster_info['certificateAuthority']['data']
        
        try:
            with open(kubeconfig_path, "r") as f:
                kubeconfig = yaml.safe_load(f) or {}
        except Exception:
            kubeconfig = {}
            
        kubeconfig.setdefault("apiVersion", "v1")
        kubeconfig.setdefault("kind", "Config")
        kubeconfig.setdefault("clusters", [])
        kubeconfig.setdefault("contexts", [])
        kubeconfig.setdefault("users", [])
        
        cluster_name_key = f"eks-{cluster_name}"
        
        # Cluster
        cluster_found = False
        for cl in kubeconfig["clusters"]:
            if cl["name"] == cluster_name_key:
                cl["cluster"] = {"certificate-authority-data": ca_data, "server": endpoint}
                cluster_found = True
                break
        if not cluster_found:
            kubeconfig["clusters"].append({"name": cluster_name_key, "cluster": {"certificate-authority-data": ca_data, "server": endpoint}})
            
        # User
        user_found = False
        for usr in kubeconfig["users"]:
            if usr["name"] == cluster_name_key:
                usr["user"] = {"token": token}
                user_found = True
                break
        if not user_found:
            kubeconfig["users"].append({"name": cluster_name_key, "user": {"token": token}})
            
        # Context
        context_found = False
        for ctx in kubeconfig["contexts"]:
            if ctx["name"] == cluster_name_key:
                ctx["context"] = {"cluster": cluster_name_key, "user": cluster_name_key}
                context_found = True
                break
        if not context_found:
            kubeconfig["contexts"].append({"name": cluster_name_key, "context": {"cluster": cluster_name_key, "user": cluster_name_key}})
            
        kubeconfig["current-context"] = cluster_name_key
        
        with open(kubeconfig_path, "w") as f:
            yaml.safe_dump(kubeconfig, f, default_flow_style=False)
    except Exception as e:
        logger.error(f"Error in update_local_kubeconfig: {e}")

_k8s_configured = False

# ── Kubernetes client setup ───────────────────────────────────────────────────
def get_k8s_client():
    global _k8s_configured
    cluster_name = os.getenv("EKS_CLUSTER_NAME")
    region_name = os.getenv("AWS_REGION", "us-east-1")
    
    if cluster_name:
        try:
            import base64
            import boto3
            import tempfile
            eks_client = boto3.client('eks', region_name=region_name)
            cluster_info = eks_client.describe_cluster(name=cluster_name)['cluster']
            endpoint = cluster_info['endpoint']
            ca_data = cluster_info['certificateAuthority']['data']
            token = get_eks_token(cluster_name, region_name)
            
            ca_cert_file = tempfile.NamedTemporaryFile(delete=False)
            ca_cert_file.write(base64.b64decode(ca_data))
            ca_cert_file.close()
            
            configuration = client.Configuration()
            configuration.host = endpoint
            configuration.ssl_ca_cert = ca_cert_file.name
            configuration.api_key['authorization'] = f'Bearer {token}'
            
            api_client = client.ApiClient(configuration)
            return client.CoreV1Api(api_client), client.AppsV1Api(api_client)
        except Exception as e:
            logger.error(f"Failed programmatic EKS client setup, falling back: {e}")
            
    # Fallback to default loading
    if not _k8s_configured:
        try:
            config.load_kube_config()
        except Exception:
            try:
                config.load_incluster_config()
            except Exception:
                pass
        _k8s_configured = True
        
    return client.CoreV1Api(), client.AppsV1Api()


# ── Tool 1: Analyze pod logs ──────────────────────────────────────────────────
@tool
def analyze_logs(namespace_and_pod: str) -> str:
    """
    Analyze logs from a Kubernetes pod for errors, warnings, and anomalies.
    Input format: 'namespace/pod_name' or 'namespace' to scan all pods.
    Returns a summary of log issues found.
    """
    try:
        parts = namespace_and_pod.strip().split("/")
        namespace = parts[0] if parts else "default"
        pod_name  = parts[1] if len(parts) > 1 else None

        v1, _ = get_k8s_client()

        if pod_name:
            pods = [type("Pod", (), {"metadata": type("M", (), {"name": pod_name})()})()]
        else:
            pods = v1.list_namespaced_pod(namespace).items

        results = []
        error_keywords = ["ERROR", "FATAL", "Exception", "OOMKilled",
                         "CrashLoopBackOff", "panic", "failed", "timeout"]

        for pod in pods[:5]:   # limit to 5 pods
            name = pod.metadata.name
            try:
                logs = v1.read_namespaced_pod_log(
                    name=name,
                    namespace=namespace,
                    tail_lines=100,
                )
                errors = [
                    line for line in logs.splitlines()
                    if any(kw.lower() in line.lower() for kw in error_keywords)
                ]
                results.append({
                    "pod": name,
                    "total_lines": len(logs.splitlines()),
                    "error_count": len(errors),
                    "sample_errors": errors[:5],
                })
            except Exception as e:
                results.append({"pod": name, "error": str(e)})

        return json.dumps(results, indent=2)

    except Exception as e:
        return f"Error analyzing logs: {str(e)}"


# ── Tool 2: Get Prometheus metrics ───────────────────────────────────────────
@tool
def get_metrics(query: str) -> str:
    """
    Query Prometheus for metrics. Use PromQL queries.
    Examples:
      - 'cpu' → gets CPU usage for all pods
      - 'memory' → gets memory usage
      - Custom PromQL: 'rate(http_requests_total[5m])'
    Returns metric values as JSON.
    """
    prometheus_url = os.getenv("PROMETHEUS_URL", "http://localhost:9090")

    # Predefined common queries
    preset_queries = {
        "cpu": 'sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (pod)',
        "memory": 'sum(container_memory_usage_bytes{container!=""}) by (pod)',
        "restarts": 'kube_pod_container_status_restarts_total',
        "http_errors": 'rate(http_requests_total{status=~"5.."}[5m])',
    }

    promql = preset_queries.get(query.lower().strip(), query)

    try:
        resp = requests.get(
            f"{prometheus_url}/api/v1/query",
            params={"query": promql},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        results = data.get("data", {}).get("result", [])
        if not results:
            return f"No data found for query: {promql}"

        formatted = []
        for r in results[:10]:
            metric = r.get("metric", {})
            value  = r.get("value", [None, None])[1]
            formatted.append({
                "labels": metric,
                "value": float(value) if value else 0,
            })

        return json.dumps({"query": promql, "results": formatted}, indent=2)

    except requests.exceptions.ConnectionError:
        return "Cannot connect to Prometheus. Run: kubectl port-forward svc/prometheus 9090:9090 -n monitoring"
    except Exception as e:
        return f"Error querying Prometheus: {str(e)}"


# ── Tool 3: Get pod status ────────────────────────────────────────────────────
@tool
def get_pod_status(namespace: str = "default") -> str:
    """
    List all pods in a namespace with their status, restarts, and age.
    Input: namespace name (default: 'default')
    Returns pod health summary.
    """
    try:
        v1, _ = get_k8s_client()
        pods = v1.list_namespaced_pod(namespace).items

        results = []
        for pod in pods:
            containers = pod.status.container_statuses or []
            results.append({
                "name": pod.metadata.name,
                "phase": pod.status.phase,
                "ready": all(c.ready for c in containers),
                "restarts": sum(c.restart_count for c in containers),
                "age_mins": round(
                    (datetime.now(timezone.utc) -
                     pod.metadata.creation_timestamp).total_seconds() / 60
                ),
                "node": pod.spec.node_name,
            })

        healthy   = sum(1 for p in results if p["phase"] == "Running" and p["ready"])
        unhealthy = len(results) - healthy

        return json.dumps({
            "namespace": namespace,
            "total_pods": len(results),
            "healthy": healthy,
            "unhealthy": unhealthy,
            "pods": results,
        }, indent=2)

    except Exception as e:
        return f"Error getting pod status: {str(e)}"


# ── Tool 4: Restart a pod ─────────────────────────────────────────────────────
@tool
def restart_pod(namespace_and_pod: str) -> str:
    """
    Restart a Kubernetes pod by deleting it (K8s recreates it automatically).
    Input format: 'namespace/pod_name'
    Use this when a pod is in CrashLoopBackOff or not responding.
    """
    try:
        parts = namespace_and_pod.strip().split("/")
        if len(parts) != 2:
            return "Error: provide 'namespace/pod_name'"

        namespace, pod_name = parts
        v1, _ = get_k8s_client()

        v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        return f"Pod {pod_name} deleted from {namespace}. Kubernetes will recreate it automatically."

    except Exception as e:
        return f"Error restarting pod: {str(e)}"


# ── Tool 5: Scale deployment ──────────────────────────────────────────────────
@tool
def scale_deployment(input_str: str) -> str:
    """
    Scale a Kubernetes deployment to a specified number of replicas.
    Input format: 'namespace/deployment_name/replicas'
    Example: 'default/my-app/3'
    Use when CPU is high and more instances are needed.
    """
    try:
        parts = input_str.strip().split("/")
        if len(parts) != 3:
            return "Error: provide 'namespace/deployment_name/replicas'"

        namespace, deployment, replicas = parts
        replicas = int(replicas)

        _, apps_v1 = get_k8s_client()

        body = {"spec": {"replicas": replicas}}
        apps_v1.patch_namespaced_deployment_scale(
            name=deployment,
            namespace=namespace,
            body=body,
        )
        return f"Deployment {deployment} scaled to {replicas} replicas in {namespace}."

    except Exception as e:
        return f"Error scaling deployment: {str(e)}"


# ── Tool 6: Trigger GitHub Actions pipeline ───────────────────────────────────
@tool
def trigger_pipeline(workflow_and_reason: str) -> str:
    """
    Trigger a GitHub Actions workflow via the API.
    Input format: 'workflow_filename/reason'
    Example: 'deploy.yml/auto-triggered by agent after pod restart'
    """
    try:
        parts = workflow_and_reason.strip().split("/", 1)
        workflow = parts[0]
        reason   = parts[1] if len(parts) > 1 else "triggered by AI agent"

        github_token = os.getenv("GITHUB_TOKEN")
        github_repo  = os.getenv("GITHUB_REPO")

        if not github_token or not github_repo:
            return "GITHUB_TOKEN or GITHUB_REPO not set in .env"

        resp = requests.post(
            f"https://api.github.com/repos/{github_repo}/actions/workflows/{workflow}/dispatches",
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github.v3+json",
            },
            json={
                "ref": "main",
                "inputs": {"reason": reason},
            },
            timeout=10,
        )

        if resp.status_code == 204:
            return f"Pipeline {workflow} triggered successfully. Reason: {reason}"
        else:
            return f"Failed to trigger pipeline: HTTP {resp.status_code} — {resp.text}"

    except Exception as e:
        return f"Error triggering pipeline: {str(e)}"
