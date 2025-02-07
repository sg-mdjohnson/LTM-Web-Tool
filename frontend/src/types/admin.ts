export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
}

export interface Device {
  id: number;
  name: string;
  host: string;
  username: string;
}

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
} 