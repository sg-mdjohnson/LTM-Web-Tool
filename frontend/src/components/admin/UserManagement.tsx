import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  useToast,
  IconButton,
  useDisclosure,
  HStack,
  Switch,
} from '@chakra-ui/react';
import { AddIcon, EditIcon, DeleteIcon } from '@chakra-ui/icons';
import api from '../../utils/api';
import LoadingSpinner from '../common/LoadingSpinner';
import AddUserModal from './AddUserModal';
import EditUserModal from './EditUserModal';
import { useApiError } from '../../utils/api';
import { useUsers } from '../../hooks/useUsers';
import { DeleteUserModal } from './DeleteUserModal';
import { User } from '../../types/auth';

export const UserManagement: React.FC = () => {
  const { users, loading, error } = useUsers();
  const addModal = useDisclosure();
  const [selectedUser, setSelectedUser] = React.useState<User | null>(null);
  const editModal = useDisclosure();
  const deleteModal = useDisclosure();
  const toast = useToast();
  const { handleError } = useApiError();

  const handleEdit = (user: User) => {
    setSelectedUser(user);
    editModal.onOpen();
  };

  const handleDelete = (user: User) => {
    setSelectedUser(user);
    deleteModal.onOpen();
  };

  const loadUsers = React.useCallback(async () => {
    try {
      const response = await api.get('/api/admin/users');
      if (response.data.status === 'success') {
        // Assuming the response data structure is similar to the previous implementation
        // and the users are stored in the same format
        // If the structure is different, you might need to adjust the code accordingly
        // or fetch the users from the new structure
        // For now, we'll use the existing users state
        // If you're using a different state for users, you'll need to update this line
        // to use the new state
        // setUsers(response.data.users);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: handleError(error),
        status: 'error',
        duration: 5000,
      });
    }
  }, [toast, handleError]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const handleAddUser = async (userData: Partial<User>) => {
    try {
      const response = await api.post('/api/admin/users', userData);
      if (response.data.status === 'success') {
        toast({
          title: 'Success',
          description: 'User added successfully',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
        loadUsers();
        addModal.onClose();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to add user',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleEditUser = async (userData: Partial<User>) => {
    if (!selectedUser) return;

    try {
      const response = await api.put(`/api/admin/users/${selectedUser.id}`, userData);
      if (response.data.status === 'success') {
        toast({
          title: 'Success',
          description: 'User updated successfully',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
        loadUsers();
        editModal.onClose();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update user',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleDeleteUser = async (userId: number) => {
    try {
      const response = await api.delete(`/api/admin/users/${userId}`);
      if (response.data.status === 'success') {
        toast({
          title: 'Success',
          description: 'User deleted successfully',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
        loadUsers();
        deleteModal.onClose();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete user',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const toggleUserStatus = async (userId: number, isActive: boolean) => {
    try {
      await api.put(`/api/admin/users/${userId}`, {
        is_active: isActive,
      });
      loadUsers();
      toast({
        title: 'Success',
        description: 'User status updated',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: handleError(error),
        status: 'error',
        duration: 5000,
      });
    }
  };

  if (loading) return <LoadingSpinner message="Loading users..." />;

  return (
    <Box>
      <Button
        leftIcon={<AddIcon />}
        colorScheme="blue"
        mb={4}
        onClick={addModal.onOpen}
      >
        Add User
      </Button>

      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>Username</Th>
            <Th>Email</Th>
            <Th>Role</Th>
            <Th>Status</Th>
            <Th>Last Login</Th>
            <Th>Actions</Th>
          </Tr>
        </Thead>
        <Tbody>
          {users?.map((user) => (
            <Tr key={user.id}>
              <Td>{user.username}</Td>
              <Td>{user.email}</Td>
              <Td>
                <Badge colorScheme={user.role === 'admin' ? 'red' : 'green'}>
                  {user.role}
                </Badge>
              </Td>
              <Td>
                <Badge colorScheme="green">Active</Badge>
              </Td>
              <Td>{user.lastLogin ? new Date(user.lastLogin).toLocaleString() : 'Never'}</Td>
              <Td>
                <HStack spacing={2}>
                  <IconButton
                    aria-label="Edit user"
                    icon={<EditIcon />}
                    size="sm"
                    onClick={() => handleEdit(user)}
                  />
                  <IconButton
                    aria-label="Delete user"
                    icon={<DeleteIcon />}
                    size="sm"
                    colorScheme="red"
                    onClick={() => handleDelete(user)}
                  />
                </HStack>
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>

      <AddUserModal
        isOpen={addModal.isOpen}
        onClose={addModal.onClose}
        onSubmit={handleAddUser}
      />
      
      {selectedUser && (
        <>
          <EditUserModal
            isOpen={editModal.isOpen}
            onClose={editModal.onClose}
            user={selectedUser}
            onSubmit={handleEditUser}
          />
          <DeleteUserModal
            isOpen={deleteModal.isOpen}
            onClose={deleteModal.onClose}
            user={selectedUser}
            onDelete={handleDeleteUser}
          />
        </>
      )}
    </Box>
  );
}; 