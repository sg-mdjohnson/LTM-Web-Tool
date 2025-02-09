import { useState, useCallback } from 'react';
import axios from 'axios';

interface SystemSettings {
  siteName: string;
  adminEmail: string;
  twoFactorEnabled: boolean;
  sessionTimeout: number;
  autoBackupEnabled: boolean;
  backupRetentionDays: number;
}

export const useSystemSettings = () => {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/admin/settings');
      setSettings(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to fetch settings');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateSettings = async (newSettings: SystemSettings) => {
    setLoading(true);
    try {
      const response = await axios.put('/api/admin/settings', newSettings);
      setSettings(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update settings');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    settings,
    loading,
    error,
    fetchSettings,
    updateSettings
  };
}; 