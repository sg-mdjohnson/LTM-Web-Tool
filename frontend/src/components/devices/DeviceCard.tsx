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
  useDisclosure
} from '@chakra-ui/react';
import {
  DeleteIcon,
  RepeatIcon,
  TimeIcon,
  WarningIcon,
  CheckCircleIcon,
  NotAllowedIcon,
  ViewIcon,
  EditIcon
} from '@chakra-ui/icons';
import { Device } from '../../types/device';
import { EditDeviceModal } from './EditDeviceModal';
import { DeleteDeviceModal } from './DeleteDeviceModal';

interface DeviceCardProps {
  device: Device;
}

export const DeviceCard: React.FC<DeviceCardProps> = ({ device }) => {
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'untested' | 'success' | 'failed'>('untested');
  const editModal = useDisclosure();
  const deleteModal = useDisclosure();

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'inactive': return 'gray';
      case 'error': return 'red';
      default: return 'yellow';
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
            <Tooltip label="Edit Device">
              <IconButton
                aria-label="Edit device"
                icon={<EditIcon />}
                size="sm"
                onClick={editModal.onOpen}
              />
            </Tooltip>
            <Tooltip label="Delete Device">
              <IconButton
                aria-label="Delete device"
                icon={<DeleteIcon />}
                size="sm"
                colorScheme="red"
                onClick={deleteModal.onOpen}
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

      <EditDeviceModal
        isOpen={editModal.isOpen}
        onClose={editModal.onClose}
        device={device}
      />
      <DeleteDeviceModal
        isOpen={deleteModal.isOpen}
        onClose={deleteModal.onClose}
        device={device}
      />
    </Box>
  );
}; 