import React from 'react';
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

export default function Sidebar() {
  const bgColor = useColorModeValue('white', 'gray.800');

  return (
    <Box
      w={{ base: 'full', md: 60 }}
      pos="fixed"
      h="full"
      bg={bgColor}
      borderRight="1px"
      borderRightColor={useColorModeValue('gray.200', 'gray.700')}
    >
      <VStack spacing={0} align="stretch">
        <Box p={5}>
          <Text fontSize="lg" fontWeight="bold">
            LTM Web Tool
          </Text>
        </Box>

        <NavItem icon={FiServer} to="/devices">
          Devices
        </NavItem>

        <NavItem icon={FiDatabase} to="/dns">
          DNS Tools
        </NavItem>

        <NavItem icon={FiSettings} to="/admin">
          Admin
        </NavItem>
      </VStack>
    </Box>
  );
} 