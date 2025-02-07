import React from 'react';
import {
  Box,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Heading,
  VStack,
} from '@chakra-ui/react';
import UserManagement from '../components/admin/UserManagement';
import SystemLogs from '../components/admin/SystemLogs';
import Settings from '../components/admin/Settings';

export default function Admin() {
  return (
    <VStack spacing={6} align="stretch">
      <Heading size="lg">Admin Dashboard</Heading>
      
      <Tabs variant="enclosed">
        <TabList>
          <Tab>Users</Tab>
          <Tab>System Logs</Tab>
          <Tab>Settings</Tab>
        </TabList>

        <TabPanels>
          <TabPanel>
            <UserManagement />
          </TabPanel>
          <TabPanel>
            <SystemLogs />
          </TabPanel>
          <TabPanel>
            <Settings />
          </TabPanel>
        </TabPanels>
      </Tabs>
    </VStack>
  );
} 