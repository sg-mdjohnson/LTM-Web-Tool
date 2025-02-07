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
  Tooltip,
  Icon,
  useColorModeValue,
  Button,
} from '@chakra-ui/react';
import { CheckCircleIcon, WarningIcon, RepeatIcon } from '@chakra-ui/icons';

interface HealthCheck {
  name: string;
  status: 'healthy' | 'warning' | 'error';
  message: string;
  lastCheck: string;
  details?: string;
}

interface Props {
  checks: HealthCheck[];
  onRefresh: () => void;
  isRefreshing: boolean;
}

export default function SystemHealth({ checks, onRefresh, isRefreshing }: Props) {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon color="green.500" />;
      case 'warning':
        return <WarningIcon color="yellow.500" />;
      case 'error':
        return <WarningIcon color="red.500" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'green';
      case 'warning':
        return 'yellow';
      case 'error':
        return 'red';
      default:
        return 'gray';
    }
  };

  return (
    <Card bg={bgColor} borderColor={borderColor}>
      <CardHeader>
        <HStack justify="space-between">
          <Heading size="md">System Health</Heading>
          <Button
            leftIcon={<RepeatIcon />}
            onClick={onRefresh}
            isLoading={isRefreshing}
            size="sm"
          >
            Refresh
          </Button>
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack spacing={4} align="stretch">
          {checks.map((check, index) => (
            <HStack
              key={index}
              p={3}
              borderWidth={1}
              borderRadius="md"
              borderColor={borderColor}
              spacing={4}
            >
              <Tooltip label={check.details || check.message}>
                <Icon as={() => getStatusIcon(check.status)} boxSize={5} />
              </Tooltip>
              <VStack align="stretch" flex={1} spacing={1}>
                <HStack justify="space-between">
                  <Text fontWeight="medium">{check.name}</Text>
                  <Badge colorScheme={getStatusColor(check.status)}>
                    {check.status.toUpperCase()}
                  </Badge>
                </HStack>
                <Text fontSize="sm" color="gray.500">
                  {check.message}
                </Text>
                <Text fontSize="xs" color="gray.400">
                  Last checked: {new Date(check.lastCheck).toLocaleString()}
                </Text>
              </VStack>
            </HStack>
          ))}
        </VStack>
      </CardBody>
    </Card>
  );
} 