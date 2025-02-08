import React from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Textarea,
  useToast,
  FormErrorMessage,
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';
import api from '../../utils/api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onAdd: () => void;
}

interface FormData {
  name: string;
  host: string;
  username: string;
  password: string;
  description?: string;
}

export default function AddDeviceModal({ isOpen, onClose, onAdd }: Props) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormData>();

  const toast = useToast();

  const onSubmit = async (data: FormData) => {
    try {
      const response = await api.post('/api/devices', {
        name: data.name,
        host: data.host,
        username: data.username,
        password: data.password,
        description: data.description || undefined
      });

      if (response.data.status === 'success') {
        toast({
          title: 'Success',
          description: 'Device added successfully',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
        reset();
        onAdd();
        onClose();
      } else {
        throw new Error(response.data.message || 'Failed to add device');
      }
    } catch (error: any) {
      console.error('Error adding device:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.message || error.message || 'Failed to add device',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="md">
      <ModalOverlay />
      <ModalContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <ModalHeader>Add Device</ModalHeader>
          <ModalCloseButton />
          
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isInvalid={!!errors.name} isRequired>
                <FormLabel>Name</FormLabel>
                <Input
                  {...register('name', {
                    required: 'Name is required',
                    minLength: { value: 2, message: 'Minimum length should be 2' }
                  })}
                  placeholder="Device name"
                />
                <FormErrorMessage>
                  {errors.name && errors.name.message}
                </FormErrorMessage>
              </FormControl>

              <FormControl isInvalid={!!errors.host} isRequired>
                <FormLabel>Host</FormLabel>
                <Input
                  {...register('host', {
                    required: 'Host is required',
                    pattern: {
                      value: /^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/,
                      message: 'Invalid hostname or IP address format'
                    }
                  })}
                  placeholder="hostname or IP address"
                />
                <FormErrorMessage>
                  {errors.host && errors.host.message}
                </FormErrorMessage>
              </FormControl>

              <FormControl isInvalid={!!errors.username} isRequired>
                <FormLabel>Username</FormLabel>
                <Input
                  {...register('username', {
                    required: 'Username is required'
                  })}
                  placeholder="Enter username"
                />
                <FormErrorMessage>
                  {errors.username && errors.username.message}
                </FormErrorMessage>
              </FormControl>

              <FormControl isInvalid={!!errors.password} isRequired>
                <FormLabel>Password</FormLabel>
                <Input
                  type="password"
                  {...register('password', {
                    required: 'Password is required'
                  })}
                  placeholder="Enter password"
                />
                <FormErrorMessage>
                  {errors.password && errors.password.message}
                </FormErrorMessage>
              </FormControl>

              <FormControl isInvalid={!!errors.description}>
                <FormLabel>Description</FormLabel>
                <Textarea
                  {...register('description')}
                  placeholder="Enter device description (optional)"
                />
                <FormErrorMessage>
                  {errors.description && errors.description.message}
                </FormErrorMessage>
              </FormControl>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="brand"
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
} 