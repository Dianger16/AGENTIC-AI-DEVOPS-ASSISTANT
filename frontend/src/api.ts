import type { StatusResponse, AgentEvent } from './types';

export const API = 'http://localhost:8000';

export async function fetchStatus(): Promise<StatusResponse> {
  const res = await fetch(`${API}/api/status`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function* streamAgent(task: string): AsyncGenerator<AgentEvent> {
  const res = await fetch(`${API}/api/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task }),
  });

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          yield JSON.parse(line.slice(6)) as AgentEvent;
        } catch { /* skip malformed */ }
      }
    }
  }
}
