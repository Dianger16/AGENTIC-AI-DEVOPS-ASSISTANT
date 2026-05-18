# agent/agent.py
# Agentic AI DevOps Assistant
# Uses LangChain ReAct agent pattern:
#   Thought → Action → Observation → Thought → ... → Final Answer
#
# The agent reasons step by step, calling tools as needed,
# until it has enough information to suggest or take a fix.

import os
import logging
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from agent.llm import get_llm
from agent.tools import (
    analyze_logs,
    get_metrics,
    get_pod_status,
    restart_pod,
    scale_deployment,
    trigger_pipeline,
)

load_dotenv()
logger  = logging.getLogger(__name__)
console = Console()

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert Agentic AI DevOps Assistant with deep knowledge of:
- Kubernetes operations and troubleshooting
- Prometheus metrics and alerting
- CI/CD pipelines and GitHub Actions
- Log analysis and root cause analysis
- Cloud infrastructure on AWS EKS

You have access to the following tools:
{tools}

Use this format EXACTLY:
Question: the input question you must answer
Thought: think step by step about what to do
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now have enough information to provide a final answer
Final Answer: your comprehensive analysis and recommendations

IMPORTANT RULES:
- Always check pod status and metrics BEFORE taking any action
- Never restart or scale without first understanding the root cause
- Explain your reasoning at each step
- After fixing, verify the fix worked
- Be specific with commands and next steps

{agent_scratchpad}"""


def create_agent():
    """Create and return the LangChain ReAct agent"""
    llm   = get_llm()
    tools = [
        analyze_logs,
        get_metrics,
        get_pod_status,
        restart_pod,
        scale_deployment,
        trigger_pipeline,
    ]

    prompt = PromptTemplate.from_template(SYSTEM_PROMPT)

    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
    )

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=int(os.getenv("MAX_ITERATIONS", 10)),
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )


def run_agent(task: str) -> dict:
    """
    Run the agent on a given task.
    The agent will reason, use tools, and return a final answer.
    """
    console.print(Panel(
        Text(task, style="bold white"),
        title="[bold blue]🤖 Agentic DevOps Assistant",
        border_style="blue",
    ))

    agent_executor = create_agent()

    try:
        result = agent_executor.invoke({"input": task})

        console.print(Panel(
            Text(result.get("output", "No output"), style="green"),
            title="[bold green]✅ Agent Final Answer",
            border_style="green",
        ))

        return result

    except Exception as e:
        console.print(f"[red]Agent error: {e}[/red]")
        logger.error(f"Agent execution failed: {e}")
        return {"output": f"Agent failed: {str(e)}", "error": True}
