import React from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Button,
  VStack,
  FormControl,
  FormLabel,
  Input,
  useToast
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';
import { Device } from '../../types/device';
import { useDevices } from '../../hooks/useDevices';

interface EditDeviceModalProps {
  isOpen: boolean;
  onClose: () => void;
  device: Device;
}

interface FormData {
  name: string;
  host: string;
  username: string;
  password?: string;
}

export const EditDeviceModal: React.FC<EditDeviceModalProps> = ({ 
  isOpen, 
  onClose, 
  device 
}) => {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    defaultValues: {
      name: device.name,
      host: device.host,
      username: device.username
    }
  });
  
  const { updateDevice } = useDevices();
  const toast = useToast();

  const onSubmit = async (data: FormData) => {
    try {
      await updateDevice(device.id, data);
      toast({
        title: 'Device updated successfully',
        status: 'success',
        duration: 3000,
      });
      onClose();
    } catch (error) {
      toast({
        title: 'Failed to update device',
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
        <form onSubmit={handleSubmit(onSubmit)}>
          <ModalHeader>Edit Device</ModalHeader>
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired isInvalid={!!errors.name}>
                <FormLabel>Device Name</FormLabel>
                <Input {...register('name', { required: 'Name is required' })} />
              </FormControl>

              <FormControl isRequired isInvalid={!!errors.host}>
                <FormLabel>Host</FormLabel>
                <Input {...register('host', { required: 'Host is required' })} />
              </FormControl>

              <FormControl isRequired isInvalid={!!errors.username}>
                <FormLabel>Username</FormLabel>
                <Input {...register('username', { required: 'Username is required' })} />
              </FormControl>

              <FormControl>
                <FormLabel>Password (leave blank to keep current)</FormLabel>
                <Input 
                  type="password" 
                  {...register('password')} 
                />
              </FormControl>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="blue" 
              type="submit"
              isLoading={isSubmitting}
            >
              Save Changes
            </Button>
          </ModalFooter>
        </form>
      </ModalContent>
    </Modal>
  );
}; 