import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Heading,
  VStack,
  HStack,
  Select,
  Input,
  Button,
  Text,
  Box,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  useToast,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  FormControl,
  FormLabel,
  Code,
  useColorModeValue,
  Switch,
  IconButton,
} from '@chakra-ui/react';
import {
  SearchIcon,
  RepeatIcon,
  LockIcon,
  ViewIcon,
} from '@chakra-ui/icons';
import api from '../../utils/api';
import { DNSResult, DNSRecord, DNSPropagationResult } from '../../types';

interface QueryHistoryEntry {
  id: string;
  timestamp: string;
  queryType: 'lookup' | 'reverse' | 'zone-transfer' | 'propagation' | 'dnssec';
  query: string;
  recordType?: string;
  server?: string;
  result: DNSResult;
}

export default function DNSTools() {
  const [query, setQuery] = useState('');
  const [queryType, setQueryType] = useState('A');
  const [dnsServer, setDnsServer] = useState('');
  const [results, setResults] = useState<DNSResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();
  const [queryHistory, setQueryHistory] = useState<QueryHistoryEntry[]>([]);
  const [dnssecOptions, setDnssecOptions] = useState({
    validateChain: true,
    checkRevocation: true,
    enforceTimestamps: true,
  });

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  const addToHistory = (entry: Omit<QueryHistoryEntry, 'id' | 'timestamp'>) => {
    const historyEntry: QueryHistoryEntry = {
      ...entry,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date().toISOString(),
    };
    setQueryHistory(prev => [historyEntry, ...prev].slice(0, 100));
  };

  const handleLookup = async () => {
    if (!query) return;

    setIsLoading(true);
    try {
      const response = await api.post('/api/dns/lookup', {
        query,
        type: queryType,
        server: dnsServer || undefined,
      });

      if (response.data.status === 'success') {
        setResults(response.data.result);
        addToHistory({
          queryType: 'lookup',
          query,
          recordType: queryType,
          server: dnsServer,
          result: response.data.result,
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to perform DNS lookup',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleReverseLookup = async () => {
    if (!query) return;

    setIsLoading(true);
    try {
      const response = await api.post('/api/dns/reverse', {
        ip: query,
        server: dnsServer || undefined,
      });

      if (response.data.status === 'success') {
        setResults(response.data.result);
        addToHistory({
          queryType: 'reverse',
          query,
          recordType: queryType,
          server: dnsServer,
          result: response.data.result,
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to perform reverse DNS lookup',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleZoneTransfer = async () => {
    if (!query) return;

    setIsLoading(true);
    try {
      const response = await api.post('/api/dns/zone-transfer', {
        domain: query,
        server: dnsServer || undefined,
      });

      if (response.data.status === 'success') {
        setResults(response.data.result);
        addToHistory({
          queryType: 'zone-transfer',
          query,
          recordType: queryType,
          server: dnsServer,
          result: response.data.result,
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to perform zone transfer',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handlePropagationCheck = async () => {
    if (!query) return;

    setIsLoading(true);
    try {
      const response = await api.post('/api/dns/propagation-check', {
        domain: query,
        type: queryType,
      });

      if (response.data.status === 'success') {
        setResults(response.data.result);
        addToHistory({
          queryType: 'propagation',
          query,
          recordType: queryType,
          server: dnsServer,
          result: response.data.result,
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to perform propagation check',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDNSSECValidation = async () => {
    if (!query) return;

    setIsLoading(true);
    try {
      const response = await api.post('/api/dns/dnssec', {
        query,
        type: queryType,
        server: dnsServer || undefined,
        options: dnssecOptions,
      });

      if (response.data.status === 'success') {
        setResults(response.data.result);
        addToHistory({
          queryType: 'dnssec',
          query,
          recordType: queryType,
          server: dnsServer,
          result: response.data.result,
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to perform DNSSEC validation',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const clearHistory = () => {
    setQueryHistory([]);
  };

  const repeatQuery = (entry: QueryHistoryEntry) => {
    setQuery(entry.query);
    if (entry.recordType) setQueryType(entry.recordType);
    if (entry.server) setDnsServer(entry.server);

    switch (entry.queryType) {
      case 'lookup':
        handleLookup();
        break;
      case 'reverse':
        handleReverseLookup();
        break;
      case 'zone-transfer':
        handleZoneTransfer();
        break;
      case 'propagation':
        handlePropagationCheck();
        break;
      case 'dnssec':
        handleDNSSECValidation();
        break;
    }
  };

  const hasRecords = (results: DNSResult): results is DNSResult & { records: DNSRecord[] } => {
    return 'records' in results && Array.isArray(results.records);
  };

  const hasPropagationResults = (results: DNSResult): results is DNSResult & { results: DNSPropagationResult[] } => {
    return 'results' in results && Array.isArray(results.results);
  };

  return (
    <Card bg={bgColor} borderColor={borderColor}>
      <CardHeader>
        <Heading size="md">DNS Tools</Heading>
      </CardHeader>
      <CardBody>
        <Tabs>
          <TabList>
            <Tab>Forward Lookup</Tab>
            <Tab>Reverse Lookup</Tab>
            <Tab>Zone Transfer</Tab>
            <Tab>Propagation</Tab>
            <Tab>DNSSEC</Tab>
            <Tab>History</Tab>
          </TabList>

          <TabPanels>
            <TabPanel>
              <VStack spacing={4} align="stretch">
                <HStack spacing={4}>
                  <FormControl flex={2}>
                    <FormLabel>Domain</FormLabel>
                    <Input
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="example.com"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Record Type</FormLabel>
                    <Select
                      value={queryType}
                      onChange={(e) => setQueryType(e.target.value)}
                    >
                      <option value="A">A</option>
                      <option value="AAAA">AAAA</option>
                      <option value="MX">MX</option>
                      <option value="NS">NS</option>
                      <option value="TXT">TXT</option>
                      <option value="CNAME">CNAME</option>
                      <option value="SOA">SOA</option>
                    </Select>
                  </FormControl>

                  <FormControl>
                    <FormLabel>DNS Server (optional)</FormLabel>
                    <Input
                      value={dnsServer}
                      onChange={(e) => setDnsServer(e.target.value)}
                      placeholder="8.8.8.8"
                    />
                  </FormControl>
                </HStack>

                <Button
                  leftIcon={<SearchIcon />}
                  onClick={handleLookup}
                  isLoading={isLoading}
                  colorScheme="brand"
                >
                  Lookup
                </Button>

                {results && (
                  <Box>
                    <Text fontWeight="medium" mb={2}>
                      Results from {results.server} ({results.time}ms)
                    </Text>
                    <Table variant="simple">
                      <Thead>
                        <Tr>
                          <Th>Name</Th>
                          <Th>Type</Th>
                          <Th>Data</Th>
                          <Th>TTL</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {results.answers.map((answer, index) => (
                          <Tr key={index}>
                            <Td>{answer.name}</Td>
                            <Td>
                              <Badge>{answer.type}</Badge>
                            </Td>
                            <Td>
                              <Code>{answer.data}</Code>
                            </Td>
                            <Td>{answer.ttl}s</Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </Box>
                )}
              </VStack>
            </TabPanel>

            <TabPanel>
              <VStack spacing={4} align="stretch">
                <FormControl>
                  <FormLabel>IP Address</FormLabel>
                  <Input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="192.168.1.1"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>DNS Server (optional)</FormLabel>
                  <Input
                    value={dnsServer}
                    onChange={(e) => setDnsServer(e.target.value)}
                    placeholder="8.8.8.8"
                  />
                </FormControl>

                <Button
                  leftIcon={<RepeatIcon />}
                  onClick={handleReverseLookup}
                  isLoading={isLoading}
                  colorScheme="brand"
                >
                  Reverse Lookup
                </Button>

                {results && (
                  <Box>
                    <Text fontWeight="medium" mb={2}>
                      Results from {results.server} ({results.time}ms)
                    </Text>
                    <Table variant="simple">
                      <Thead>
                        <Tr>
                          <Th>IP Address</Th>
                          <Th>Hostname</Th>
                          <Th>TTL</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {results.answers.map((answer, index) => (
                          <Tr key={index}>
                            <Td>{query}</Td>
                            <Td>{answer.data}</Td>
                            <Td>{answer.ttl}s</Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </Box>
                )}
              </VStack>
            </TabPanel>

            <TabPanel>
              <VStack spacing={4} align="stretch">
                <FormControl>
                  <FormLabel>Domain</FormLabel>
                  <Input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="example.com"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>DNS Server (optional)</FormLabel>
                  <Input
                    value={dnsServer}
                    onChange={(e) => setDnsServer(e.target.value)}
                    placeholder="ns1.example.com"
                  />
                </FormControl>

                <Button
                  leftIcon={<ViewIcon />}
                  onClick={handleZoneTransfer}
                  isLoading={isLoading}
                  colorScheme="brand"
                >
                  Zone Transfer
                </Button>

                {results && hasRecords(results) && (
                  <Box>
                    <Text fontWeight="medium" mb={2}>
                      Zone Transfer Results
                    </Text>
                    <Table variant="simple">
                      <Thead>
                        <Tr>
                          <Th>Name</Th>
                          <Th>Type</Th>
                          <Th>TTL</Th>
                          <Th>Data</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {results.records.map((record, index) => (
                          <Tr key={index}>
                            <Td>{record.name}</Td>
                            <Td>
                              <Badge>{record.type}</Badge>
                            </Td>
                            <Td>{record.ttl}s</Td>
                            <Td>
                              <Code>{record.data.join(', ')}</Code>
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </Box>
                )}
              </VStack>
            </TabPanel>

            <TabPanel>
              <VStack spacing={4} align="stretch">
                <FormControl>
                  <FormLabel>Domain</FormLabel>
                  <Input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="example.com"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Record Type</FormLabel>
                  <Select
                    value={queryType}
                    onChange={(e) => setQueryType(e.target.value)}
                  >
                    <option value="A">A</option>
                    <option value="AAAA">AAAA</option>
                    <option value="MX">MX</option>
                    <option value="NS">NS</option>
                    <option value="TXT">TXT</option>
                    <option value="CNAME">CNAME</option>
                  </Select>
                </FormControl>

                <Button
                  leftIcon={<RepeatIcon />}
                  onClick={handlePropagationCheck}
                  isLoading={isLoading}
                  colorScheme="brand"
                >
                  Check Propagation
                </Button>

                {results && hasPropagationResults(results) && (
                  <Box>
                    <Text fontWeight="medium" mb={2}>
                      Propagation Results
                    </Text>
                    <Table variant="simple">
                      <Thead>
                        <Tr>
                          <Th>Nameserver</Th>
                          <Th>Status</Th>
                          <Th>Response Time</Th>
                          <Th>Answer</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {results.results.map((result, index) => (
                          <Tr key={index}>
                            <Td>{result.nameserver}</Td>
                            <Td>
                              <Badge
                                colorScheme={
                                  result.status === 'success' ? 'green' : 'red'
                                }
                              >
                                {result.status}
                              </Badge>
                            </Td>
                            <Td>
                              {result.status === 'success'
                                ? `${result.time}ms`
                                : '-'}
                            </Td>
                            <Td>
                              {result.status === 'success' && result.answers ? (
                                <Code>{result.answers.join(', ')}</Code>
                              ) : (
                                <Text color="red.500">{result.error}</Text>
                              )}
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </Box>
                )}
              </VStack>
            </TabPanel>

            <TabPanel>
              <VStack spacing={4} align="stretch">
                <FormControl>
                  <FormLabel>Domain</FormLabel>
                  <Input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="example.com"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Record Type</FormLabel>
                  <Select
                    value={queryType}
                    onChange={(e) => setQueryType(e.target.value)}
                  >
                    <option value="A">A</option>
                    <option value="AAAA">AAAA</option>
                    <option value="MX">MX</option>
                    <option value="NS">NS</option>
                    <option value="TXT">TXT</option>
                    <option value="CNAME">CNAME</option>
                  </Select>
                </FormControl>

                <FormControl>
                  <FormLabel>DNS Server (optional)</FormLabel>
                  <Input
                    value={dnsServer}
                    onChange={(e) => setDnsServer(e.target.value)}
                    placeholder="8.8.8.8"
                  />
                </FormControl>

                <VStack align="start" spacing={2}>
                  <Heading size="sm">Validation Options</Heading>
                  <FormControl display="flex" alignItems="center">
                    <FormLabel mb="0">Validate Trust Chain</FormLabel>
                    <Switch
                      isChecked={dnssecOptions.validateChain}
                      onChange={(e) =>
                        setDnssecOptions(prev => ({
                          ...prev,
                          validateChain: e.target.checked,
                        }))
                      }
                    />
                  </FormControl>

                  <FormControl display="flex" alignItems="center">
                    <FormLabel mb="0">Check Revocation Status</FormLabel>
                    <Switch
                      isChecked={dnssecOptions.checkRevocation}
                      onChange={(e) =>
                        setDnssecOptions(prev => ({
                          ...prev,
                          checkRevocation: e.target.checked,
                        }))
                      }
                    />
                  </FormControl>

                  <FormControl display="flex" alignItems="center">
                    <FormLabel mb="0">Enforce Timestamps</FormLabel>
                    <Switch
                      isChecked={dnssecOptions.enforceTimestamps}
                      onChange={(e) =>
                        setDnssecOptions(prev => ({
                          ...prev,
                          enforceTimestamps: e.target.checked,
                        }))
                      }
                    />
                  </FormControl>
                </VStack>

                <Button
                  leftIcon={<LockIcon />}
                  onClick={handleDNSSECValidation}
                  isLoading={isLoading}
                  colorScheme="brand"
                >
                  Validate DNSSEC
                </Button>

                {results?.dnssec && (
                  <Box>
                    <HStack mb={4}>
                      <Badge
                        colorScheme={results.dnssec.secure ? 'green' : 'red'}
                        fontSize="md"
                        p={2}
                      >
                        {results.dnssec.secure ? 'SECURE' : 'INSECURE'}
                      </Badge>
                      <Badge
                        colorScheme={results.dnssec.validated ? 'green' : 'yellow'}
                        fontSize="md"
                        p={2}
                      >
                        {results.dnssec.validated ? 'VALIDATED' : 'NOT VALIDATED'}
                      </Badge>
                    </HStack>

                    {results.dnssec.chain && (
                      <Table variant="simple">
                        <Thead>
                          <Tr>
                            <Th>Name</Th>
                            <Th>Type</Th>
                            <Th>Algorithm</Th>
                            <Th>Valid From</Th>
                            <Th>Valid Until</Th>
                            <Th>Status</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {results.dnssec.chain.map((link, index) => (
                            <Tr key={index}>
                              <Td>{link.name}</Td>
                              <Td>{link.type}</Td>
                              <Td>{link.algorithm}</Td>
                              <Td>{new Date(link.validFrom).toLocaleString()}</Td>
                              <Td>{new Date(link.validUntil).toLocaleString()}</Td>
                              <Td>
                                <Badge
                                  colorScheme={
                                    link.status === 'valid'
                                      ? 'green'
                                      : link.status === 'invalid'
                                      ? 'red'
                                      : 'yellow'
                                  }
                                >
                                  {link.status.toUpperCase()}
                                </Badge>
                              </Td>
                            </Tr>
                          ))}
                        </Tbody>
                      </Table>
                    )}
                  </Box>
                )}
              </VStack>
            </TabPanel>

            <TabPanel>
              <VStack spacing={4} align="stretch">
                <HStack justify="space-between">
                  <Heading size="sm">Query History</Heading>
                  <Button
                    size="sm"
                    colorScheme="red"
                    variant="outline"
                    onClick={clearHistory}
                  >
                    Clear History
                  </Button>
                </HStack>

                {queryHistory.length === 0 ? (
                  <Text color="gray.500">No queries in history</Text>
                ) : (
                  <Table variant="simple">
                    <Thead>
                      <Tr>
                        <Th>Timestamp</Th>
                        <Th>Type</Th>
                        <Th>Query</Th>
                        <Th>Record Type</Th>
                        <Th>Server</Th>
                        <Th>Actions</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {queryHistory.map((entry) => (
                        <Tr key={entry.id}>
                          <Td>{new Date(entry.timestamp).toLocaleString()}</Td>
                          <Td>
                            <Badge>{entry.queryType}</Badge>
                          </Td>
                          <Td>{entry.query}</Td>
                          <Td>{entry.recordType || '-'}</Td>
                          <Td>{entry.server || 'default'}</Td>
                          <Td>
                            <HStack spacing={2}>
                              <IconButton
                                aria-label="Repeat query"
                                icon={<RepeatIcon />}
                                size="sm"
                                onClick={() => repeatQuery(entry)}
                              />
                              <IconButton
                                aria-label="View results"
                                icon={<ViewIcon />}
                                size="sm"
                                onClick={() => setResults(entry.result)}
                              />
                            </HStack>
                          </Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                )}
              </VStack>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </CardBody>
    </Card>
  );
} 