import React from 'react';
import {
  Box,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
} from '@chakra-ui/react';
import SystemStatus from './SystemStatus';
import ConfigBackupRestore from './ConfigBackupRestore';
import ConfigComparison from './ConfigComparison';
import UserManagement from './UserManagement';

export default function AdminPanel() {
  return (
    <Box>
      <Tabs isLazy>
        <TabList>
          <Tab>System Status</Tab>
          <Tab>Backup/Restore</Tab>
          <Tab>Config Comparison</Tab>
          <Tab>User Management</Tab>
        </TabList>

        <TabPanels>
          <TabPanel>
            <SystemStatus />
          </TabPanel>
          <TabPanel>
            <ConfigBackupRestore />
          </TabPanel>
          <TabPanel>
            <ConfigComparison />
          </TabPanel>
          <TabPanel>
            <UserManagement />
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
} 