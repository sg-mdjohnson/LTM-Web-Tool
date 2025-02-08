import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Progress,
  useColorModeValue,
} from '@chakra-ui/react';
import api from '../../utils/api';
import { useApiError } from '../../utils/api';
import LoadingSpinner from '../common/LoadingSpinner';

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
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { handleError } = useApiError();
  const bgColor = useColorModeValue('white', 'gray.800');

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await api.get('/api/admin/metrics');
      setMetrics(response.data.metrics);
    } catch (error) {
      handleError(error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) return <LoadingSpinner message="Loading system metrics..." />;
  if (!metrics) return null;

  return (
    <Grid templateColumns="repeat(2, 1fr)" gap={6}>
      <Box p={5} shadow="md" borderWidth="1px" borderRadius="lg" bg={bgColor}>
        <Stat>
          <StatLabel>CPU Usage</StatLabel>
          <StatNumber>{metrics.cpu_usage}%</StatNumber>
          <Progress value={metrics.cpu_usage} colorScheme={metrics.cpu_usage > 80 ? 'red' : 'green'} />
        </Stat>
      </Box>

      <Box p={5} shadow="md" borderWidth="1px" borderRadius="lg" bg={bgColor}>
        <Stat>
          <StatLabel>Memory Usage</StatLabel>
          <StatNumber>{metrics.memory_usage}%</StatNumber>
          <Progress value={metrics.memory_usage} colorScheme={metrics.memory_usage > 80 ? 'red' : 'green'} />
        </Stat>
      </Box>

      <Box p={5} shadow="md" borderWidth="1px" borderRadius="lg" bg={bgColor}>
        <Stat>
          <StatLabel>Disk Usage</StatLabel>
          <StatNumber>{metrics.disk_usage}%</StatNumber>
          <Progress value={metrics.disk_usage} colorScheme={metrics.disk_usage > 80 ? 'red' : 'green'} />
        </Stat>
      </Box>

      <Box p={5} shadow="md" borderWidth="1px" borderRadius="lg" bg={bgColor}>
        <Stat>
          <StatLabel>System Uptime</StatLabel>
          <StatNumber>{metrics.uptime}</StatNumber>
        </Stat>
      </Box>

      <Box p={5} shadow="md" borderWidth="1px" borderRadius="lg" bg={bgColor}>
        <Stat>
          <StatLabel>Active Users</StatLabel>
          <StatNumber>{metrics.active_users}</StatNumber>
          <StatHelpText>{metrics.active_sessions} active sessions</StatHelpText>
        </Stat>
      </Box>

      <Box p={5} shadow="md" borderWidth="1px" borderRadius="lg" bg={bgColor}>
        <Stat>
          <StatLabel>Last Backup</StatLabel>
          <StatNumber>{new Date(metrics.last_backup).toLocaleString()}</StatNumber>
          <StatHelpText>Database Size: {metrics.database_size}</StatHelpText>
        </Stat>
      </Box>
    </Grid>
  );
} 