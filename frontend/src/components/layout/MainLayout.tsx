import React from 'react';
import { Box, Flex, useColorModeValue } from '@chakra-ui/react';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <Flex minH="100vh" bg={useColorModeValue('gray.50', 'gray.900')}>
      <Sidebar />
      <Box flex="1">
        <Navbar />
        <Box p={8}>
          {children}
        </Box>
      </Box>
    </Flex>
  );
} 