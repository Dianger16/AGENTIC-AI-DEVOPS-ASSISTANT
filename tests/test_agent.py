# tests/test_agent.py
# Unit tests — no Kubernetes or OpenRouter needed

import pytest
import json
from unittest.mock import patch, MagicMock
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestTools:
    def test_get_metrics_connection_error(self):
        """Should return helpful message when Prometheus unreachable"""
        from agent.tools import get_metrics
        result = get_metrics.invoke("cpu")
        assert "Cannot connect" in result or "Error" in result or "No data" in result

    def test_get_pod_status_returns_string(self):
        """Should return string even when K8s not available"""
        from agent.tools import get_pod_status
        result = get_pod_status.invoke("default")
        assert isinstance(result, str)

    def test_scale_deployment_bad_input(self):
        """Should return error message for bad input format"""
        from agent.tools import scale_deployment
        result = scale_deployment.invoke("bad-input")
        assert "Error" in result

    def test_restart_pod_bad_input(self):
        """Should return error message for bad input format"""
        from agent.tools import restart_pod
        result = restart_pod.invoke("bad-input")
        assert "Error" in result

    def test_trigger_pipeline_no_credentials(self):
        """Should return helpful message when credentials missing"""
        with patch.dict(os.environ, {}, clear=True):
            from agent.tools import trigger_pipeline
            result = trigger_pipeline.invoke("deploy.yml/test")
            assert "GITHUB_TOKEN" in result or "Error" in result

    def test_analyze_logs_bad_input(self):
        """Should handle errors gracefully"""
        from agent.tools import analyze_logs
        result = analyze_logs.invoke("nonexistent/pod")
        assert isinstance(result, str)


class TestDemoTasks:
    def test_demo_tasks_are_defined(self):
        """All demo tasks should be importable"""
        from main import DEMO_TASKS
        assert len(DEMO_TASKS) >= 6
        for k, v in DEMO_TASKS.items():
            assert isinstance(v, str)
            assert len(v) > 10

    def test_demo_tasks_have_numeric_keys(self):
        from main import DEMO_TASKS
        for k in DEMO_TASKS:
            assert k.isdigit()


class TestLLMConfig:
    def test_llm_uses_openrouter_base(self):
        """LLM should be configured with correct model and api key"""
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "test-key",
            "OPENROUTER_MODEL": "meta-llama/llama-3-70b-instruct:nitro"
        }):
            from agent.llm import get_llm
            llm = get_llm()
            assert llm.api_key == "test-key"
            assert "llama" in llm.model.lower()
            assert llm._llm_type == "openrouter"