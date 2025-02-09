import React, { useState } from 'react';
import {
  VStack,
  FormControl,
  FormLabel,
  Input,
  Select,
  Button,
  Box,
  Text,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Spinner
} from '@chakra-ui/react';
import { useDNSLookup } from '../../hooks/useDNSLookup';

interface DNSLookupProps {
  onError: (error: string) => void;
}

export const DNSLookup: React.FC<DNSLookupProps> = ({ onError }) => {
  const [domain, setDomain] = useState('');
  const [recordType, setRecordType] = useState('A');
  const { lookup, loading, results } = useDNSLookup();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await lookup(domain, recordType);
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

          <FormControl>
            <FormLabel>Record Type</FormLabel>
            <Select value={recordType} onChange={(e) => setRecordType(e.target.value)}>
              <option value="A">A</option>
              <option value="AAAA">AAAA</option>
              <option value="CNAME">CNAME</option>
              <option value="MX">MX</option>
              <option value="TXT">TXT</option>
              <option value="NS">NS</option>
            </Select>
          </FormControl>

          <Button type="submit" colorScheme="blue" isLoading={loading}>
            Lookup
          </Button>
        </VStack>
      </form>

      {loading && <Spinner />}

      {results && (
        <Box mt={4}>
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Type</Th>
                <Th>Value</Th>
                <Th>TTL</Th>
              </Tr>
            </Thead>
            <Tbody>
              {results.map((record, index) => (
                <Tr key={index}>
                  <Td>{record.type}</Td>
                  <Td>{record.value}</Td>
                  <Td>{record.ttl}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      )}
    </VStack>
  );
}; 