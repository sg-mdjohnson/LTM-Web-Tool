import React, { Component, ErrorInfo, ReactNode } from 'react';
import {
  Box,
  Button,
  Heading,
  Text,
  VStack,
  useColorModeValue,
} from '@chakra-ui/react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <Box
          p={8}
          maxW="xl"
          mx="auto"
          textAlign="center"
          bg={useColorModeValue('white', 'gray.800')}
          rounded="lg"
          shadow="base"
        >
          <VStack spacing={4}>
            <Heading size="lg">Something went wrong</Heading>
            <Text color="gray.500">
              {this.state.error?.message || 'An unexpected error occurred'}
            </Text>
            <Button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
            >
              Try again
            </Button>
          </VStack>
        </Box>
      );
    }

    return this.props.children;
  }
} 