export interface Device {
  id: number;
  name: string;
  host: string;
  username: string;
  status: 'active' | 'inactive' | 'error' | 'unknown';
  description?: string;
  last_used?: string;
  lastSync?: string;
}

export interface DeviceFormData {
  name: string;
  host: string;
  username: string;
  password?: string;
  description?: string;
}

export interface DeviceUpdateData extends Partial<DeviceFormData> {
  id: number;
} 