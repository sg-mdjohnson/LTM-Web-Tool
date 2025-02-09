import { useState, useCallback } from 'react';
import axios from 'axios';

interface Backup {
  id: string;
  timestamp: string;
  size: string;
  type: 'auto' | 'manual';
  status: 'completed' | 'in_progress' | 'failed';
}

export const useBackups = () => {
  const [backups, setBackups] = useState<Backup[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBackups = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/admin/backups');
      setBackups(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to fetch backups');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const createBackup = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/admin/backups');
      setBackups(prev => [...prev, response.data]);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to create backup');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const downloadBackup = async (backupId: string) => {
    try {
      const response = await axios.get(`/api/admin/backups/${backupId}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `backup-${backupId}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to download backup');
      throw err;
    }
  };

  const restoreBackup = async (backupId: string) => {
    setLoading(true);
    try {
      await axios.post(`/api/admin/backups/${backupId}/restore`);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to restore backup');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteBackup = async (backupId: string) => {
    setLoading(true);
    try {
      await axios.delete(`/api/admin/backups/${backupId}`);
      setBackups(prev => prev.filter(backup => backup.id !== backupId));
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to delete backup');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    backups,
    loading,
    error,
    fetchBackups,
    createBackup,
    downloadBackup,
    restoreBackup,
    deleteBackup
  };
}; 