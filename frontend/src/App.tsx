import React from 'react';
import { Box, Container } from '@chakra-ui/react';
import DNSTools from './components/dns/DNSTools';

function App() {
  return (
    <Container maxW="container.xl" py={4}>
      <Box>
        <DNSTools />
      </Box>
    </Container>
  );
}

export default App; 