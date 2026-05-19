import React from 'react';
import type { TabId } from '../types';
import {
  LayoutDashboard, Bot, Boxes, HeartPulse,
  Cpu, Wrench, Search, ChevronRight
} from 'lucide-react';
import './Sidebar.css';

interface Props {
  active: TabId;
  onTab: (t: TabId) => void;
  onQuickTask: (task: string) => void;
}

const navItems: { id: TabId; icon: React.ReactNode; label: string }[] = [
  { id: 'dashboard', icon: <LayoutDashboard size={18} />, label: 'Dashboard' },
  { id: 'agent',     icon: <Bot size={18} />,              label: 'Agent Console' },
  { id: 'pods',      icon: <Boxes size={18} />,            label: 'Pod Monitor' },
];

const quickTasks = [
  { icon: <HeartPulse size={15} />, label: 'Health Check',    task: 'Check all pod health in default namespace' },
  { icon: <Cpu size={15} />,        label: 'Metrics Analysis', task: 'Analyze CPU and memory metrics for all pods' },
  { icon: <Wrench size={15} />,     label: 'Fix Issues',       task: 'Find and fix any crashing pods in default namespace' },
  { icon: <Search size={15} />,     label: 'Log Scan',         task: 'Scan pod logs for errors and suggest fixes' },
];

export default function Sidebar({ active, onTab, onQuickTask }: Props) {
  return (
    <aside className="sidebar glass">
      <div className="sidebar-section-label">Navigation</div>
      {navItems.map(item => (
        <button
          key={item.id}
          className={`sidebar-btn ${active === item.id ? 'active' : ''}`}
          onClick={() => onTab(item.id)}
        >
          <span className="sidebar-icon">{item.icon}</span>
          <span>{item.label}</span>
          {active === item.id && <ChevronRight size={14} className="sidebar-chevron" />}
        </button>
      ))}

      <div className="sidebar-divider" />
      <div className="sidebar-section-label">Quick Tasks</div>
      {quickTasks.map(qt => (
        <button key={qt.label} className="sidebar-btn quick" onClick={() => onQuickTask(qt.task)}>
          <span className="sidebar-icon">{qt.icon}</span>
          <span>{qt.label}</span>
        </button>
      ))}

      <div className="sidebar-divider" />
      <div className="sidebar-section-label">Cluster Info</div>
      <div className="cluster-info">
        <div className="cluster-row">
          <span className="cluster-key">Cluster</span>
          <span className="cluster-val">agentic-devops</span>
        </div>
        <div className="cluster-row">
          <span className="cluster-key">Region</span>
          <span className="cluster-val">us-east-1</span>
        </div>
        <div className="cluster-row">
          <span className="cluster-key">Model</span>
          <span className="cluster-val">llama-3-70b</span>
        </div>
      </div>
    </aside>
  );
}
