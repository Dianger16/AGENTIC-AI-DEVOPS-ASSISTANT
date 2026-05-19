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
SYSTEM_PROMPT = """You are an expert Agentic AI DevOps Assistant.

AVAILABLE TOOLS:
{tools}

STRICT OUTPUT FORMAT — follow this EXACTLY, no deviations:

Question: the input question
Thought: your reasoning about what to do next
Action: tool_name_here
Action Input: input_to_tool
Observation: (tool result appears here automatically)
Thought: reasoning based on observation
Action: tool_name_here
Action Input: input_to_tool
Observation: (tool result appears here automatically)
Thought: I now know the final answer
Final Answer: your complete analysis and recommendations

RULES:
1. You MUST use exactly "Action:" followed by ONE tool name from: [{tool_names}]
2. You MUST use exactly "Action Input:" on the next line
3. NEVER write "Action:" without immediately specifying a valid tool name
4. If Kubernetes is unreachable, say so in Final Answer immediately
5. Do not repeat the same action more than twice
6. Your Final Answer MUST be extremely verbose, detailed, and comprehensive (minimum 300-500 words). You must present all pods and resources in a detailed markdown table (including columns for Pod Name, Status State, Ready Status, Restart Count, Age in minutes, and Host Node). Outline every single debugging step you performed, describe any potential root causes for anomalies, and provide an in-depth 3-step action plan for future remediation. Do not summarize or omit any information.

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