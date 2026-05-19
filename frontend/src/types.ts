export interface Pod {
  name: string;
  phase: string;
  ready: boolean;
  restarts: number;
  age_mins: number;
  node: string;
}

export interface MetricResult {
  labels: Record<string, string>;
  value: number;
}

export interface StatusResponse {
  pods?: {
    pods: Pod[];
    total_pods: number;
    healthy: number;
    unhealthy: number;
  };
  metrics?: {
    results: MetricResult[];
  };
}

export type TraceType = 'thought' | 'tool' | 'result' | 'final' | 'error';

export interface TraceItem {
  id: number;
  type: TraceType;
  label: string;
  content: string;
}

export interface AgentEvent {
  type: string;
  content?: string;
  tool?: string;
  input?: string;
  output?: string;
  message?: string;
}

export interface Activity {
  id: number;
  text: string;
  color: 'blue' | 'green' | 'amber' | 'red';
  time: string;
}

export type TabId = 'dashboard' | 'agent' | 'pods';

// Chart data shapes
export interface CpuDataPoint {
  name: string;
  cpu: number;
}

export interface HealthDataPoint {
  name: string;
  value: number;
  color: string;
}

export interface TimeSeriesPoint {
  time: string;
  healthy: number;
  unhealthy: number;
  restarts: number;
}
