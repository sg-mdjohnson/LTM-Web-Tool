import { useState, useCallback } from 'react';
import axios from 'axios';

interface HistoryEntry {
  timestamp: string;
  domain: string;
  type: string;
  result: string;
}

export const useDNSHistory = () => {
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/dns/history');
      setHistory(response.data.history);
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to fetch history');
    } finally {
      setLoading(false);
    }
  }, []);

  const clearHistory = async () => {
    try {
      await axios.delete('/api/dns/history');
      setHistory([]);
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to clear history');
    }
  };

  return { history, loading, fetchHistory, clearHistory };
}; 