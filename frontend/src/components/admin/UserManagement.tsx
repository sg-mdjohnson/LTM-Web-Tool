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
import ErrorAlert from '../common/ErrorAlert';
import AddUserModal from './AddUserModal';
import EditUserModal from './EditUserModal';
import { useApiError } from '../../utils/api';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  last_login?: string;
}

export default function UserManagement() {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { isOpen: isAddOpen, onOpen: onAddOpen, onClose: onAddClose } = useDisclosure();
  const { isOpen: isEditOpen, onOpen: onEditOpen, onClose: onEditClose } = useDisclosure();
  const toast = useToast();
  const { handleError } = useApiError();

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await api.get('/api/admin/users');
      if (response.data.status === 'success') {
        setUsers(response.data.users);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: handleError(error),
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsLoading(false);
    }
  };

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
        onAddClose();
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
        onEditClose();
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

  if (isLoading) return <LoadingSpinner message="Loading users..." />;

  return (
    <Box>
      <Button
        leftIcon={<AddIcon />}
        colorScheme="brand"
        mb={4}
        onClick={onAddOpen}
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
          {users.map(user => (
            <Tr key={user.id}>
              <Td>{user.username}</Td>
              <Td>{user.email}</Td>
              <Td>
                <Badge colorScheme={user.role === 'admin' ? 'red' : 'green'}>
                  {user.role}
                </Badge>
              </Td>
              <Td>
                <Switch
                  isChecked={user.is_active}
                  onChange={() => toggleUserStatus(user.id, !user.is_active)}
                />
              </Td>
              <Td>{user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</Td>
              <Td>
                <HStack spacing={2}>
                  <IconButton
                    aria-label="Edit user"
                    icon={<EditIcon />}
                    size="sm"
                    onClick={() => {
                      setSelectedUser(user);
                      onEditOpen();
                    }}
                  />
                  <IconButton
                    aria-label="Delete user"
                    icon={<DeleteIcon />}
                    size="sm"
                    colorScheme="red"
                    onClick={() => handleDeleteUser(user.id)}
                  />
                </HStack>
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>

      <AddUserModal
        isOpen={isAddOpen}
        onClose={onAddClose}
        onSubmit={handleAddUser}
      />

      <EditUserModal
        isOpen={isEditOpen}
        onClose={onEditClose}
        onSubmit={handleEditUser}
        user={selectedUser}
      />
    </Box>
  );
} 