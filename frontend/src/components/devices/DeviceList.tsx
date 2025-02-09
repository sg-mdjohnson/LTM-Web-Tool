import React, { useEffect } from 'react';
import {
  VStack,
  SimpleGrid,
  Button,
  useDisclosure,
  Box,
  Text,
  Spinner
} from '@chakra-ui/react';
import { AddIcon } from '@chakra-ui/icons';
import { DeviceCard } from './DeviceCard';
import { AddDeviceModal } from './AddDeviceModal';
import { useDevices } from '../../hooks/useDevices';

export const DeviceList: React.FC = () => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { devices, loading, error, fetchDevices } = useDevices();

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  if (loading) return <Spinner />;
  if (error) return <Text color="red.500">{error}</Text>;

  return (
    <Box p={4}>
      <Button
        leftIcon={<AddIcon />}
        colorScheme="blue"
        mb={4}
        onClick={onOpen}
      >
        Add Device
      </Button>

      <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
        {devices.map((device) => (
          <DeviceCard key={device.id} device={device} />
        ))}
      </SimpleGrid>

      <AddDeviceModal isOpen={isOpen} onClose={onClose} />
    </Box>
  );
}; 