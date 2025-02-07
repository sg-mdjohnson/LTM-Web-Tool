export interface DNSResult {
  query: string;
  type: string;
  answers: DNSAnswer[];
  server: string;
  time: number;
  records?: DNSRecord[];
  results?: DNSPropagationResult[];
  dnssec?: {
    validated: boolean;
    secure: boolean;
    chain?: DNSSECChain[];
  };
}

export interface DNSAnswer {
  name: string;
  type: string;
  data: string;
  ttl: number;
}

export interface DNSRecord {
  name: string;
  type: string;
  ttl: number;
  data: string[];
}

export interface DNSPropagationResult {
  nameserver: string;
  status: 'success' | 'error';
  time?: number;
  answers?: string[];
  error?: string;
}

export interface DNSSECChain {
  name: string;
  type: string;
  algorithm: string;
  validFrom: string;
  validUntil: string;
  status: 'valid' | 'invalid' | 'missing';
} 