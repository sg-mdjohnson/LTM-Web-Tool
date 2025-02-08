import React from 'react';
import {
  Box,
  VStack,
  Link,
  useColorModeValue,
} from '@chakra-ui/react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const NavItem = ({ to, children }: { to: string; children: React.ReactNode }) => {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      as={RouterLink}
      to={to}
      w="full"
      p={3}
      borderRadius="md"
      bg={isActive ? 'brand.500' : 'transparent'}
      color={isActive ? 'white' : undefined}
      _hover={{
        bg: isActive ? 'brand.600' : useColorModeValue('gray.100', 'gray.700'),
      }}
    >
      {children}
    </Link>
  );
};

export default function Sidebar() {
  const { user } = useAuth();

  return (
    <Box
      w={60}
      bg={useColorModeValue('white', 'gray.800')}
      borderRight={1}
      borderStyle={'solid'}
      borderColor={useColorModeValue('gray.200', 'gray.700')}
      p={4}
    >
      <VStack spacing={2} align="stretch">
        <NavItem to="/devices">Devices</NavItem>
        <NavItem to="/dns">DNS Tools</NavItem>
        {user?.role === 'admin' && (
          <NavItem to="/admin">Admin</NavItem>
        )}
      </VStack>
    </Box>
  );
} 