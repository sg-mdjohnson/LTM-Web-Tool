import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  Select,
  HStack,
  Text,
  Code,
  Button,
  useToast,
  Badge,
  Flex,
  Spacer,
} from '@chakra-ui/react';
import { DownloadIcon, RepeatIcon } from '@chakra-ui/icons';
import api from '../../utils/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorAlert from '../common/ErrorAlert';

interface LogEntry {
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
  message: string;
  source: string;
}

const LOG_TYPES = [
  { value: 'all', label: 'All Logs' },
  { value: 'app', label: 'Application Logs' },
  { value: 'audit', label: 'Audit Logs' },
  { value: 'cli', label: 'CLI Logs' },
  { value: 'auth', label: 'Authentication Logs' },
];

const TIME_PERIODS = [
  { value: '1', label: 'Last 24 Hours' },
  { value: '7', label: 'Last 7 Days' },
  { value: '30', label: 'Last 30 Days' },
  { value: 'all', label: 'All Time' },
];

export default function SystemLogs() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [logType, setLogType] = useState('all');
  const [timePeriod, setTimePeriod] = useState('7');
  const toast = useToast();

  useEffect(() => {
    loadLogs();
  }, [logType, timePeriod]);

  const loadLogs = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/api/admin/logs', {
        params: {
          type: logType,
          days: timePeriod === 'all' ? undefined : timePeriod,
        },
      });
      if (response.data.status === 'success') {
        setLogs(response.data.logs);
      }
    } catch (error) {
      setError('Failed to load system logs');
      toast({
        title: 'Error',
        description: 'Failed to load logs',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      const response = await api.get('/api/admin/logs/download', {
        params: {
          type: logType,
          days: timePeriod === 'all' ? undefined : timePeriod,
        },
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `system-logs-${new Date().toISOString()}.txt`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to download logs',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR':
        return 'red';
      case 'WARNING':
        return 'yellow';
      case 'INFO':
        return 'blue';
      case 'DEBUG':
        return 'gray';
      default:
        return 'gray';
    }
  };

  if (error) {
    return <ErrorAlert message={error} />;
  }

  return (
    <VStack spacing={4} align="stretch">
      <Flex gap={4} wrap="wrap">
        <HStack>
          <Text>Log Type:</Text>
          <Select
            value={logType}
            onChange={(e) => setLogType(e.target.value)}
            width="200px"
          >
            {LOG_TYPES.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </Select>
        </HStack>

        <HStack>
          <Text>Time Period:</Text>
          <Select
            value={timePeriod}
            onChange={(e) => setTimePeriod(e.target.value)}
            width="200px"
          >
            {TIME_PERIODS.map(period => (
              <option key={period.value} value={period.value}>
                {period.label}
              </option>
            ))}
          </Select>
        </HStack>

        <Spacer />

        <HStack>
          <Button
            leftIcon={<RepeatIcon />}
            onClick={loadLogs}
            isLoading={isLoading}
          >
            Refresh
          </Button>
          <Button
            leftIcon={<DownloadIcon />}
            onClick={handleDownload}
            colorScheme="brand"
          >
            Download
          </Button>
        </HStack>
      </Flex>

      {isLoading ? (
        <LoadingSpinner message="Loading logs..." />
      ) : (
        <Box
          borderWidth={1}
          borderRadius="md"
          p={4}
          maxH="600px"
          overflowY="auto"
          fontFamily="mono"
        >
          {logs.length === 0 ? (
            <Text color="gray.500" textAlign="center">No logs found</Text>
          ) : (
            <VStack spacing={2} align="stretch">
              {logs.map((log, index) => (
                <Box key={index} fontSize="sm">
                  <HStack spacing={2} mb={1}>
                    <Text color="gray.500">
                      {new Date(log.timestamp).toLocaleString()}
                    </Text>
                    <Badge colorScheme={getLevelColor(log.level)}>
                      {log.level}
                    </Badge>
                    <Text color="gray.500">[{log.source}]</Text>
                  </HStack>
                  <Code
                    display="block"
                    whiteSpace="pre-wrap"
                    p={2}
                    borderRadius="md"
                  >
                    {log.message}
                  </Code>
                </Box>
              ))}
            </VStack>
          )}
        </Box>
      )}
    </VStack>
  );
} 