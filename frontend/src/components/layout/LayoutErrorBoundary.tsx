import React from 'react';
import { Box, Button, Text, VStack } from '@chakra-ui/react';
import { ErrorBoundary } from 'react-error-boundary';

const ErrorFallback = ({ error, resetErrorBoundary }) => (
  <Box p={8}>
    <VStack spacing={4}>
      <Text>Something went wrong with the layout:</Text>
      <Text color="red.500">{error.message}</Text>
      <Button onClick={resetErrorBoundary}>Try again</Button>
    </VStack>
  </Box>
);

export const LayoutErrorBoundary: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ErrorBoundary FallbackComponent={ErrorFallback}>
    {children}
  </ErrorBoundary>
); 