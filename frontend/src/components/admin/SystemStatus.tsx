import React from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Heading,
  VStack,
  HStack,
  Text,
  Badge,
  CircularProgress,
  CircularProgressLabel,
  Tooltip,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  useColorModeValue,
} from '@chakra-ui/react';

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

interface Props {
  metrics: SystemMetrics;
}

export default function SystemStatus({ metrics }: Props) {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  const getUsageColor = (usage: number) => {
    if (usage >= 90) return 'red';
    if (usage >= 70) return 'yellow';
    return 'green';
  };

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
                  value={metrics.cpu_usage}
                  color={getUsageColor(metrics.cpu_usage)}
                  size="100px"
                >
                  <CircularProgressLabel>
                    {metrics.cpu_usage}%
                  </CircularProgressLabel>
                </CircularProgress>
                <Text textAlign="center" mt={2}>CPU</Text>
              </Box>
            </Tooltip>

            <Tooltip label="Memory Usage">
              <Box>
                <CircularProgress
                  value={metrics.memory_usage}
                  color={getUsageColor(metrics.memory_usage)}
                  size="100px"
                >
                  <CircularProgressLabel>
                    {metrics.memory_usage}%
                  </CircularProgressLabel>
                </CircularProgress>
                <Text textAlign="center" mt={2}>Memory</Text>
              </Box>
            </Tooltip>

            <Tooltip label="Disk Usage">
              <Box>
                <CircularProgress
                  value={metrics.disk_usage}
                  color={getUsageColor(metrics.disk_usage)}
                  size="100px"
                >
                  <CircularProgressLabel>
                    {metrics.disk_usage}%
                  </CircularProgressLabel>
                </CircularProgress>
                <Text textAlign="center" mt={2}>Disk</Text>
              </Box>
            </Tooltip>
          </HStack>

          <HStack spacing={8} justify="space-around">
            <Stat>
              <StatLabel>Uptime</StatLabel>
              <StatNumber>{metrics.uptime}</StatNumber>
            </Stat>

            <Stat>
              <StatLabel>Active Users</StatLabel>
              <StatNumber>{metrics.active_users}</StatNumber>
              <StatHelpText>{metrics.active_sessions} sessions</StatHelpText>
            </Stat>

            <Stat>
              <StatLabel>Database Size</StatLabel>
              <StatNumber>{metrics.database_size}</StatNumber>
              <StatHelpText>Last backup: {metrics.last_backup}</StatHelpText>
            </Stat>
          </HStack>
        </VStack>
      </CardBody>
    </Card>
  );
} 