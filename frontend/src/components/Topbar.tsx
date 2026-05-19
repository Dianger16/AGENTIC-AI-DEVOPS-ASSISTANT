import { RefreshCw } from 'lucide-react';
import './Topbar.css';

interface Props {
  connected: boolean | null;
  onRefresh: () => void;
}

export default function Topbar({ connected, onRefresh }: Props) {
  const dotClass = connected === null ? 'dot-idle' : connected ? 'dot-on' : 'dot-off';
  const label    = connected === null ? 'Connecting...' : connected ? 'Connected' : 'API Offline';

  return (
    <header className="topbar">
      <div className="topbar-logo">
        <div className="logo-icon">🤖</div>
        <span className="logo-text">Agentic DevOps</span>
        <span className="logo-badge">AI</span>
      </div>

      <div className="topbar-right">
        <button className="topbar-refresh" onClick={onRefresh} title="Refresh status">
          <RefreshCw size={14} />
        </button>
        <div className={`status-dot ${dotClass}`} />
        <span className="status-text">{label}</span>
      </div>
    </header>
  );
}
