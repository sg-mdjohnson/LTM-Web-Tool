import React, { useEffect } from 'react';
import {
  VStack,
  Box,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Text,
  Button,
  Spinner
} from '@chakra-ui/react';
import { useDNSHistory } from '../../hooks/useDNSHistory';

interface DNSHistoryProps {
  onError: (error: string) => void;
}

export const DNSHistory: React.FC<DNSHistoryProps> = ({ onError }) => {
  const { history, loading, fetchHistory, clearHistory } = useDNSHistory();

  useEffect(() => {
    fetchHistory().catch(onError);
  }, [fetchHistory, onError]);

  return (
    <VStack spacing={4} align="stretch">
      <Box display="flex" justifyContent="flex-end">
        <Button
          colorScheme="red"
          variant="outline"
          onClick={() => clearHistory().catch(onError)}
        >
          Clear History
        </Button>
      </Box>

      {loading && <Spinner />}

      {history && history.length > 0 ? (
        <Table variant="simple">
          <Thead>
            <Tr>
              <Th>Timestamp</Th>
              <Th>Domain</Th>
              <Th>Type</Th>
              <Th>Result</Th>
            </Tr>
          </Thead>
          <Tbody>
            {history.map((entry, index) => (
              <Tr key={index}>
                <Td>{new Date(entry.timestamp).toLocaleString()}</Td>
                <Td>{entry.domain}</Td>
                <Td>{entry.type}</Td>
                <Td>{entry.result}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      ) : (
        <Text>No history available</Text>
      )}
    </VStack>
  );
}; 