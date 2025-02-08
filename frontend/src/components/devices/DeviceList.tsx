import React, { useState, useEffect } from 'react';
import {
  VStack,
  SimpleGrid,
  Text,
  Box,
  useToast,
  Button,
  useDisclosure,
  HStack,
  Heading,
} from '@chakra-ui/react';
import { AddIcon } from '@chakra-ui/icons';
import api from '../../utils/api';
import DeviceCard from './DeviceCard';
import LoadingSpinner from '../common/LoadingSpinner';
import AddDeviceModal from './AddDeviceModal';
import { Device } from '../../types/device';

export default function DeviceList() {
  console.log('DeviceList rendering...');
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();

  const loadDevices = React.useCallback(async () => {
    try {
      const response = await api.get('/api/devices');
      if (response.data) {
        setDevices(response.data);
      }
    } catch (error) {
      console.error('Failed to load devices:', error);
      toast({
        title: 'Error',
        description: 'Failed to load devices',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadDevices();
  }, [loadDevices]);

  const handleDeleteDevice = async (deviceId: number) => {
    try {
      await api.delete(`/api/devices/${deviceId}`);
      await loadDevices();
      toast({
        title: 'Success',
        description: 'Device deleted successfully',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Failed to delete device:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete device',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleTestConnection = async (deviceId: number) => {
    try {
      const response = await api.post(`/api/devices/${deviceId}/test`);
      return response.data.status === 'success';
    } catch (error) {
      console.error('Failed to test device connection:', error);
      return false;
    }
  };

  const handleAddDevice = async () => {
    await loadDevices();
    onClose();
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading devices..." />;
  }

  return (
    <Box>
      <Heading mb={4}>Devices</Heading>
      <VStack spacing={4} align="stretch">
        <HStack justify="flex-end">
          <Button
            leftIcon={<AddIcon />}
            colorScheme="brand"
            onClick={onOpen}
          >
            Add Device
          </Button>
        </HStack>

        {!devices || devices.length === 0 ? (
          <Box
            p={8}
            textAlign="center"
            borderWidth={1}
            borderRadius="lg"
            borderStyle="dashed"
          >
            <Text color="gray.500">No devices added yet.</Text>
          </Box>
        ) : (
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
            {devices.map(device => (
              <DeviceCard
                key={device.id}
                device={device}
                onDelete={handleDeleteDevice}
                onTest={handleTestConnection}
              />
            ))}
          </SimpleGrid>
        )}

        <AddDeviceModal
          isOpen={isOpen}
          onClose={onClose}
          onAdd={handleAddDevice}
        />
      </VStack>
    </Box>
  );
} 