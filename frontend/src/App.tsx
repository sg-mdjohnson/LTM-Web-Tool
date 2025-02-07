import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Box, Container } from '@chakra-ui/react';
import Navbar from './components/layout/Navbar';
import DNSTools from './components/dns/DNSTools';
import DeviceList from './components/devices/DeviceList';
import ConfigBackupRestore from './components/admin/ConfigBackupRestore';
import ConfigComparison from './components/admin/ConfigComparison';
import SystemStatus from './components/admin/SystemStatus';

function App() {
  return (
    <Router>
      <Box minH="100vh">
        <Navbar />
        <Container maxW="container.xl" py={4}>
          <Routes>
            <Route path="/" element={<DNSTools />} />
            <Route path="/dns" element={<DNSTools />} />
            <Route path="/devices" element={<DeviceList />} />
            <Route path="/config" element={<ConfigComparison />} />
            <Route path="/backup" element={<ConfigBackupRestore />} />
            <Route path="/admin" element={<SystemStatus />} />
          </Routes>
        </Container>
      </Box>
    </Router>
  );
}

export default App; 