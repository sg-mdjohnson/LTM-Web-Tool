import React from 'react';
import { ChakraProvider, Box } from '@chakra-ui/react';
import { BrowserRouter as Router } from 'react-router-dom';
import theme from './theme/theme';
import AppRoutes from './routes';
import Navbar from './components/common/Navbar';
import { AuthProvider } from './contexts/AuthContext';
import ErrorBoundary from './components/common/ErrorBoundary';

function App() {
  return (
    <ChakraProvider theme={theme}>
      <ErrorBoundary>
        <AuthProvider>
          <Router>
            <Box minH="100vh">
              <Navbar />
              <Box as="main" p={4}>
                <AppRoutes />
              </Box>
            </Box>
          </Router>
        </AuthProvider>
      </ErrorBoundary>
    </ChakraProvider>
  );
}

export default App; 