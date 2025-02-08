import React, { useState, useEffect } from 'react';
import {
  Box,
  Select,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  HStack,
  Input,
  Button,
  useColorModeValue,
  Text,
  VStack,
} from '@chakra-ui/react';
import { DownloadIcon, RepeatIcon } from '@chakra-ui/icons';
import api from '../../utils/api';
import { useApiError } from '../../utils/api';
import LoadingSpinner from '../common/LoadingSpinner';

interface LogEntry {
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
  source: string;
  message: string;
  details?: string;
}

export default function SystemLogs() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [logType, setLogType] = useState('app');
  const [filter, setFilter] = useState('');
  const [days, setDays] = useState(7);
  const { handleError } = useApiError();

  const bgColor = useColorModeValue('white', 'gray.800');

  useEffect(() => {
    fetchLogs();
  }, [logType, days]);

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/api/admin/logs', {
        params: { type: logType, days }
      });
      setLogs(response.data.logs);
    } catch (error) {
      handleError(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await api.get('/api/admin/logs/export', {
        params: { type: logType, days },
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `system-logs-${logType}-${new Date().toISOString()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      handleError(error);
    }
  };

  const getLevelBadge = (level: string) => {
    const colors: Record<string, string> = {
      ERROR: 'red',
      WARNING: 'yellow',
      INFO: 'blue',
      DEBUG: 'gray'
    };
    return <Badge colorScheme={colors[level]}>{level}</Badge>;
  };

  const filteredLogs = logs.filter(log => 
    log.message.toLowerCase().includes(filter.toLowerCase()) ||
    log.source.toLowerCase().includes(filter.toLowerCase())
  );

  if (isLoading) return <LoadingSpinner message="Loading logs..." />;

  return (
    <Box bg={bgColor} p={4} borderRadius="lg" shadow="sm">
      <VStack spacing={4} align="stretch">
        <HStack spacing={4}>
          <Select
            value={logType}
            onChange={(e) => setLogType(e.target.value)}
            w="200px"
          >
            <option value="app">Application Logs</option>
            <option value="audit">Audit Logs</option>
            <option value="error">Error Logs</option>
            <option value="access">Access Logs</option>
          </Select>

          <Select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            w="150px"
          >
            <option value={1}>Last 24 hours</option>
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </Select>

          <Input
            placeholder="Filter logs..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            flex={1}
          />

          <Button
            leftIcon={<RepeatIcon />}
            onClick={fetchLogs}
          >
            Refresh
          </Button>

          <Button
            leftIcon={<DownloadIcon />}
            onClick={handleExport}
          >
            Export
          </Button>
        </HStack>

        <Box overflowX="auto">
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Timestamp</Th>
                <Th>Level</Th>
                <Th>Source</Th>
                <Th>Message</Th>
              </Tr>
            </Thead>
            <Tbody>
              {filteredLogs.map((log, index) => (
                <Tr key={index}>
                  <Td whiteSpace="nowrap">
                    {new Date(log.timestamp).toLocaleString()}
                  </Td>
                  <Td>{getLevelBadge(log.level)}</Td>
                  <Td>{log.source}</Td>
                  <Td>
                    <Text>{log.message}</Text>
                    {log.details && (
                      <Text fontSize="sm" color="gray.500" mt={1}>
                        {log.details}
                      </Text>
                    )}
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>

        {filteredLogs.length === 0 && (
          <Text textAlign="center" color="gray.500" py={8}>
            No logs found matching your criteria
          </Text>
        )}
      </VStack>
    </Box>
  );
} 