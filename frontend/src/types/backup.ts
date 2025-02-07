export interface BackupEntry {
  id: string;
  timestamp: string;
  type: 'manual' | 'scheduled';
  author: string;
  size: string;
  devices: string[];
  comment?: string;
  status: 'success' | 'partial' | 'failed';
  version: string;
  config: string;
} 