import React, { useState } from 'react';
import {
  Box,
  Heading,
  Text,
  Badge,
  HStack,
  useColorModeValue,
  IconButton,
  Tooltip,
  VStack,
} from '@chakra-ui/react';
import {
  DeleteIcon,
  RepeatIcon,
  TimeIcon,
  WarningIcon,
  CheckCircleIcon,
  NotAllowedIcon,
  ViewIcon
} from '@chakra-ui/icons';
import { Device } from '../../types/device';

interface Props {
  device: Device;
  onDelete: (id: number) => Promise<void>;
  onTest: (id: number) => Promise<boolean>;
}

export default function DeviceCard({ device, onDelete, onTest }: Props) {
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'untested' | 'success' | 'failed'>('untested');

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  const handleTestConnection = async () => {
    setIsTestingConnection(true);
    try {
      const success = await onTest(device.id);
      setConnectionStatus(success ? 'success' : 'failed');
    } finally {
      setIsTestingConnection(false);
    }
  };

  const getStatusColor = (status: string | undefined): string => {
    switch (status) {
      case 'active':
        return 'green';
      case 'inactive':
        return 'yellow';
      case 'error':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getStatusIcon = (status: string | undefined) => {
    switch (status) {
      case 'active':
        return <CheckCircleIcon color="green.500" />;
      case 'inactive':
        return <WarningIcon color="orange.500" />;
      case 'error':
        return <NotAllowedIcon color="red.500" />;
      default:
        return <WarningIcon color="gray.500" />;
    }
  };

  return (
    <Box
      p={5}
      borderWidth={1}
      borderRadius="lg"
      bg={bgColor}
      borderColor={borderColor}
      position="relative"
    >
      <VStack align="stretch" spacing={3}>
        <HStack justify="space-between">
          <HStack>
            <ViewIcon boxSize={5} />
            <Heading size="md">{device.name}</Heading>
          </HStack>
          <HStack>
            {getStatusIcon(device.status)}
            <Badge colorScheme={getStatusColor(device.status)}>
              {device.status || 'unknown'}
            </Badge>
          </HStack>
        </HStack>

        <Text color="gray.500">{device.host}</Text>
        {device.description && (
          <Text fontSize="sm" noOfLines={2}>
            {device.description}
          </Text>
        )}

        <HStack justify="space-between" mt={4}>
          <HStack>
            <Tooltip label="Test Connection">
              <IconButton
                aria-label="Test connection"
                icon={<RepeatIcon />}
                size="sm"
                isLoading={isTestingConnection}
                colorScheme={
                  connectionStatus === 'success'
                    ? 'green'
                    : connectionStatus === 'failed'
                    ? 'red'
                    : 'gray'
                }
                onClick={handleTestConnection}
              />
            </Tooltip>
            <Tooltip label="Delete Device">
              <IconButton
                aria-label="Delete device"
                icon={<DeleteIcon />}
                size="sm"
                colorScheme="red"
                variant="ghost"
                onClick={() => onDelete(device.id)}
              />
            </Tooltip>
          </HStack>

          {device.last_used && (
            <HStack spacing={1} fontSize="xs" color="gray.500">
              <TimeIcon boxSize={3} />
              <Text>Last used: {new Date(device.last_used).toLocaleDateString()}</Text>
            </HStack>
          )}
        </HStack>
      </VStack>
    </Box>
  );
} 