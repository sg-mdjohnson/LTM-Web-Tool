import React, { memo } from 'react';
import { Box, Flex, useColorModeValue } from '@chakra-ui/react';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = memo(({ children }) => {
  const bgColor = useColorModeValue('gray.50', 'gray.900');

  return (
    <Flex minH="100vh" bg={bgColor}>
      <Sidebar />
      <Box flex="1" ml={{ base: 0, md: 60 }}>
        <Navbar />
        <Box 
          p={8} 
          overflowY="auto"
          maxH="calc(100vh - 64px)" // 64px is navbar height
        >
          {children}
        </Box>
      </Box>
    </Flex>
  );
});

MainLayout.displayName = 'MainLayout';

export default MainLayout; 