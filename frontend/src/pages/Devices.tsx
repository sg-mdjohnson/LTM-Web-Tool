import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  Button,
  useDisclosure,
  useToast,
  SimpleGrid,
  Text,
  Badge,
  useColorModeValue,
} from '@chakra-ui/react';
import { AddIcon } from '@chakra-ui/icons';
import api from '../utils/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import DeviceCard from '../components/devices/DeviceCard';
import AddDeviceModal from '../components/devices/AddDeviceModal';
import { Device } from '../types/device';

export default function Devices() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();

  useEffect(() => {
    loadDevices();
  }, []);

  const loadDevices = async () => {
    try {
      const response = await api.get('/api/device/list');
      if (response.data.status === 'success') {
        setDevices(response.data.devices);
      }
    } catch (error) {
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
  };

  const handleAddDevice = async () => {
    try {
      await loadDevices();
      onClose();
    } catch (error) {
      console.error('Error reloading devices:', error);
    }
  };

  const handleDeleteDevice = async (deviceId: number) => {
    try {
      const response = await api.delete(`/api/device/${deviceId}`);
      if (response.data.status === 'success') {
        toast({
          title: 'Success',
          description: 'Device deleted successfully',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
        loadDevices();
      }
    } catch (error) {
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
      const response = await api.post(`/api/device/${deviceId}/test`);
      return response.data.status === 'success';
    } catch (error) {
      return false;
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading devices..." />;
  }

  return (
    <Box>
      <VStack spacing={4} align="stretch">
        <Button
          leftIcon={<AddIcon />}
          colorScheme="brand"
          onClick={onOpen}
          alignSelf="flex-end"
        >
          Add Device
        </Button>

        {devices.length === 0 ? (
          <Box
            p={8}
            textAlign="center"
            borderWidth={1}
            borderRadius="lg"
            borderStyle="dashed"
          >
            <Text color="gray.500">No devices added yet. Click "Add Device" to get started.</Text>
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
      </VStack>

      <AddDeviceModal
        isOpen={isOpen}
        onClose={onClose}
        onAdd={handleAddDevice}
      />
    </Box>
  );
} 