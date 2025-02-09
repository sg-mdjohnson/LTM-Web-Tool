import React from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Button,
  Text,
  useToast
} from '@chakra-ui/react';
import { Device } from '../../types/device';
import { useDevices } from '../../hooks/useDevices';

interface DeleteDeviceModalProps {
  isOpen: boolean;
  onClose: () => void;
  device: Device;
}

export const DeleteDeviceModal: React.FC<DeleteDeviceModalProps> = ({
  isOpen,
  onClose,
  device
}) => {
  const { deleteDevice } = useDevices();
  const toast = useToast();

  const handleDelete = async () => {
    try {
      await deleteDevice(device.id);
      toast({
        title: 'Device deleted successfully',
        status: 'success',
        duration: 3000,
      });
      onClose();
    } catch (error) {
      toast({
        title: 'Failed to delete device',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Delete Device</ModalHeader>
        <ModalBody>
          <Text>
            Are you sure you want to delete {device.name}? This action cannot be undone.
          </Text>
        </ModalBody>

        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            Cancel
          </Button>
          <Button colorScheme="red" onClick={handleDelete}>
            Delete
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}; 