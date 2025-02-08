import React from 'react';
import {
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Button,
  useDisclosure,
} from '@chakra-ui/react';
import { ChevronDownIcon } from '@chakra-ui/icons';
import { useAuth } from '../../contexts/AuthContext';
import ChangePasswordModal from '../auth/ChangePasswordModal';

export default function UserMenu() {
  const { user, logout } = useAuth();
  const { isOpen, onOpen, onClose } = useDisclosure();

  return (
    <>
      <Menu>
        <MenuButton as={Button} rightIcon={<ChevronDownIcon />}>
          {user?.username}
        </MenuButton>
        <MenuList>
          <MenuItem onClick={onOpen}>Change Password</MenuItem>
          <MenuItem onClick={logout}>Logout</MenuItem>
        </MenuList>
      </Menu>

      <ChangePasswordModal isOpen={isOpen} onClose={onClose} />
    </>
  );
} 