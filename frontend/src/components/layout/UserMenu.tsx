import React, { memo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Button,
  Avatar,
  Text,
  HStack,
  Divider,
  useColorModeValue,
} from '@chakra-ui/react';
import { ChevronDownIcon } from '@chakra-ui/icons';
import { useAuth } from '../../contexts/AuthContext';
import type { User } from '../../types/auth';

const UserMenu: React.FC = memo(() => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const menuBg = useColorModeValue('white', 'gray.800');

  if (!user) return null;

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  return (
    <Menu>
      <MenuButton
        as={Button}
        variant="ghost"
        rightIcon={<ChevronDownIcon />}
      >
        <HStack>
          <Avatar
            size="sm"
            name={user.name || user.username}
            src={user.avatar}
          />
          <Text>{user.name || user.username}</Text>
        </HStack>
      </MenuButton>
      <MenuList bg={menuBg}>
        <MenuItem onClick={() => handleNavigation('/profile')}>
          Profile
        </MenuItem>
        <MenuItem onClick={() => handleNavigation('/settings')}>
          Settings
        </MenuItem>
        <Divider />
        <MenuItem onClick={logout}>
          Logout
        </MenuItem>
      </MenuList>
    </Menu>
  );
});

UserMenu.displayName = 'UserMenu';

export default UserMenu; 