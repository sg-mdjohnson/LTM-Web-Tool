import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  VStack,
  Input,
  Text,
  useColorModeValue,
  Flex,
  Select,
  Button,
  useToast,
  Code,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  IconButton,
  HStack,
  Heading,
} from '@chakra-ui/react';
import { StarIcon, ChevronUpIcon, ChevronDownIcon } from '@chakra-ui/icons';
import api from '../utils/api';
import CommandTemplates from '../components/cli/CommandTemplates';

interface CommandHistory {
  command: string;
  output: string;
  status: 'success' | 'error';
  timestamp: string;
}

interface Device {
  id: number;
  name: string;
  host: string;
}

export default function CLI() {
  const [command, setCommand] = useState('');
  const [history, setHistory] = useState<CommandHistory[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const historyEndRef = useRef<HTMLDivElement>(null);
  const toast = useToast();
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [commandFilter, setCommandFilter] = useState('all');

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    loadDevices();
    loadCommandHistory();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [history]);

  const loadDevices = async () => {
    try {
      const response = await api.get('/api/device/list');
      if (response.data.status === 'success') {
        setDevices(response.data.devices);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load devices',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const loadCommandHistory = async () => {
    try {
      const response = await api.get('/api/cli/history');
      if (response.data.status === 'success') {
        setHistory(response.data.history);
      }
    } catch (error) {
      console.error('Failed to load command history:', error);
    }
  };

  const scrollToBottom = () => {
    historyEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim() || !selectedDevice) return;

    setIsLoading(true);
    try {
      const response = await api.post('/api/cli/execute', {
        command: command.trim(),
        device_id: selectedDevice,
      });

      if (response.data.status === 'success') {
        setHistory(prev => [...prev, {
          command: command.trim(),
          output: response.data.output,
          status: 'success',
          timestamp: new Date().toISOString(),
        }]);
        setCommand('');
      }
    } catch (error) {
      toast({
        title: 'Command Failed',
        description: error instanceof Error ? error.message : 'Failed to execute command',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCommandSelect = (command: string) => {
    setCommand(command);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (historyIndex < history.length - 1) {
        const newIndex = historyIndex + 1;
        setHistoryIndex(newIndex);
        setCommand(history[history.length - 1 - newIndex].command);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex > -1) {
        const newIndex = historyIndex - 1;
        setHistoryIndex(newIndex);
        setCommand(newIndex === -1 ? '' : history[history.length - 1 - newIndex].command);
      }
    }
  };

  const toggleFavorite = (command: string) => {
    setFavorites(prev => {
      const isFavorite = prev.includes(command);
      if (isFavorite) {
        return prev.filter(cmd => cmd !== command);
      } else {
        return [...prev, command];
      }
    });
  };

  return (
    <VStack spacing={4} align="stretch" h="calc(100vh - 100px)">
      <Flex gap={2}>
        <Select
          placeholder="Select Device"
          value={selectedDevice}
          onChange={(e) => setSelectedDevice(e.target.value)}
        >
          {devices.map(device => (
            <option key={device.id} value={device.id}>
              {device.name} ({device.host})
            </option>
          ))}
        </Select>
        <Button
          onClick={loadDevices}
          size="md"
          colorScheme="brand"
          variant="outline"
        >
          Refresh
        </Button>
      </Flex>

      <Tabs>
        <TabList>
          <Tab>Terminal</Tab>
          <Tab>Common Commands</Tab>
          <Tab>Favorites</Tab>
        </TabList>

        <TabPanels>
          <TabPanel p={0} pt={4}>
            <Box
              flex={1}
              borderWidth={1}
              borderRadius="md"
              bg={bgColor}
              borderColor={borderColor}
              p={4}
              overflowY="auto"
              fontFamily="mono"
              minH="400px"
            >
              {history.map((entry, index) => (
                <Box key={index} mb={4}>
                  <HStack>
                    <Text color="green.500">$ {entry.command}</Text>
                    <IconButton
                      aria-label="Favorite command"
                      icon={<StarIcon />}
                      size="xs"
                      variant="ghost"
                      color={favorites.includes(entry.command) ? 'yellow.500' : 'gray.500'}
                      onClick={() => toggleFavorite(entry.command)}
                    />
                  </HStack>
                  <Code
                    display="block"
                    whiteSpace="pre-wrap"
                    p={2}
                    mt={1}
                    colorScheme={entry.status === 'success' ? 'green' : 'red'}
                  >
                    {entry.output}
                  </Code>
                </Box>
              ))}
              <div ref={historyEndRef} />
            </Box>

            <form onSubmit={handleSubmit} style={{ width: '100%', marginTop: '1rem' }}>
              <HStack>
                <Input
                  placeholder="Enter command (e.g., 'list ltm virtual')"
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  onKeyDown={handleKeyDown}
                  isDisabled={isLoading || !selectedDevice}
                  bg={bgColor}
                  borderColor={borderColor}
                  fontFamily="mono"
                />
                <IconButton
                  aria-label="Previous command"
                  icon={<ChevronUpIcon />}
                  isDisabled={historyIndex >= history.length - 1}
                  onClick={() => handleKeyDown({ key: 'ArrowUp', preventDefault: () => {} } as any)}
                />
                <IconButton
                  aria-label="Next command"
                  icon={<ChevronDownIcon />}
                  isDisabled={historyIndex <= -1}
                  onClick={() => handleKeyDown({ key: 'ArrowDown', preventDefault: () => {} } as any)}
                />
              </HStack>
            </form>
          </TabPanel>

          <TabPanel>
            <CommandTemplates onSelectCommand={handleCommandSelect} />
          </TabPanel>

          <TabPanel>
            <Box>
              <Heading size="md" mb={4}>Favorite Commands</Heading>
              <VStack align="stretch" spacing={2}>
                {favorites.map((cmd, index) => (
                  <HStack key={index}>
                    <Button
                      variant="outline"
                      size="sm"
                      flex={1}
                      justifyContent="flex-start"
                      onClick={() => handleCommandSelect(cmd)}
                    >
                      {cmd}
                    </Button>
                    <IconButton
                      aria-label="Remove from favorites"
                      icon={<StarIcon />}
                      size="sm"
                      colorScheme="yellow"
                      onClick={() => toggleFavorite(cmd)}
                    />
                  </HStack>
                ))}
              </VStack>
            </Box>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </VStack>
  );
} 