import type { Pod } from '../types';
import './Badge.css';

interface Props {
  phase: string;
  ready: boolean;
}

export function StatusBadge({ phase, ready }: Props) {
  if (phase === 'Running' && ready)
    return <span className="badge badge-green"><span className="badge-dot" />Running</span>;
  if (phase === 'Running')
    return <span className="badge badge-amber"><span className="badge-dot" />Not Ready</span>;
  if (phase === 'Pending')
    return <span className="badge badge-blue"><span className="badge-dot" />Pending</span>;
  return <span className="badge badge-red"><span className="badge-dot" />{phase || 'Unknown'}</span>;
}

export function ReadyBadge({ ready }: { ready: boolean }) {
  return ready
    ? <span className="badge badge-green">Yes</span>
    : <span className="badge badge-red">No</span>;
}

export function RestartBadge({ restarts }: Pick<Pod, 'restarts'>) {
  if (restarts === 0) return <span style={{ color: 'var(--text-muted)' }}>0</span>;
  if (restarts < 5)   return <span style={{ color: 'var(--amber)' }}>{restarts}</span>;
  return <span className="badge badge-red">{restarts}</span>;
}
