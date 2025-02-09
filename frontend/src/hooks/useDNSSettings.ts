import { useState, useEffect } from 'react';
import axios from 'axios';

interface DNSSettings {
  timeout: number;
  retries: number;
  cacheEnabled: boolean;
  cacheDuration: number;
  preferredNameservers: string;
}

export const useDNSSettings = () => {
  const [loading, setLoading] = useState(false);
  const [settings, setSettings] = useState<DNSSettings | null>(null);

  useEffect(() => {
    const fetchSettings = async () => {
      setLoading(true);
      try {
        const response = await axios.get('/api/dns/settings');
        setSettings(response.data.settings);
      } catch (error) {
        console.error('Failed to fetch DNS settings:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  const saveSettings = async (newSettings: DNSSettings) => {
    setLoading(true);
    try {
      await axios.post('/api/dns/settings', newSettings);
      setSettings(newSettings);
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  return { settings, loading, saveSettings };
}; 