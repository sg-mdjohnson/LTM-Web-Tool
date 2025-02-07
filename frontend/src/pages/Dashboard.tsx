import React, { useEffect, useState } from 'react';
import {
  Box,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Heading,
  useColorModeValue,
  VStack,
  Text,
} from '@chakra-ui/react';
import api from '../utils/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorAlert from '../components/common/ErrorAlert';

interface DashboardStats {
  totalDevices: number;
  activeDevices: number;
  totalCommands: number;
  commandsToday: number;
  lastCommand?: {
    command: string;
    timestamp: string;
    device: string;
  };
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    loadDashboardStats();
  }, []);

  const loadDashboardStats = async () => {
    try {
      const response = await api.get('/api/dashboard/stats');
      if (response.data.status === 'success') {
        setStats(response.data.stats);
      }
    } catch (error) {
      setError('Failed to load dashboard statistics');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading dashboard..." />;
  }

  if (error) {
    return <ErrorAlert message={error} />;
  }

  return (
    <VStack spacing={6} align="stretch">
      <Heading size="lg">Dashboard</Heading>

      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
        <StatCard
          label="Total Devices"
          value={stats?.totalDevices || 0}
          helpText="Registered devices"
        />
        <StatCard
          label="Active Devices"
          value={stats?.activeDevices || 0}
          helpText="Currently active"
        />
        <StatCard
          label="Total Commands"
          value={stats?.totalCommands || 0}
          helpText="All time"
        />
        <StatCard
          label="Commands Today"
          value={stats?.commandsToday || 0}
          helpText="Last 24 hours"
        />
      </SimpleGrid>

      {stats?.lastCommand && (
        <Box p={5} borderWidth={1} borderRadius="lg" bg={bgColor} borderColor={borderColor}>
          <Heading size="md" mb={4}>Last Command</Heading>
          <VStack align="stretch" spacing={2}>
            <Text><strong>Command:</strong> {stats.lastCommand.command}</Text>
            <Text><strong>Device:</strong> {stats.lastCommand.device}</Text>
            <Text><strong>Time:</strong> {new Date(stats.lastCommand.timestamp).toLocaleString()}</Text>
          </VStack>
        </Box>
      )}
    </VStack>
  );
}

interface StatCardProps {
  label: string;
  value: number;
  helpText: string;
}

function StatCard({ label, value, helpText }: StatCardProps) {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Box p={5} borderWidth={1} borderRadius="lg" bg={bgColor} borderColor={borderColor}>
      <Stat>
        <StatLabel>{label}</StatLabel>
        <StatNumber>{value}</StatNumber>
        <StatHelpText>{helpText}</StatHelpText>
      </Stat>
    </Box>
  );
} 