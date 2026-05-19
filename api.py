# api.py
# FastAPI backend — serves the dashboard and streams agent responses
# Usage: uvicorn api:app --reload --port 8000

import os
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agentic DevOps Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request model ─────────────────────────────────────────────────────────────
class TaskRequest(BaseModel):
    task: str

# ── SSE streaming endpoint ────────────────────────────────────────────────────
@app.post("/api/run")
async def run_agent_stream(request: TaskRequest):
    """
    Streams agent reasoning steps as Server-Sent Events.
    Frontend receives each step in real time.
    """
    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            from agent.agent import create_agent

            # Send start event
            yield f"data: {json.dumps({'type': 'start', 'task': request.task, 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"

            agent_executor = create_agent()

            # Capture intermediate steps via callback
            steps = []

            def on_tool_start(tool_name, tool_input):
                step = {
                    "type": "tool_call",
                    "tool": tool_name,
                    "input": str(tool_input),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                steps.append(step)
                return step

            def on_tool_end(output):
                step = {
                    "type": "tool_result",
                    "output": str(output),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                steps.append(step)
                return step

            # Run agent in thread pool (it's sync)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: agent_executor.invoke({"input": request.task})
            )

            # Stream intermediate steps
            intermediate = result.get("intermediate_steps", [])
            for i, (action, observation) in enumerate(intermediate):
                # Tool call
                yield f"data: {json.dumps({'type': 'thought', 'content': f'Step {i+1}: Using {action.tool}', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
                await asyncio.sleep(0.1)

                yield f"data: {json.dumps({'type': 'tool_call', 'tool': action.tool, 'input': str(action.tool_input), 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
                await asyncio.sleep(0.1)

                yield f"data: {json.dumps({'type': 'tool_result', 'output': str(observation), 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
                await asyncio.sleep(0.1)

            # Final answer
            yield f"data: {json.dumps({'type': 'final', 'content': result.get('output', 'No output'), 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"Agent error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )

# ── Quick status endpoint ─────────────────────────────────────────────────────
@app.get("/api/status")
async def get_status():
    """Returns current K8s pod status and Prometheus metrics"""
    try:
        from agent.tools import get_pod_status, get_metrics
        pods    = get_pod_status.invoke("default")
        metrics = get_metrics.invoke("cpu")
        return {
            "pods":    json.loads(pods),
            "metrics": json.loads(metrics) if metrics.startswith("{") else {"error": metrics},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}

# ── Serve frontend ────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("frontend/index.html") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)