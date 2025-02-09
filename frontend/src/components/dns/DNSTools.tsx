import React, { useState, useMemo, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  HStack,
  Input,
  Select,
  Text,
  VStack,
  useColorModeValue,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Spinner,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Tabs,
  TabList,
  TabPanels,
  TabPanel,
  Tab,
  Tooltip,
  InputGroup,
  InputLeftElement,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverBody,
  useToast
} from '@chakra-ui/react';
import { 
  TriangleDownIcon, 
  TriangleUpIcon, 
  SearchIcon, 
  DownloadIcon,
  TimeIcon,
  ChevronDownIcon,
  LockIcon,
  RepeatIcon,
} from '@chakra-ui/icons';
import api from '../../utils/api';
import { DNSResult, DNSRecord, DNSSECChain } from '../../types/dns';
import { ErrorBoundary } from 'react-error-boundary';
import { DNSLookup } from './DNSLookup';
import { DNSPropagation } from './DNSPropagation';
import { DNSHistory } from './DNSHistory';
import { DNSSettings } from './DNSSettings';

type SortField = 'name' | 'type' | 'ttl' | 'status';
type SortDirection = 'asc' | 'desc';

// Maximum number of history items to store
const MAX_HISTORY_ITEMS = 10;

interface HistoryItem {
  id: string;
  domain: string;
  recordType: string;
  dnsServer: string;
  timestamp: number;
  result?: DNSResult;
  isFavorite?: boolean;
}

// Add specific type for tab values
type TabValue = 'forward' | 'reverse';

// Add specific type for record types
type RecordType = 'A' | 'AAAA' | 'MX' | 'NS' | 'TXT' | 'CNAME';

interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetErrorBoundary }) => (
  <Box p={4} bg="red.100" color="red.900" borderRadius="lg">
    <Text fontWeight="bold">Something went wrong:</Text>
    <Text>{error.message}</Text>
    <Button onClick={resetErrorBoundary} mt={2}>Try again</Button>
  </Box>
);

// Add constants at the top
const INITIAL_STATE = {
  domain: '',
  recordType: 'A' as RecordType,
  dnsServer: '',
  result: null as DNSResult | null,
  error: null as string | null,
};

interface DNSResultsTableProps {
  result: DNSResult | null;
  isLoading: boolean;
  filter: string;
  setFilter: (value: string) => void;
  sortField: SortField;
  sortDirection: SortDirection;
  handleSort: (field: SortField) => void;
  filteredAndSortedRecords: DNSRecord[];
  exportToCSV: () => void;
  exportToJSON: () => void;
}

const DNSResultsTable: React.FC<DNSResultsTableProps> = ({
  result,
  isLoading,
  filter,
  setFilter,
  sortField,
  sortDirection,
  handleSort,
  filteredAndSortedRecords,
  exportToCSV,
  exportToJSON,
}) => {
  const tableBgColor = useColorModeValue('white', 'gray.800');
  
  return (
    <Box p={4} bg={tableBgColor} borderRadius="lg" overflowX="auto">
      <HStack mb={4} spacing={4} justify="space-between">
        <HStack spacing={4}>
          <InputGroup>
            <InputLeftElement>
              <SearchIcon color="gray.500" />
            </InputLeftElement>
            <Input
              placeholder="Filter results..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              width="300px"
            />
          </InputGroup>
          <Text fontSize="sm" color="gray.500">
            {filteredAndSortedRecords.length} results found
          </Text>
        </HStack>
        
        <Menu>
          <MenuButton as={Button} rightIcon={<ChevronDownIcon />}>
            Export
          </MenuButton>
          <MenuList>
            <MenuItem 
              onClick={exportToCSV} 
              isDisabled={isLoading}
            >
              Export to CSV
            </MenuItem>
            <MenuItem 
              onClick={exportToJSON} 
              isDisabled={isLoading}
            >
              Export to JSON
            </MenuItem>
          </MenuList>
        </Menu>
      </HStack>

      {result?.dnssec && (
        <Tooltip
          label={`DNSSEC: ${result.dnssec.secure ? 'Secure' : 'Not Secure'}`}
        >
          <IconButton
            aria-label="DNSSEC Status"
            icon={<LockIcon />}
            variant="ghost"
            colorScheme={result.dnssec.secure ? 'green' : 'red'}
            size="sm"
          />
        </Tooltip>
      )}

      <Table variant="simple">
        <Thead>
          <Tr>
            <Th cursor="pointer" onClick={() => handleSort('name')}>
              <HStack spacing={2}>
                <Text>Domain</Text>
                {sortField === 'name' && (
                  sortDirection === 'asc' ? <TriangleUpIcon /> : <TriangleDownIcon />
                )}
              </HStack>
            </Th>
            <Th cursor="pointer" onClick={() => handleSort('type')}>
              <HStack spacing={2}>
                <Text>Type</Text>
                {sortField === 'type' && (
                  sortDirection === 'asc' ? <TriangleUpIcon /> : <TriangleDownIcon />
                )}
              </HStack>
            </Th>
            <Th cursor="pointer" onClick={() => handleSort('ttl')}>
              <HStack spacing={2}>
                <Text>TTL</Text>
                {sortField === 'ttl' && (
                  sortDirection === 'asc' ? <TriangleUpIcon /> : <TriangleDownIcon />
                )}
              </HStack>
            </Th>
            <Th>Data</Th>
            <Th cursor="pointer" onClick={() => handleSort('status')}>
              <HStack spacing={2}>
                <Text>Status</Text>
                {sortField === 'status' && (
                  sortDirection === 'asc' ? <TriangleUpIcon /> : <TriangleDownIcon />
                )}
              </HStack>
            </Th>
          </Tr>
        </Thead>
        <Tbody>
          {filteredAndSortedRecords.map((record, index) => (
            <Tr key={index}>
              <Td>{record.name}</Td>
              <Td>{record.type}</Td>
              <Td>{record.ttl}</Td>
              <Td>
                <VStack align="start" spacing={1}>
                  {record.data.map((value, i) => (
                    <Text key={i}>{value}</Text>
                  ))}
                </VStack>
              </Td>
              <Td>
                <Badge
                  colorScheme={record.status === 'success' ? 'green' : 'red'}
                >
                  {record.status}
                </Badge>
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </Box>
  );
};

export const DNSTools: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const toast = useToast();

  const handleError = (error: string) => {
    toast({
      title: 'Error',
      description: error,
      status: 'error',
      duration: 5000,
      isClosable: true,
    });
  };

  return (
    <Box p={4}>
      <Tabs index={activeTab} onChange={setActiveTab}>
        <TabList>
          <Tab>DNS Lookup</Tab>
          <Tab>Propagation Check</Tab>
          <Tab>History</Tab>
          <Tab>Settings</Tab>
        </TabList>

        <TabPanels>
          <TabPanel>
            <DNSLookup onError={handleError} />
          </TabPanel>
          <TabPanel>
            <DNSPropagation onError={handleError} />
          </TabPanel>
          <TabPanel>
            <DNSHistory onError={handleError} />
          </TabPanel>
          <TabPanel>
            <DNSSettings onError={handleError} />
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
};