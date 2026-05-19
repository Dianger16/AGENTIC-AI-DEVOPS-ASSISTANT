import { useMemo } from 'react';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { Network, CheckCircle, TriangleAlert, RotateCcw, Cpu, RefreshCw } from 'lucide-react';
import type { Pod, MetricResult, TimeSeriesPoint } from '../types';
import { StatusBadge, RestartBadge } from './Badge';
import './Dashboard.css';

interface Props {
  pods: Pod[];
  metrics: MetricResult[];
  healthy: number;
  unhealthy: number;
  onRefresh: () => void;
}

// Deterministic mock time-series (last 8 intervals) from live data
function buildTimeSeries(healthy: number, unhealthy: number): TimeSeriesPoint[] {
  const now = new Date();
  return Array.from({ length: 8 }, (_, i) => {
    const t = new Date(now.getTime() - (7 - i) * 5 * 60000);
    const jitter = (seed: number) => Math.round((Math.sin(i * 2.4 + seed) * 0.5 + 0.5) * 2);
    return {
      time: t.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      healthy: Math.max(0, healthy - jitter(1)),
      unhealthy: Math.max(0, unhealthy + jitter(2)),
      restarts: jitter(3),
    };
  });
}

const TOOLTIP_STYLE = {
  backgroundColor: '#F5F3EC',
  border: '1px solid #121212',
  borderRadius: 6,
  color: '#121212',
  fontSize: 12,
  fontFamily: 'Inter, sans-serif',
  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)',
};

export default function Dashboard({ pods, metrics, healthy, unhealthy, onRefresh }: Props) {
  const total    = pods.length;
  const restarts = pods.reduce((s, p) => s + (p.restarts || 0), 0);

  const cpuData = useMemo(() =>
    metrics.slice(0, 10).map(r => ({
      name: (r.labels.pod || r.labels.instance || 'unknown').split('-').slice(0, 2).join('-'),
      cpu: parseFloat(r.value < 1 ? (r.value * 1000).toFixed(1) : r.value.toFixed(2)),
      unit: r.value < 1 ? 'm' : '',
    })), [metrics]);

  const pieData = [
    { name: 'Healthy',   value: healthy,   color: '#121212' },
    { name: 'Unhealthy', value: unhealthy,  color: '#A8A29E' },
  ].filter(d => d.value > 0);

  const timeSeries = useMemo(() => buildTimeSeries(healthy, unhealthy), [healthy, unhealthy]);

  return (
    <div className="dashboard">
      {/* Metric cards */}
      <div className="metrics-grid">
        <MetricCard icon={<Network size={18} />} label="Total Pods"  value={total}    sub={`${healthy}/${total} ready`}    color="blue"   />
        <MetricCard icon={<CheckCircle size={18} />} label="Healthy"     value={healthy}  sub="Running & ready"                  color="teal"   />
        <MetricCard icon={<TriangleAlert size={18} />} label="Unhealthy" value={unhealthy} sub="Need attention"                 color="amber"  />
        <MetricCard icon={<RotateCcw size={18} />}  label="Restarts"    value={restarts} sub="Total across pods"               color="red"    />
      </div>

      {/* Charts row */}
      <div className="charts-row">
        {/* Area chart – pod health over time */}
        <div className="chart-card glass">
          <div className="chart-header">
            <span className="chart-title">Pod Health Timeline</span>
            <span className="chart-sub">Last 40 min</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={timeSeries} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gHealthy" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#121212" stopOpacity={0.06} />
                  <stop offset="95%" stopColor="#121212" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gUnhealthy" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#A8A29E" stopOpacity={0.06} />
                  <stop offset="95%" stopColor="#A8A29E" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(18,18,18,0.05)" />
              <XAxis dataKey="time" tick={{ fill: '#78716C', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#78716C', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ fontSize: 12, color: '#78716C' }} />
              <Area type="monotone" dataKey="healthy"   stroke="#121212" fill="url(#gHealthy)"   strokeWidth={1.5} dot={false} />
              <Area type="monotone" dataKey="unhealthy" stroke="#A8A29E" fill="url(#gUnhealthy)" strokeWidth={1.5} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Pie chart – health distribution */}
        <div className="chart-card glass pie-card">
          <div className="chart-header">
            <span className="chart-title">Health Distribution</span>
          </div>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%" cy="50%"
                  innerRadius={60} outerRadius={90}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} opacity={0.9} />
                  ))}
                </Pie>
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Legend wrapperStyle={{ fontSize: 12, color: '#9aa0bb' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="chart-empty">No pod data yet</div>
          )}
        </div>
      </div>

      {/* CPU bar chart */}
      {cpuData.length > 0 && (
        <div className="chart-card glass cpu-chart">
          <div className="chart-header">
            <span className="chart-title"><Cpu size={15} style={{ marginRight: 6 }} />CPU Usage per Pod</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={cpuData} margin={{ top: 10, right: 10, left: -20, bottom: 30 }}>
              <defs>
                <linearGradient id="gCpu" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%"   stopColor="#121212" stopOpacity={0.8} />
                  <stop offset="100%" stopColor="#A8A29E" stopOpacity={0.4} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(18,18,18,0.05)" />
              <XAxis dataKey="name" tick={{ fill: '#78716C', fontSize: 10 }} axisLine={false} tickLine={false} angle={-25} textAnchor="end" />
              <YAxis tick={{ fill: '#78716C', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(value: any) => [value, 'CPU']} />
              <Bar dataKey="cpu" fill="url(#gCpu)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Pod table */}
      <div className="card glass pod-table-card">
        <div className="card-header">
          <span className="card-title">Pod Status Overview</span>
          <button className="icon-btn" onClick={onRefresh} title="Refresh">
            <RefreshCw size={14} />
          </button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Pod Name</th>
                <th>Status</th>
                <th>Restarts</th>
                <th>Age</th>
                <th>Node</th>
              </tr>
            </thead>
            <tbody>
              {pods.length === 0 ? (
                <tr><td colSpan={5} className="table-empty">No pods found</td></tr>
              ) : pods.map(p => (
                <tr key={p.name}>
                  <td className="pod-name">{p.name}</td>
                  <td><StatusBadge phase={p.phase} ready={p.ready} /></td>
                  <td><RestartBadge restarts={p.restarts} /></td>
                  <td className="text-muted">{p.age_mins}m</td>
                  <td className="pod-node">{(p.node || '').split('.')[0]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ icon, label, value, sub, color }: {
  icon: React.ReactNode; label: string; value: number; sub: string; color: string;
}) {
  return (
    <div className={`metric-card glass metric-${color}`}>
      <div className="metric-label">
        <span className="metric-icon">{icon}</span>
        {label}
      </div>
      <div className="metric-value">{value === 0 && value !== undefined ? 0 : (value || '—')}</div>
      <div className="metric-sub">{sub}</div>
      <div className="metric-glow" />
    </div>
  );
}
