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

// Separate functional component for error UI
function ErrorFallback({ error, resetErrorBoundary }: { 
  error: Error | null; 
  resetErrorBoundary: () => void;
}) {
  const bgColor = useColorModeValue('white', 'gray.800');
  
  return (
    <Box
      p={8}
      maxW="xl"
      mx="auto"
      textAlign="center"
      bg={bgColor}
      rounded="lg"
      shadow="base"
    >
      <VStack spacing={4}>
        <Heading size="lg">Something went wrong</Heading>
        <Text color="gray.500">
          {error?.message || 'An unexpected error occurred'}
        </Text>
        <Button onClick={resetErrorBoundary}>
          Try again
        </Button>
      </VStack>
    </Box>
  );
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

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <ErrorFallback 
          error={this.state.error} 
          resetErrorBoundary={this.handleReset}
        />
      );
    }

    return this.props.children;
  }
} 