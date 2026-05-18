# Agentic AI DevOps Assistant
### Stack: LangChain + OpenRouter + AWS EKS + Prometheus

> Project #14 from the DevOps + AI Project Sheet

---

## What It Does

```
You: "Why are pods crashing in default namespace?"
         │
         ▼
┌─────────────────────────────────────────┐
│         LangChain ReAct Agent           │
│                                         │
│  Thought: I should check pod status     │
│  Action: get_pod_status(default)        │
│  Observation: 2 pods in CrashLoopBackOff│
│                                         │
│  Thought: I should check logs           │
│  Action: analyze_logs(default)          │
│  Observation: OOMKilled errors found    │
│                                         │
│  Thought: Check memory metrics          │
│  Action: get_metrics(memory)            │
│  Observation: 95% memory usage          │
│                                         │
│  Thought: Scale up to fix it            │
│  Action: scale_deployment(default/app/3)│
│  Observation: Scaled to 3 replicas      │
│                                         │
│  Final Answer: Pods were OOMKilled due  │
│  to memory pressure. Scaled to 3        │
│  replicas. Monitor for stability.       │
└─────────────────────────────────────────┘
         │
         ▼
   Slack/CLI output with full reasoning
```

---

## Project Structure

```
agentic-devops/
├── agent/
│   ├── agent.py      → LangChain ReAct agent + prompt
│   ├── tools.py      → 6 tools: logs, metrics, pods, restart, scale, pipeline
│   └── llm.py        → OpenRouter LLM config
├── terraform/
│   └── main.tf       → EKS cluster + VPC + node group
├── k8s/
│   └── manifests.yaml → Demo app + Prometheus + HPA
├── tests/
│   └── test_agent.py → Unit tests
├── main.py           → Interactive CLI
├── requirements.txt
└── .env.example
```

---

## Agent Tools

| Tool | What it does |
|---|---|
| `get_pod_status` | Lists all pods with health, restarts, age |
| `analyze_logs` | Scans pod logs for errors and anomalies |
| `get_metrics` | Queries Prometheus for CPU/memory/HTTP errors |
| `restart_pod` | Deletes a failing pod (K8s auto-recreates) |
| `scale_deployment` | Scales replicas up or down |
| `trigger_pipeline` | Triggers GitHub Actions workflow via API |

---

## Setup

### Step 1 — Install dependencies
```bash
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
cp .env.example .env       # fill in your values
```

### Step 2 — Provision EKS
```bash
cd terraform
terraform init
terraform apply
# Takes ~15 minutes
```

### Step 3 — Configure kubectl
```bash
# Use the command from terraform output:
aws eks update-kubeconfig --region us-east-1 --name agentic-devops
kubectl get nodes   # verify cluster is ready
```

### Step 4 — Deploy workloads
```bash
kubectl apply -f k8s/manifests.yaml
kubectl get pods   # verify pods are running
```

### Step 5 — Port-forward Prometheus
```bash
kubectl port-forward svc/prometheus 9090:9090 -n monitoring &
```

### Step 6 — Run the agent
```bash
# Interactive mode
python main.py

# Single task
python main.py --task "Check pod health and fix any issues"

# Demo menu
python main.py --demo
```

---

## Demo Tasks

| # | Task |
|---|---|
| 1 | Check health of all pods in default namespace |
| 2 | Analyze CPU and memory metrics for all pods |
| 3 | Find CrashLoopBackOff pods and fix them |
| 4 | Scan logs for errors and suggest fixes |
| 5 | Scale demo-app if CPU > 70% |
| 6 | Full health check report |

---

## ⚠️ Cost Warning

EKS costs ~$0.14/hr (~$3.36/day):
- Control plane: $0.10/hr
- 2x t3.small nodes: ~$0.042/hr

**Destroy when done:**
```bash
cd terraform
terraform destroy
```

---

## What This Demonstrates

| Skill | Evidence |
|---|---|
| LangChain | ReAct agent, tool calling, prompt engineering |
| Agentic AI | Multi-step reasoning, autonomous decision making |
| OpenRouter | Free LLM integration via OpenAI-compatible API |
| Kubernetes | Pod management, scaling, log analysis via Python SDK |
| Prometheus | PromQL queries, metric analysis |
| AWS EKS | Managed K8s cluster provisioned with Terraform |
| GitHub Actions | Pipeline triggering via REST API |
| Python | Async tools, rich CLI, error handling |
