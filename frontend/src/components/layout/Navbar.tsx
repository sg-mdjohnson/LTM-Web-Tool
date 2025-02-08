import React from 'react';
import {
  Box,
  Flex,
  Button,
  useColorModeValue,
  Stack,
  useColorMode,
  Text,
} from '@chakra-ui/react';
import { MoonIcon, SunIcon } from '@chakra-ui/icons';
import { useAuth } from '../../contexts/AuthContext';
import UserMenu from './UserMenu';

export default function Navbar() {
  const { colorMode, toggleColorMode } = useColorMode();
  const { user } = useAuth();

  return (
    <Box
      px={4}
      bg={useColorModeValue('white', 'gray.800')}
      borderBottom={1}
      borderStyle={'solid'}
      borderColor={useColorModeValue('gray.200', 'gray.700')}
    >
      <Flex h={16} alignItems={'center'} justifyContent={'space-between'}>
        <Text fontSize="lg" fontWeight="bold">
          LTM Web Tool
        </Text>

        <Flex alignItems={'center'}>
          <Stack direction={'row'} spacing={7}>
            <Button onClick={toggleColorMode}>
              {colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
            </Button>
            {user && <UserMenu />}
          </Stack>
        </Flex>
      </Flex>
    </Box>
  );
} 