import { useState, useEffect, useCallback } from 'react';
import type { Pod, MetricResult, TabId, Activity } from './types';
import { fetchStatus } from './api';
import Topbar from './components/Topbar';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import AgentConsole from './components/AgentConsole';
import PodMonitor from './components/PodMonitor';
import './App.css';

export default function App() {
  const [tab, setTab]             = useState<TabId>('dashboard');
  const [pods, setPods]           = useState<Pod[]>([]);
  const [metrics, setMetrics]     = useState<MetricResult[]>([]);
  const [healthy, setHealthy]     = useState(0);
  const [unhealthy, setUnhealthy] = useState(0);
  const [connected, setConnected] = useState<boolean | null>(null);
  const [initialTask, setInitialTask] = useState('');

  const refresh = useCallback(async () => {
    try {
      const data = await fetchStatus();
      if (data.pods) {
        setPods(data.pods.pods ?? []);
        setHealthy(data.pods.healthy ?? 0);
        setUnhealthy(data.pods.unhealthy ?? 0);
      }
      if (data.metrics?.results) {
        setMetrics(data.metrics.results);
      }
      setConnected(true);
    } catch {
      setConnected(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 30_000);
    return () => clearInterval(id);
  }, [refresh]);

  function handleQuickTask(task: string) {
    setInitialTask(task);
    setTab('agent');
  }

  function handleActivity(_text: string, _color: Activity['color']) { /* global activity hook */ }

  return (
    <div className="app-layout">
      <Topbar connected={connected} onRefresh={refresh} />
      <Sidebar active={tab} onTab={setTab} onQuickTask={handleQuickTask} />
      <main className="app-main">
        {tab === 'dashboard' && (
          <Dashboard
            pods={pods}
            metrics={metrics}
            healthy={healthy}
            unhealthy={unhealthy}
            onRefresh={refresh}
          />
        )}
        {tab === 'agent' && (
          <AgentConsole initialTask={initialTask} onActivity={handleActivity} onRefresh={refresh} />
        )}
        {tab === 'pods' && (
          <PodMonitor pods={pods} onRefresh={refresh} />
        )}
      </main>
    </div>
  );
}
