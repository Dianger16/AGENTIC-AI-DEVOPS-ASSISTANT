import { RefreshCw } from 'lucide-react';
import type { Pod } from '../types';
import { StatusBadge, ReadyBadge, RestartBadge } from './Badge';
import './PodMonitor.css';

interface Props {
  pods: Pod[];
  onRefresh: () => void;
}

export default function PodMonitor({ pods, onRefresh }: Props) {
  return (
    <div className="pod-monitor glass">
      <div className="pm-header">
        <span className="pm-title">All Pods — Detailed View</span>
        <div className="pm-actions">
          <span className="pm-count">{pods.length} pods</span>
          <button className="icon-btn" onClick={onRefresh}>
            <RefreshCw size={14} />
          </button>
        </div>
      </div>
      <div className="pm-table-wrap">
        <table>
          <thead>
            <tr>
              <th>Pod Name</th>
              <th>Namespace</th>
              <th>Phase</th>
              <th>Ready</th>
              <th>Restarts</th>
              <th>Age (min)</th>
              <th>Node</th>
            </tr>
          </thead>
          <tbody>
            {pods.length === 0 ? (
              <tr><td colSpan={7} className="table-empty">No pods found</td></tr>
            ) : pods.map(p => (
              <tr key={p.name}>
                <td className="pod-name">{p.name}</td>
                <td className="text-muted">default</td>
                <td><StatusBadge phase={p.phase} ready={p.ready} /></td>
                <td><ReadyBadge ready={p.ready} /></td>
                <td><RestartBadge restarts={p.restarts} /></td>
                <td className="text-muted">{p.age_mins}</td>
                <td className="pod-node">{(p.node || '').split('.')[0]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
