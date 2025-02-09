import React, { memo } from 'react';
import {
  Box,
  Flex,
  Button,
  useColorModeValue,
  Stack,
  useColorMode,
  Text,
  Tooltip,
} from '@chakra-ui/react';
import { MoonIcon, SunIcon } from '@chakra-ui/icons';
import { useAuth } from '../../contexts/AuthContext';
import UserMenu from './UserMenu';

const Navbar: React.FC = memo(() => {
  const { colorMode, toggleColorMode } = useColorMode();
  const { user } = useAuth();

  return (
    <Box
      px={4}
      h="64px"
      position="sticky"
      top={0}
      zIndex={1}
      bg={useColorModeValue('white', 'gray.800')}
      borderBottom="1px"
      borderStyle="solid"
      borderColor={useColorModeValue('gray.200', 'gray.700')}
    >
      <Flex h="full" alignItems="center" justifyContent="space-between">
        <Text fontSize="lg" fontWeight="bold">
          LTM Web Tool
        </Text>

        <Flex alignItems="center">
          <Stack direction="row" spacing={7}>
            <Tooltip label={`Switch to ${colorMode === 'light' ? 'dark' : 'light'} mode`}>
              <Button onClick={toggleColorMode} aria-label="Toggle color mode">
                {colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
              </Button>
            </Tooltip>
            {user && <UserMenu />}
          </Stack>
        </Flex>
      </Flex>
    </Box>
  );
});

Navbar.displayName = 'Navbar';

export default Navbar; 