import React, { useState } from 'react';
import {
  VStack,
  FormControl,
  FormLabel,
  Input,
  Button,
  Box,
  Text,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Spinner,
  Badge
} from '@chakra-ui/react';
import { useDNSPropagation } from '../../hooks/useDNSPropagation';

interface DNSPropagationProps {
  onError: (error: string) => void;
}

export const DNSPropagation: React.FC<DNSPropagationProps> = ({ onError }) => {
  const [domain, setDomain] = useState('');
  const { checkPropagation, loading, results } = useDNSPropagation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await checkPropagation(domain);
    } catch (error) {
      onError(error.message);
    }
  };

  return (
    <VStack spacing={4} align="stretch">
      <form onSubmit={handleSubmit}>
        <VStack spacing={4}>
          <FormControl isRequired>
            <FormLabel>Domain Name</FormLabel>
            <Input
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="example.com"
            />
          </FormControl>

          <Button type="submit" colorScheme="blue" isLoading={loading}>
            Check Propagation
          </Button>
        </VStack>
      </form>

      {loading && <Spinner />}

      {results && (
        <Box mt={4}>
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Nameserver</Th>
                <Th>Status</Th>
                <Th>IP Address</Th>
                <Th>Response Time</Th>
              </Tr>
            </Thead>
            <Tbody>
              {results.map((result, index) => (
                <Tr key={index}>
                  <Td>{result.nameserver}</Td>
                  <Td>
                    <Badge
                      colorScheme={result.status === 'success' ? 'green' : 'red'}
                    >
                      {result.status}
                    </Badge>
                  </Td>
                  <Td>{result.ip}</Td>
                  <Td>{result.responseTime}ms</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      )}
    </VStack>
  );
}; 