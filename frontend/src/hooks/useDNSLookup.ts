import { useState } from 'react';
import axios from 'axios';

interface DNSRecord {
  type: string;
  value: string;
  ttl: number;
}

export const useDNSLookup = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<DNSRecord[] | null>(null);

  const lookup = async (domain: string, recordType: string) => {
    setLoading(true);
    try {
      const response = await axios.post('/api/dns/lookup', {
        domain,
        type: recordType
      });
      setResults(response.data.results);
    } catch (error) {
      throw new Error(error.response?.data?.message || 'DNS lookup failed');
    } finally {
      setLoading(false);
    }
  };

  return { lookup, loading, results };
}; 