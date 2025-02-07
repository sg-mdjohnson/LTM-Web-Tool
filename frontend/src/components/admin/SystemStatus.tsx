import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Heading,
  VStack,
  HStack,
  Text,
  CircularProgress,
  CircularProgressLabel,
  Tooltip,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  useColorModeValue,
  Box,
} from '@chakra-ui/react';
import api from '../../utils/api';

interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  uptime: string;
  active_users: number;
  active_sessions: number;
  last_backup: string;
  database_size: string;
}

export default function SystemStatus() {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  const getUsageColor = (usage: number) => {
    if (usage >= 90) return 'red';
    if (usage >= 70) return 'yellow';
    return 'green';
  };

  const [metricsState, setMetricsState] = useState<SystemMetrics>({
    cpu_usage: 0,
    memory_usage: 0,
    disk_usage: 0,
    uptime: '0d 0h 0m',
    active_users: 0,
    active_sessions: 0,
    last_backup: 'Never',
    database_size: '0 MB'
  });

  useEffect(() => {
    const loadMetrics = async () => {
      try {
        const response = await api.get('/api/admin/metrics');
        if (response.data.status === 'success') {
          setMetricsState(response.data.metrics);
        }
      } catch (error) {
        console.error('Failed to load metrics:', error);
      }
    };

    loadMetrics();
    const interval = setInterval(loadMetrics, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <Card bg={bgColor} borderColor={borderColor}>
      <CardHeader>
        <Heading size="md">System Status</Heading>
      </CardHeader>
      <CardBody>
        <VStack spacing={6} align="stretch">
          <HStack spacing={8} justify="center">
            <Tooltip label="CPU Usage">
              <Box>
                <CircularProgress
                  value={metricsState.cpu_usage}
                  color={getUsageColor(metricsState.cpu_usage)}
                  size="100px"
                >
                  <CircularProgressLabel>
                    {metricsState.cpu_usage}%
                  </CircularProgressLabel>
                </CircularProgress>
                <Text textAlign="center" mt={2}>CPU</Text>
              </Box>
            </Tooltip>

            <Tooltip label="Memory Usage">
              <Box>
                <CircularProgress
                  value={metricsState.memory_usage}
                  color={getUsageColor(metricsState.memory_usage)}
                  size="100px"
                >
                  <CircularProgressLabel>
                    {metricsState.memory_usage}%
                  </CircularProgressLabel>
                </CircularProgress>
                <Text textAlign="center" mt={2}>Memory</Text>
              </Box>
            </Tooltip>

            <Tooltip label="Disk Usage">
              <Box>
                <CircularProgress
                  value={metricsState.disk_usage}
                  color={getUsageColor(metricsState.disk_usage)}
                  size="100px"
                >
                  <CircularProgressLabel>
                    {metricsState.disk_usage}%
                  </CircularProgressLabel>
                </CircularProgress>
                <Text textAlign="center" mt={2}>Disk</Text>
              </Box>
            </Tooltip>
          </HStack>

          <HStack spacing={8} justify="space-around">
            <Stat>
              <StatLabel>Uptime</StatLabel>
              <StatNumber>{metricsState.uptime}</StatNumber>
            </Stat>

            <Stat>
              <StatLabel>Active Users</StatLabel>
              <StatNumber>{metricsState.active_users}</StatNumber>
              <StatHelpText>{metricsState.active_sessions} sessions</StatHelpText>
            </Stat>

            <Stat>
              <StatLabel>Database Size</StatLabel>
              <StatNumber>{metricsState.database_size}</StatNumber>
              <StatHelpText>Last backup: {metricsState.last_backup}</StatHelpText>
            </Stat>
          </HStack>
        </VStack>
      </CardBody>
    </Card>
  );
} 