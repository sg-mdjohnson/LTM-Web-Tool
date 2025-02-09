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
import { User } from '../../types/auth';
import { useUsers } from '../../hooks/useUsers';

interface DeleteUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: User;
}

export const DeleteUserModal: React.FC<DeleteUserModalProps> = ({ 
  isOpen, 
  onClose, 
  user 
}) => {
  const { deleteUser } = useUsers();
  const toast = useToast();
  const [isDeleting, setIsDeleting] = React.useState(false);

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await deleteUser(user.id);
      toast({
        title: 'User deleted successfully',
        status: 'success',
        duration: 3000,
      });
      onClose();
    } catch (error) {
      toast({
        title: 'Error deleting user',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Delete User</ModalHeader>
        <ModalBody>
          <Text>
            Are you sure you want to delete the user "{user.username}"? This action cannot be undone.
          </Text>
        </ModalBody>

        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            Cancel
          </Button>
          <Button
            colorScheme="red"
            onClick={handleDelete}
            isLoading={isDeleting}
          >
            Delete
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}; 