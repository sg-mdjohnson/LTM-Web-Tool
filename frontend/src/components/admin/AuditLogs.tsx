import React from 'react';
import {
  Box,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  HStack,
  Select,
  Input,
  Button,
  IconButton,
  useToast,
  Text
} from '@chakra-ui/react';
import { SearchIcon, DownloadIcon } from '@chakra-ui/icons';
import { useAuditLogs } from '../../hooks/useAuditLogs';

export const AuditLogs: React.FC = () => {
  const { logs, loading, error, fetchLogs, downloadLogs } = useAuditLogs();
  const [filters, setFilters] = React.useState({
    action: '',
    user: '',
    dateFrom: '',
    dateTo: ''
  });

  const handleSearch = () => {
    fetchLogs(filters);
  };

  const handleDownload = async () => {
    try {
      await downloadLogs(filters);
    } catch (error) {
      console.error('Failed to download logs:', error);
    }
  };

  const getActionColor = (action: string) => {
    switch (action.toLowerCase()) {
      case 'create':
        return 'green';
      case 'update':
        return 'blue';
      case 'delete':
        return 'red';
      default:
        return 'gray';
    }
  };

  return (
    <Box>
      <HStack spacing={4} mb={4}>
        <Select
          placeholder="Action"
          value={filters.action}
          onChange={(e) => setFilters({ ...filters, action: e.target.value })}
        >
          <option value="create">Create</option>
          <option value="update">Update</option>
          <option value="delete">Delete</option>
          <option value="login">Login</option>
        </Select>

        <Input
          placeholder="User"
          value={filters.user}
          onChange={(e) => setFilters({ ...filters, user: e.target.value })}
        />

        <Input
          type="date"
          value={filters.dateFrom}
          onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
        />

        <Input
          type="date"
          value={filters.dateTo}
          onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
        />

        <Button
          leftIcon={<SearchIcon />}
          colorScheme="blue"
          onClick={handleSearch}
          isLoading={loading}
        >
          Search
        </Button>

        <IconButton
          aria-label="Download logs"
          icon={<DownloadIcon />}
          onClick={handleDownload}
        />
      </HStack>

      {error && (
        <Text color="red.500" mb={4}>
          {error}
        </Text>
      )}

      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>Timestamp</Th>
            <Th>User</Th>
            <Th>Action</Th>
            <Th>Resource</Th>
            <Th>Details</Th>
            <Th>IP Address</Th>
          </Tr>
        </Thead>
        <Tbody>
          {logs.map((log) => (
            <Tr key={log.id}>
              <Td>{new Date(log.timestamp).toLocaleString()}</Td>
              <Td>{log.username}</Td>
              <Td>
                <Badge colorScheme={getActionColor(log.action)}>
                  {log.action}
                </Badge>
              </Td>
              <Td>{log.resource}</Td>
              <Td>{log.details}</Td>
              <Td>{log.ipAddress}</Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </Box>
  );
}; 