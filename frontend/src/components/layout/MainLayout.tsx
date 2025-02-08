import React from 'react';
import { Box, Flex, useColorModeValue } from '@chakra-ui/react';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

export default function MainLayout({ children }: { children: React.ReactNode }) {
  console.log('MainLayout rendering...');
  const bgColor = useColorModeValue('gray.50', 'gray.900');

  return (
    <Flex minH="100vh" bg={bgColor}>
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