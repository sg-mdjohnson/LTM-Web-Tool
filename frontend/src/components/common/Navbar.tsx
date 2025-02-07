import React from 'react';
import {
  Box,
  Flex,
  Button,
  useColorMode,
  useColorModeValue,
  Stack,
  Heading,
} from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { MoonIcon, SunIcon } from '@chakra-ui/icons';

export default function Navbar() {
  const { colorMode, toggleColorMode } = useColorMode();
  const { user, logout, isAuthenticated } = useAuth();
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Box
      bg={bgColor}
      px={4}
      borderBottom={1}
      borderStyle={'solid'}
      borderColor={borderColor}
    >
      <Flex h={16} alignItems={'center'} justifyContent={'space-between'}>
        <Heading size="md" as={RouterLink} to="/">
          F5 LTM Tool
        </Heading>

        <Flex alignItems={'center'}>
          <Stack direction={'row'} spacing={7}>
            <Button onClick={toggleColorMode}>
              {colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
            </Button>

            {isAuthenticated ? (
              <>
                <Button as={RouterLink} to="/devices">
                  Devices
                </Button>
                <Button as={RouterLink} to="/cli">
                  CLI
                </Button>
                {user?.role === 'admin' && (
                  <Button as={RouterLink} to="/admin">
                    Admin
                  </Button>
                )}
                <Button onClick={() => logout()}>
                  Logout
                </Button>
              </>
            ) : (
              <Button as={RouterLink} to="/login">
                Login
              </Button>
            )}
          </Stack>
        </Flex>
      </Flex>
    </Box>
  );
} 