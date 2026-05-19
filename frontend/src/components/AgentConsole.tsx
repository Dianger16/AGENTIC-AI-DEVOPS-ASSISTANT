import { useEffect, useRef, useState, useCallback } from 'react';
import {
  Brain, Play, Network, Scroll, ChartLine,
  RotateCcw, ArrowUpRightFromSquare, PlayCircle, ClockArrowDown, Bot
} from 'lucide-react';
import type { TraceItem, Activity, AgentEvent } from '../types';
import { streamAgent } from '../api';
import './AgentConsole.css';

const PRESETS = [
  'Check all pod health in default namespace',
  'Find and fix any crashing pods',
  'Analyze CPU and memory metrics',
  'Scan logs for errors and suggest fixes',
  'Scale demo-app to 3 replicas if CPU is high',
];

const TOOLS = [
  { icon: <Network size={14} />,     name: 'get_pod_status',    color: 'blue'   },
  { icon: <Scroll size={14} />,      name: 'analyze_logs',      color: 'blue'   },
  { icon: <ChartLine size={14} />,   name: 'get_metrics',       color: 'blue'   },
  { icon: <RotateCcw size={14} />,   name: 'restart_pod',       color: 'amber'  },
  { icon: <ArrowUpRightFromSquare size={14} />, name: 'scale_deployment', color: 'amber' },
  { icon: <PlayCircle size={14} />,  name: 'trigger_pipeline',  color: 'purple' },
];

interface Props {
  initialTask: string;
  onActivity: (text: string, color: Activity['color']) => void;
  onRefresh: () => void;
}

export default function AgentConsole({ initialTask, onActivity, onRefresh }: Props) {
  const [task, setTask]       = useState(initialTask);
  const [running, setRunning] = useState(false);
  const [traces, setTraces]   = useState<TraceItem[]>([]);
  const [stepCount, setSteps] = useState(0);
  const [activities, setActivities] = useState<Activity[]>([]);
  const idRef = useRef(0);
  const traceRef = useRef<HTMLDivElement>(null);

  function addTrace(type: TraceItem['type'], label: string, content: string) {
    const item: TraceItem = { id: idRef.current++, type, label, content };
    setTraces(prev => [...prev, item]);
    setTimeout(() => traceRef.current?.scrollTo({ top: 99999, behavior: 'smooth' }), 50);
    return item;
  }

  function addActivity(text: string, color: Activity['color']) {
    const act: Activity = {
      id: idRef.current++,
      text,
      color,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setActivities(prev => [act, ...prev].slice(0, 10));
    onActivity(text, color);
  }

  function handleEvent(ev: AgentEvent) {
    switch (ev.type) {
      case 'thought':
        addTrace('thought', 'Thought', ev.content ?? '');
        setSteps(s => s + 1);
        break;
      case 'tool_call':
        addTrace('tool', `Tool: ${ev.tool}`, ev.input ?? '');
        addActivity(`Called ${ev.tool}`, 'blue');
        break;
      case 'tool_result':
        addTrace('result', 'Observation', ev.output ?? '');
        break;
      case 'final':
        addTrace('final', '✓ Final Answer', ev.content ?? '');
        addActivity('Task complete', 'green');
        onRefresh();
        break;
      case 'error':
        addTrace('error', 'Error', ev.message ?? '');
        addActivity('Error occurred', 'red');
        break;
    }
  }

  const runAgent = useCallback(async (taskToRun: string = task) => {
    if (!taskToRun.trim() || running) return;
    setRunning(true);
    setTraces([]);
    setSteps(0);
    try {
      for await (const ev of streamAgent(taskToRun)) {
        handleEvent(ev);
      }
    } catch (e) {
      addTrace('error', 'Error', `Cannot reach API. Make sure backend is running.\n${e}`);
    }
    setRunning(false);
  }, [task, running]);

  useEffect(() => {
    if (initialTask) {
      setTask(initialTask);
      runAgent(initialTask);
    }
  }, [initialTask]);

  return (
    <div className="agent-layout">
      {/* Left: input + trace */}
      <div className="agent-main">
        <div className="task-card glass">
          <div className="task-label">Give the Agent a Task</div>
          <textarea
            className="task-input"
            value={task}
            onChange={e => setTask(e.target.value)}
            placeholder="e.g. Check pod health and fix any issues in default namespace..."
            onKeyDown={e => e.key === 'Enter' && e.ctrlKey && runAgent()}
          />
          <div className="presets">
            {PRESETS.map(p => (
              <button key={p} className="preset-btn" onClick={() => setTask(p)}>{p}</button>
            ))}
          </div>
          <button
            className={`run-btn ${running ? 'running' : ''}`}
            onClick={() => runAgent()}
            disabled={running}
          >
            {running
              ? <><div className="spinner" /> Running Agent...</>
              : <><Play size={16} /> Run Agent<span className="run-hint">Ctrl+Enter</span></>
            }
          </button>
        </div>

        {/* Reasoning trace */}
        <div className="trace-card glass">
          <div className="trace-header">
            <span className="trace-title"><Brain size={16} /> Agent Reasoning</span>
            <span className="step-count">{stepCount} steps</span>
          </div>
          <div className="trace-body" ref={traceRef}>
            {traces.length === 0 ? (
              <div className="trace-empty">
                <Bot size={40} strokeWidth={1} />
                <p>Run a task to see the agent's reasoning here</p>
              </div>
            ) : traces.map(t => (
              <div key={t.id} className={`trace-item trace-${t.type}`}>
                <div className="trace-item-label">{t.label}</div>
                <div className="trace-item-content">{t.content}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel */}
      <div className="agent-right">
        {/* Tools */}
        <div className="right-card glass">
          <div className="right-title">Available Tools</div>
          <div className="tools-list">
            {TOOLS.map(t => (
              <div key={t.name} className={`tool-item tool-${t.color}`}>
                {t.icon}
                <span>{t.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Activity feed */}
        <div className="right-card glass">
          <div className="right-title"><ClockArrowDown size={13} /> Recent Actions</div>
          <div className="activity-list">
            {activities.length === 0
              ? <p className="no-activity">No actions yet</p>
              : activities.map(a => (
                  <div key={a.id} className="activity-item">
                    <span className={`activity-dot act-${a.color}`} />
                    <div>
                      <div className="activity-text">{a.text}</div>
                      <div className="activity-time">{a.time}</div>
                    </div>
                  </div>
                ))
            }
          </div>
        </div>

        {/* Model info */}
        <div className="right-card glass model-card">
          <div className="right-title"><Bot size={13} /> Model</div>
          <div className="model-name">llama-3-70b</div>
          <div className="model-via">via OpenRouter</div>
        </div>
      </div>
    </div>
  );
}
