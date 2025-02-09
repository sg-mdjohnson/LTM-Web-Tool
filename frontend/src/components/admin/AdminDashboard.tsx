import React from 'react';
import {
  Box,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Heading,
  VStack
} from '@chakra-ui/react';
import { UserManagement } from './UserManagement';
import { SystemSettings } from './SystemSettings';
import { AuditLogs } from './AuditLogs';
import { BackupRestore } from './BackupRestore';

export const AdminDashboard: React.FC = () => {
  return (
    <Box p={4}>
      <VStack spacing={4} align="stretch">
        <Heading size="lg">Admin Dashboard</Heading>
        
        <Tabs variant="enclosed">
          <TabList>
            <Tab>Users</Tab>
            <Tab>System Settings</Tab>
            <Tab>Audit Logs</Tab>
            <Tab>Backup & Restore</Tab>
          </TabList>

          <TabPanels>
            <TabPanel>
              <UserManagement />
            </TabPanel>
            <TabPanel>
              <SystemSettings />
            </TabPanel>
            <TabPanel>
              <AuditLogs />
            </TabPanel>
            <TabPanel>
              <BackupRestore />
            </TabPanel>
          </TabPanels>
        </Tabs>
      </VStack>
    </Box>
  );
}; 