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
import { useDevices } from '../../hooks/useDevices';

interface AddDeviceModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface FormData {
  name: string;
  host: string;
  username: string;
  password: string;
}

export const AddDeviceModal: React.FC<AddDeviceModalProps> = ({ isOpen, onClose }) => {
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<FormData>();
  const { addDevice } = useDevices();
  const toast = useToast();

  const onSubmit = async (data: FormData) => {
    try {
      await addDevice(data);
      toast({
        title: 'Device added successfully',
        status: 'success',
        duration: 3000,
      });
      reset();
      onClose();
    } catch (error) {
      toast({
        title: 'Failed to add device',
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
          <ModalHeader>Add New Device</ModalHeader>
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

              <FormControl isRequired isInvalid={!!errors.password}>
                <FormLabel>Password</FormLabel>
                <Input 
                  type="password" 
                  {...register('password', { required: 'Password is required' })} 
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
              Add Device
            </Button>
          </ModalFooter>
        </form>
      </ModalContent>
    </Modal>
  );
}; 