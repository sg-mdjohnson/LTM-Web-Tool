import React, { useEffect } from 'react';
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
  Select,
  Switch,
  VStack,
  FormErrorMessage,
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: Partial<User>) => Promise<void>;
  user: User | null;
}

interface FormInputs {
  email: string;
  role: string;
  is_active: boolean;
  password?: string;
}

export default function EditUserModal({ isOpen, onClose, onSubmit, user }: Props) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormInputs>();

  useEffect(() => {
    if (user) {
      reset({
        email: user.email,
        role: user.role,
        is_active: user.is_active,
      });
    }
  }, [user, reset]);

  const handleClose = () => {
    reset();
    onClose();
  };

  const onSubmitForm = async (data: FormInputs) => {
    // Only include password if it was changed
    const submitData = { ...data };
    if (!submitData.password) {
      delete submitData.password;
    }
    await onSubmit(submitData);
    handleClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose}>
      <ModalOverlay />
      <ModalContent>
        <form onSubmit={handleSubmit(onSubmitForm)}>
          <ModalHeader>Edit User: {user?.username}</ModalHeader>
          <ModalCloseButton />

          <ModalBody>
            <VStack spacing={4}>
              <FormControl isInvalid={!!errors.email} isRequired>
                <FormLabel>Email</FormLabel>
                <Input
                  type="email"
                  {...register('email', {
                    required: 'Email is required',
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: 'Invalid email address',
                    },
                  })}
                />
                <FormErrorMessage>
                  {errors.email && errors.email.message}
                </FormErrorMessage>
              </FormControl>

              <FormControl>
                <FormLabel>New Password (optional)</FormLabel>
                <Input
                  type="password"
                  {...register('password', {
                    minLength: { value: 6, message: 'Minimum length should be 6' },
                  })}
                  placeholder="Leave blank to keep current password"
                />
                <FormErrorMessage>
                  {errors.password && errors.password.message}
                </FormErrorMessage>
              </FormControl>

              <FormControl isInvalid={!!errors.role} isRequired>
                <FormLabel>Role</FormLabel>
                <Select {...register('role')}>
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </Select>
                <FormErrorMessage>
                  {errors.role && errors.role.message}
                </FormErrorMessage>
              </FormControl>

              <FormControl>
                <FormLabel>Active</FormLabel>
                <Switch {...register('is_active')} />
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
              Update User
            </Button>
          </ModalFooter>
        </form>
      </ModalContent>
    </Modal>
  );
} 