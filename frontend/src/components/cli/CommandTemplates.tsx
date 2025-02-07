import React from 'react';
import {
  Box,
  Button,
  SimpleGrid,
  useColorModeValue,
  Heading,
  Text,
} from '@chakra-ui/react';

interface CommandTemplate {
  name: string;
  command: string;
  description: string;
  category: string;
}

const COMMON_COMMANDS: CommandTemplate[] = [
  {
    name: 'List Virtual Servers',
    command: 'list ltm virtual',
    description: 'List all virtual servers',
    category: 'virtual',
  },
  {
    name: 'List Pools',
    command: 'list ltm pool',
    description: 'List all pools',
    category: 'pool',
  },
  {
    name: 'List Nodes',
    command: 'list ltm node',
    description: 'List all nodes',
    category: 'node',
  },
  {
    name: 'List Rules',
    command: 'list ltm rule',
    description: 'List all iRules',
    category: 'rule',
  },
  {
    name: 'List TCP Monitors',
    command: 'list ltm monitor tcp',
    description: 'List TCP monitors',
    category: 'monitor',
  },
  {
    name: 'List SSL Profiles',
    command: 'list ltm profile client-ssl',
    description: 'List SSL profiles',
    category: 'ssl',
  },
];

interface Props {
  onSelectCommand: (command: string) => void;
}

export default function CommandTemplates({ onSelectCommand }: Props) {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Box>
      <Heading size="md" mb={4}>Common Commands</Heading>
      <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
        {COMMON_COMMANDS.map((template, index) => (
          <Box
            key={index}
            p={4}
            bg={bgColor}
            borderWidth={1}
            borderRadius="md"
            borderColor={borderColor}
          >
            <Text fontWeight="bold" mb={2}>{template.name}</Text>
            <Text fontSize="sm" mb={3} color="gray.500">
              {template.description}
            </Text>
            <Button
              size="sm"
              width="full"
              onClick={() => onSelectCommand(template.command)}
            >
              Use Command
            </Button>
          </Box>
        ))}
      </SimpleGrid>
    </Box>
  );
} 