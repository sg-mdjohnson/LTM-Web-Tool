import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Heading,
  VStack,
  HStack,
  Text,
  Badge,
  Button,
  useToast,
  Tooltip,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  IconButton,
  useColorModeValue,
  Collapse,
  Box,
} from '@chakra-ui/react';
import { 
  RepeatIcon, 
  ChevronDownIcon, 
  ChevronUpIcon,
  WarningIcon,
  CheckCircleIcon,
} from '@chakra-ui/icons';
import api from '../../utils/api';

interface DeviceStatus {
  id: number;
  name: string;
  host: string;
  status: 'connected' | 'disconnected' | 'error';
  lastSync: string;
  version: string;
  platform: string;
  modules: {
    ltm: boolean;
    gtm: boolean;
    asm: boolean;
    apm: boolean;
  };
  metrics: {
    cpu_usage: number;
    memory_usage: number;
    connections: number;
    throughput: string;
  };
  error?: string;
}

export default function F5DeviceStatus() {
  const [devices, setDevices] = useState<DeviceStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedDevice, setExpandedDevice] = useState<number | null>(null);
  const toast = useToast();

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

  useEffect(() => {
    loadDeviceStatus();
    const interval = setInterval(loadDeviceStatus, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  const loadDeviceStatus = async () => {
    try {
      const response = await api.get('/api/admin/devices/status');
      if (response.data.status === 'success') {
        setDevices(response.data.devices);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load device status',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      connected: 'green',
      disconnected: 'yellow',
      error: 'red',
    };
    return <Badge colorScheme={colors[status]}>{status.toUpperCase()}</Badge>;
  };

  const getModuleBadge = (enabled: boolean) => (
    <Badge colorScheme={enabled ? 'green' : 'gray'}>
      {enabled ? 'ENABLED' : 'DISABLED'}
    </Badge>
  );

  const handleRefresh = () => {
    setIsLoading(true);
    loadDeviceStatus();
  };

  return (
    <Card bg={bgColor} borderColor={borderColor}>
      <CardHeader>
        <HStack justify="space-between">
          <Heading size="md">F5 Device Status</Heading>
          <Button
            leftIcon={<RepeatIcon />}
            onClick={handleRefresh}
            isLoading={isLoading}
            size="sm"
          >
            Refresh
          </Button>
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack spacing={4} align="stretch">
          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>Device</Th>
                <Th>Status</Th>
                <Th>Version</Th>
                <Th>CPU</Th>
                <Th>Memory</Th>
                <Th>Connections</Th>
                <Th>Last Sync</Th>
                <Th></Th>
              </Tr>
            </Thead>
            <Tbody>
              {devices.map((device) => (
                <React.Fragment key={device.id}>
                  <Tr
                    cursor="pointer"
                    _hover={{ bg: hoverBg }}
                    onClick={() => setExpandedDevice(
                      expandedDevice === device.id ? null : device.id
                    )}
                  >
                    <Td>
                      <VStack align="start" spacing={0}>
                        <Text fontWeight="medium">{device.name}</Text>
                        <Text fontSize="xs" color="gray.500">
                          {device.host}
                        </Text>
                      </VStack>
                    </Td>
                    <Td>{getStatusBadge(device.status)}</Td>
                    <Td>{device.version}</Td>
                    <Td>
                      <Tooltip label={`CPU Usage: ${device.metrics.cpu_usage}%`}>
                        <Text>{device.metrics.cpu_usage}%</Text>
                      </Tooltip>
                    </Td>
                    <Td>
                      <Tooltip label={`Memory Usage: ${device.metrics.memory_usage}%`}>
                        <Text>{device.metrics.memory_usage}%</Text>
                      </Tooltip>
                    </Td>
                    <Td>{device.metrics.connections.toLocaleString()}</Td>
                    <Td>{new Date(device.lastSync).toLocaleString()}</Td>
                    <Td>
                      <IconButton
                        aria-label="Toggle details"
                        icon={expandedDevice === device.id ? 
                          <ChevronUpIcon /> : <ChevronDownIcon />}
                        size="sm"
                        variant="ghost"
                      />
                    </Td>
                  </Tr>
                  <Tr>
                    <Td colSpan={8} p={0}>
                      <Collapse in={expandedDevice === device.id}>
                        <Box p={4} bg={hoverBg}>
                          <VStack align="stretch" spacing={3}>
                            <HStack justify="space-between">
                              <Text fontWeight="medium">Platform:</Text>
                              <Text>{device.platform}</Text>
                            </HStack>
                            <HStack justify="space-between">
                              <Text fontWeight="medium">Throughput:</Text>
                              <Text>{device.metrics.throughput}</Text>
                            </HStack>
                            <HStack justify="space-between">
                              <Text fontWeight="medium">Modules:</Text>
                              <HStack spacing={2}>
                                <Tooltip label="Local Traffic Manager">
                                  <Badge>LTM {getModuleBadge(device.modules.ltm)}</Badge>
                                </Tooltip>
                                <Tooltip label="Global Traffic Manager">
                                  <Badge>GTM {getModuleBadge(device.modules.gtm)}</Badge>
                                </Tooltip>
                                <Tooltip label="Application Security Manager">
                                  <Badge>ASM {getModuleBadge(device.modules.asm)}</Badge>
                                </Tooltip>
                                <Tooltip label="Access Policy Manager">
                                  <Badge>APM {getModuleBadge(device.modules.apm)}</Badge>
                                </Tooltip>
                              </HStack>
                            </HStack>
                            {device.error && (
                              <HStack color="red.500">
                                <WarningIcon />
                                <Text>{device.error}</Text>
                              </HStack>
                            )}
                          </VStack>
                        </Box>
                      </Collapse>
                    </Td>
                  </Tr>
                </React.Fragment>
              ))}
            </Tbody>
          </Table>
        </VStack>
      </CardBody>
    </Card>
  );
} 