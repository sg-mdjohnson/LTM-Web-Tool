import React from 'react';
import {
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Box,
  Button,
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';

interface Props {
  message: string;
  showHomeButton?: boolean;
}

export default function ErrorAlert({ message, showHomeButton = false }: Props) {
  const navigate = useNavigate();

  return (
    <Box my={4}>
      <Alert
        status="error"
        variant="subtle"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        textAlign="center"
        height="200px"
        borderRadius="md"
      >
        <AlertIcon boxSize="40px" mr={0} />
        <AlertTitle mt={4} mb={1} fontSize="lg">
          Error
        </AlertTitle>
        <AlertDescription maxWidth="sm">
          {message}
        </AlertDescription>
        {showHomeButton && (
          <Button
            onClick={() => navigate('/')}
            colorScheme="brand"
            size="sm"
            mt={4}
          >
            Return to Dashboard
          </Button>
        )}
      </Alert>
    </Box>
  );
} 