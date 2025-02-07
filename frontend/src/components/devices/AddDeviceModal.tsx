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
import { Device } from '../../types/device';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: Partial<Device>) => Promise<void>;
}

interface FormInputs {
  name: string;
  host: string;
  username: string;
  password: string;
  description?: string;
}

export default function AddDeviceModal({ isOpen, onClose, onSubmit }: Props) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormInputs>();

  const toast = useToast();

  const onSubmitForm = async (data: FormInputs) => {
    try {
      await onSubmit(data);
      reset();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to add device',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="md">
      <ModalOverlay />
      <ModalContent>
        <form onSubmit={handleSubmit(onSubmitForm)}>
          <ModalHeader>Add New Device</ModalHeader>
          <ModalCloseButton />
          
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isInvalid={!!errors.name} isRequired>
                <FormLabel>Device Name</FormLabel>
                <Input
                  {...register('name', {
                    required: 'Name is required',
                    minLength: { value: 2, message: 'Minimum length should be 2' }
                  })}
                  placeholder="Enter device name"
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
                      value: /^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
                      message: 'Invalid hostname format'
                    }
                  })}
                  placeholder="e.g., ltm.example.com"
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
            <Button variant="ghost" mr={3} onClick={handleClose}>
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