import React from 'react';
import {
  Box,
  Flex,
  HStack,
  Link,
  useColorModeValue,
  Heading,
  IconButton,
  useColorMode,
} from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import {
  SettingsIcon,
  ViewIcon,
  LockIcon,
  RepeatIcon,
  InfoIcon,
  MoonIcon,
  SunIcon,
  StarIcon,
} from '@chakra-ui/icons';

export default function Navbar() {
  const { colorMode, toggleColorMode } = useColorMode();
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const iconColor = useColorModeValue('gray.600', 'gray.300');

  return (
    <Box bg={bgColor} px={4} shadow="sm" borderBottom="1px" borderColor={borderColor}>
      <Flex h={16} alignItems="center" justifyContent="space-between">
        <HStack spacing={8} alignItems="center">
          <HStack spacing={2}>
            <InfoIcon boxSize="24px" color={iconColor} />
            <Heading size="md">LTM Web Tool</Heading>
          </HStack>
          <HStack as="nav" spacing={6}>
            <Link as={RouterLink} to="/dns" _hover={{ color: 'brand.400' }}>
              <HStack spacing={2}>
                <ViewIcon boxSize="18px" />
                <span>DNS Tools</span>
              </HStack>
            </Link>
            <Link as={RouterLink} to="/devices" _hover={{ color: 'brand.400' }}>
              <HStack spacing={2}>
                <RepeatIcon boxSize="18px" />
                <span>Devices</span>
              </HStack>
            </Link>
            <Link as={RouterLink} to="/config" _hover={{ color: 'brand.400' }}>
              <HStack spacing={2}>
                <SettingsIcon boxSize="18px" />
                <span>Configuration</span>
              </HStack>
            </Link>
            <Link as={RouterLink} to="/backup" _hover={{ color: 'brand.400' }}>
              <HStack spacing={2}>
                <StarIcon boxSize="18px" />
                <span>Backup/Restore</span>
              </HStack>
            </Link>
            <Link as={RouterLink} to="/admin" _hover={{ color: 'brand.400' }}>
              <HStack spacing={2}>
                <LockIcon boxSize="18px" />
                <span>Admin</span>
              </HStack>
            </Link>
          </HStack>
        </HStack>
        <IconButton
          aria-label="Toggle color mode"
          icon={colorMode === 'light' ? <MoonIcon boxSize="20px" /> : <SunIcon boxSize="20px" />}
          onClick={toggleColorMode}
          variant="ghost"
          _hover={{ bg: 'whiteAlpha.200' }}
        />
      </Flex>
    </Box>
  );
} 