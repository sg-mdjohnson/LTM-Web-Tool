import React, { memo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Flex, Icon, Text, useColorModeValue } from '@chakra-ui/react';
import { IconType } from 'react-icons';

interface NavItemProps {
  icon: IconType;
  to: string;
  label: string;
  children: React.ReactNode;
}

const NavItem: React.FC<NavItemProps> = memo(({ icon, to, children }) => {
  const location = useLocation();
  const isActive = location.pathname.startsWith(to);
  const activeColor = useColorModeValue('brand.500', 'brand.200');
  const hoverBg = useColorModeValue('gray.100', 'gray.700');

  return (
    <Link to={to}>
      <Flex
        align="center"
        p="4"
        mx="4"
        borderRadius="lg"
        role="group"
        cursor="pointer"
        color={isActive ? activeColor : undefined}
        bg={isActive ? useColorModeValue('gray.100', 'gray.700') : undefined}
        _hover={{
          bg: hoverBg,
        }}
      >
        <Icon
          mr="4"
          fontSize="16"
          as={icon}
          aria-hidden="true"
        />
        <Text>{children}</Text>
      </Flex>
    </Link>
  );
});

NavItem.displayName = 'NavItem';

export default NavItem; 