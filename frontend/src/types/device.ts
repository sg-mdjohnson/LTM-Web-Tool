export interface Device {
  id: number;
  name: string;
  host: string;
  username: string;
  description?: string;
  status: 'active' | 'inactive' | 'error' | 'unknown';
  last_used?: string;
} 