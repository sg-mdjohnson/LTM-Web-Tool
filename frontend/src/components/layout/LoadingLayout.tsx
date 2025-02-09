import React from 'react';
import { Box, Spinner, Center } from '@chakra-ui/react';

export const LoadingLayout = () => (
  <Box h="100vh">
    <Center h="full">
      <Spinner size="xl" />
    </Center>
  </Box>
); 