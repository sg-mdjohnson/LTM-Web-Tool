export interface DNSResult {
  status: 'success' | 'error';
  records?: DNSRecord[];
  results?: DNSPropagationResult[];
  time?: number;
  answers?: Array<{
    data: string;
    ttl: number;
  }>;
  dnssec?: {
    secure: boolean;
    validated: boolean;
    chain?: Array<{
      name: string;
      type: string;
      algorithm: string;
      validFrom: string;
      validUntil: string;
      status: 'valid' | 'invalid' | 'warning';
    }>;
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
  status: string;
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