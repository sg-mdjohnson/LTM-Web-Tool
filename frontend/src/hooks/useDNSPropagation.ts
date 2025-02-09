import { useState } from 'react';
import axios from 'axios';

interface PropagationResult {
  nameserver: string;
  status: 'success' | 'error';
  ip: string;
  responseTime: number;
}

export const useDNSPropagation = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<PropagationResult[] | null>(null);

  const checkPropagation = async (domain: string) => {
    setLoading(true);
    try {
      const response = await axios.post('/api/dns/propagation', { domain });
      setResults(response.data.results);
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Propagation check failed');
    } finally {
      setLoading(false);
    }
  };

  return { checkPropagation, loading, results };
}; 