import React from 'react';
import {
  Box,
  Heading,
  Text,
  Button,
  VStack,
  Container,
} from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';

export default function NotFound() {
  return (
    <Container maxW="xl" py={12}>
      <VStack spacing={6} textAlign="center">
        <Heading size="2xl">404</Heading>
        <Heading size="xl">Page Not Found</Heading>
        <Text>The page you're looking for doesn't exist or has been moved.</Text>
        <Button as={RouterLink} to="/" colorScheme="brand">
          Return Home
        </Button>
      </VStack>
    </Container>
  );
} 