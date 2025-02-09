import React, { memo } from 'react';
import {
  Box,
  VStack,
  Text,
  useColorModeValue,
} from '@chakra-ui/react';
import {
  FiServer,
  FiSettings,
  FiDatabase,
} from 'react-icons/fi';
import NavItem from './NavItem';

const Sidebar: React.FC = memo(() => {
  const bgColor = useColorModeValue('white', 'gray.800');

  return (
    <Box
      w="60"
      pos="fixed"
      h="100vh"
      bg={bgColor}
      borderRight="1px"
      borderRightColor={useColorModeValue('gray.200', 'gray.700')}
      overflowY="auto"
    >
      <VStack spacing={0} align="stretch">
        <Box p={5}>
          <Text fontSize="lg" fontWeight="bold">
            LTM Web Tool
          </Text>
        </Box>

        <NavItem icon={FiServer} to="/devices" label="Devices">
          Devices
        </NavItem>

        <NavItem icon={FiDatabase} to="/dns" label="DNS Tools">
          DNS Tools
        </NavItem>

        <NavItem icon={FiSettings} to="/admin" label="Admin">
          Admin
        </NavItem>
      </VStack>
    </Box>
  );
});

Sidebar.displayName = 'Sidebar';

export default Sidebar; 