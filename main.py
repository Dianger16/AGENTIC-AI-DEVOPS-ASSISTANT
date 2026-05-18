# main.py
# Interactive CLI for the Agentic DevOps Assistant
# Usage: python main.py
#        python main.py --task "Why are pods crashing in default namespace?"

import os
import sys
import logging
import argparse
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

console = Console()

# ── Predefined tasks for demo ─────────────────────────────────────────────────
DEMO_TASKS = {
    "1": "Check the health of all pods in the default namespace and identify any issues",
    "2": "Analyze CPU and memory metrics for all pods and suggest optimizations",
    "3": "Check if there are any pods in CrashLoopBackOff and fix them",
    "4": "Scan pod logs in the default namespace for errors and suggest fixes",
    "5": "Scale the demo-app deployment to 3 replicas if CPU usage is above 70%",
    "6": "Run a full health check: pod status + metrics + logs, then give a summary report",
}


def validate_env():
    required = ["OPENROUTER_API_KEY"]
    missing  = [k for k in required if not os.getenv(k)]
    if missing:
        console.print(f"[red]Missing required env vars: {', '.join(missing)}[/red]")
        console.print("Copy .env.example to .env and fill in your values")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Agentic AI DevOps Assistant")
    parser.add_argument("--task", type=str, help="Task for the agent to execute")
    parser.add_argument("--demo", action="store_true", help="Run demo task menu")
    args = parser.parse_args()

    console.print(Panel(
        "[bold blue]Agentic AI DevOps Assistant[/bold blue]\n"
        "[dim]LangChain + OpenRouter + Kubernetes + Prometheus[/dim]",
        border_style="blue",
    ))

    if not validate_env():
        sys.exit(1)

    # Import here so validation runs first
    from agent.agent import run_agent

    if args.task:
        run_agent(args.task)
        return

    if args.demo:
        console.print("\n[bold]Demo Tasks:[/bold]")
        for k, v in DEMO_TASKS.items():
            console.print(f"  [cyan]{k}[/cyan]. {v}")
        choice = Prompt.ask("\nChoose a demo task", choices=list(DEMO_TASKS.keys()))
        run_agent(DEMO_TASKS[choice])
        return

    # Interactive mode
    console.print("\n[dim]Type your task or 'demo' to see prebuilt tasks. 'quit' to exit.[/dim]\n")

    while True:
        try:
            task = Prompt.ask("[bold cyan]Task[/bold cyan]").strip()

            if task.lower() in ("quit", "exit", "q"):
                console.print("Goodbye!")
                break

            if task.lower() == "demo":
                console.print("\n[bold]Demo Tasks:[/bold]")
                for k, v in DEMO_TASKS.items():
                    console.print(f"  [cyan]{k}[/cyan]. {v}")
                choice = Prompt.ask("Choose", choices=list(DEMO_TASKS.keys()))
                task = DEMO_TASKS[choice]

            if task:
                run_agent(task)

        except (KeyboardInterrupt, EOFError):
            console.print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
