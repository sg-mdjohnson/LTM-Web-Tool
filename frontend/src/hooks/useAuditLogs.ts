import { useState, useCallback } from 'react';
import axios from 'axios';

interface AuditLog {
  id: number;
  timestamp: string;
  username: string;
  action: string;
  resource: string;
  details: string;
  ipAddress: string;
}

interface LogFilters {
  action?: string;
  user?: string;
  dateFrom?: string;
  dateTo?: string;
}

export const useAuditLogs = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = useCallback(async (filters?: LogFilters) => {
    setLoading(true);
    try {
      const response = await axios.get('/api/admin/audit-logs', { params: filters });
      setLogs(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to fetch audit logs');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const downloadLogs = async (filters?: LogFilters) => {
    try {
      const response = await axios.get('/api/admin/audit-logs/download', {
        params: filters,
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `audit-logs-${new Date().toISOString()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to download audit logs');
      throw err;
    }
  };

  return {
    logs,
    loading,
    error,
    fetchLogs,
    downloadLogs
  };
}; 