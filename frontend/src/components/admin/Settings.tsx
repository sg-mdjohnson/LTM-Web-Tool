import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  Heading,
  FormControl,
  FormLabel,
  Input,
  Switch,
  Button,
  useToast,
  Divider,
  HStack,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Card,
  CardHeader,
  CardBody,
  Text,
  useColorModeValue,
  Select,
} from '@chakra-ui/react';
import { DownloadIcon, RepeatIcon, WarningIcon } from '@chakra-ui/icons';
import api from '../../utils/api';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorAlert from '../common/ErrorAlert';
import RestoreBackupModal from './RestoreBackupModal';
import SystemStatus from './SystemStatus';
import BackupSchedule from './BackupSchedule';
import SystemHealth from './SystemHealth';
import NotificationSettings from './NotificationSettings';
import MaintenanceTasks from './MaintenanceTasks';
import F5DeviceStatus from './F5DeviceStatus';
import ConfigComparison from './ConfigComparison';

interface SystemSettings {
  session_timeout: number;
  max_login_attempts: number;
  password_expiry_days: number;
  enable_audit_logging: boolean;
  cli_timeout: number;
  backup_retention_days: number;
  log_retention_days: number;
  default_theme: 'light' | 'dark';
  maintenance_mode: boolean;
  backup_config: {
    enabled: boolean;
    frequency: 'daily' | 'weekly' | 'monthly';
    time: string;
    retention_days: number;
  };
  notification_config: {
    email_notifications: boolean;
    notification_email: string;
    smtp_server: string;
    smtp_port: number;
    smtp_username: string;
    smtp_password: string;
    smtp_use_tls: boolean;
    notify_on: {
      backup_complete: boolean;
      backup_failed: boolean;
      system_warnings: boolean;
      system_errors: boolean;
      login_failures: boolean;
    };
  };
}

interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  uptime: string;
  active_users: number;
  active_sessions: number;
  last_backup: string;
  database_size: string;
}

interface HealthCheck {
  name: string;
  status: 'healthy' | 'warning' | 'error';
  message: string;
  lastCheck: string;
  details?: string;
}

export default function Settings() {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();
  const [isRestoreModalOpen, setIsRestoreModalOpen] = useState(false);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [healthChecks, setHealthChecks] = useState<HealthCheck[]>([]);
  const [isHealthRefreshing, setIsHealthRefreshing] = useState(false);

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    loadSettings();
    loadSystemMetrics();
    loadHealthChecks();
    
    const metricsInterval = setInterval(loadSystemMetrics, 30000);
    const healthInterval = setInterval(loadHealthChecks, 60000);

    return () => {
      clearInterval(metricsInterval);
      clearInterval(healthInterval);
    };
  }, []);

  const loadSettings = async () => {
    try {
      const response = await api.get('/api/admin/settings');
      if (response.data.status === 'success') {
        setSettings(response.data.settings);
      }
    } catch (error) {
      setError('Failed to load system settings');
    } finally {
      setIsLoading(false);
    }
  };

  const loadSystemMetrics = async () => {
    try {
      const response = await api.get('/api/admin/metrics');
      if (response.data.status === 'success') {
        setSystemMetrics(response.data.metrics);
      }
    } catch (error) {
      console.error('Failed to load system metrics:', error);
    }
  };

  const loadHealthChecks = async () => {
    setIsHealthRefreshing(true);
    try {
      const response = await api.get('/api/admin/health');
      if (response.data.status === 'success') {
        setHealthChecks(response.data.checks);
      }
    } catch (error) {
      console.error('Failed to load health checks:', error);
    } finally {
      setIsHealthRefreshing(false);
    }
  };

  const handleSave = async () => {
    if (!settings) return;

    setIsSaving(true);
    try {
      const response = await api.put('/api/admin/settings', settings);
      if (response.data.status === 'success') {
        toast({
          title: 'Success',
          description: 'Settings saved successfully',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to save settings',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleBackup = async () => {
    try {
      const response = await api.get('/api/admin/backup', {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `backup-${new Date().toISOString()}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create backup',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleTestEmail = async () => {
    try {
      await api.post('/api/admin/notifications/test');
      toast({
        title: 'Success',
        description: 'Test email sent successfully',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to send test email',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  if (isLoading) return <LoadingSpinner message="Loading settings..." />;
  if (error) return <ErrorAlert message={error} />;
  if (!settings) return null;

  return (
    <VStack spacing={6} align="stretch">
      {systemMetrics && <SystemStatus metrics={systemMetrics} />}
      
      <SystemHealth
        checks={healthChecks}
        onRefresh={loadHealthChecks}
        isRefreshing={isHealthRefreshing}
      />

      <F5DeviceStatus />

      <ConfigComparison />

      <Card bg={bgColor} borderColor={borderColor}>
        <CardHeader>
          <Heading size="md">Security Settings</Heading>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <FormControl>
              <FormLabel>Session Timeout (minutes)</FormLabel>
              <NumberInput
                value={settings.session_timeout}
                onChange={(_, value) =>
                  setSettings(prev => ({ ...prev!, session_timeout: value }))
                }
                min={5}
                max={1440}
              >
                <NumberInputField />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
            </FormControl>

            <FormControl>
              <FormLabel>Maximum Login Attempts</FormLabel>
              <NumberInput
                value={settings.max_login_attempts}
                onChange={(_, value) =>
                  setSettings(prev => ({ ...prev!, max_login_attempts: value }))
                }
                min={3}
                max={10}
              >
                <NumberInputField />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
            </FormControl>

            <FormControl>
              <FormLabel>Password Expiry (days)</FormLabel>
              <NumberInput
                value={settings.password_expiry_days}
                onChange={(_, value) =>
                  setSettings(prev => ({ ...prev!, password_expiry_days: value }))
                }
                min={0}
                max={365}
              >
                <NumberInputField />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
            </FormControl>
          </VStack>
        </CardBody>
      </Card>

      <Card bg={bgColor} borderColor={borderColor}>
        <CardHeader>
          <Heading size="md">System Settings</Heading>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <FormControl>
              <FormLabel>CLI Timeout (seconds)</FormLabel>
              <NumberInput
                value={settings.cli_timeout}
                onChange={(_, value) =>
                  setSettings(prev => ({ ...prev!, cli_timeout: value }))
                }
                min={30}
                max={300}
              >
                <NumberInputField />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
            </FormControl>

            <FormControl>
              <FormLabel>Default Theme</FormLabel>
              <Select
                value={settings.default_theme}
                onChange={(e) =>
                  setSettings(prev => ({
                    ...prev!,
                    default_theme: e.target.value as 'light' | 'dark',
                  }))
                }
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </Select>
            </FormControl>

            <FormControl display="flex" alignItems="center">
              <FormLabel mb="0">Enable Audit Logging</FormLabel>
              <Switch
                isChecked={settings.enable_audit_logging}
                onChange={(e) =>
                  setSettings(prev => ({
                    ...prev!,
                    enable_audit_logging: e.target.checked,
                  }))
                }
              />
            </FormControl>
          </VStack>
        </CardBody>
      </Card>

      <NotificationSettings
        config={settings.notification_config}
        onChange={(config) =>
          setSettings(prev => ({
            ...prev!,
            notification_config: config,
          }))
        }
        onTestEmail={handleTestEmail}
      />

      <Card bg={bgColor} borderColor={borderColor}>
        <CardHeader>
          <Heading size="md">Backup & Restore</Heading>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <HStack justify="space-between">
              <Box>
                <Text fontWeight="bold">Manual Backup</Text>
                <Text fontSize="sm" color="gray.500">
                  Download a backup of all system settings and data
                </Text>
              </Box>
              <HStack>
                <Button
                  leftIcon={<DownloadIcon />}
                  onClick={handleBackup}
                  colorScheme="brand"
                >
                  Download Backup
                </Button>
                <Button
                  leftIcon={<RepeatIcon />}
                  onClick={() => setIsRestoreModalOpen(true)}
                  variant="outline"
                >
                  Restore Backup
                </Button>
              </HStack>
            </HStack>

            <Divider />

            <BackupSchedule
              config={settings.backup_config}
              onChange={(config) =>
                setSettings(prev => ({
                  ...prev!,
                  backup_config: config,
                }))
              }
            />
          </VStack>
        </CardBody>
      </Card>

      <Card bg={bgColor} borderColor={borderColor}>
        <CardHeader>
          <Heading size="md">Maintenance</Heading>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <MaintenanceTasks />
            <Divider />
            <FormControl display="flex" alignItems="center">
              <Box flex="1">
                <FormLabel mb="0">Maintenance Mode</FormLabel>
                <Text fontSize="sm" color="gray.500">
                  Only administrators can access the system when enabled
                </Text>
              </Box>
              <Switch
                isChecked={settings.maintenance_mode}
                onChange={(e) =>
                  setSettings(prev => ({
                    ...prev!,
                    maintenance_mode: e.target.checked,
                  }))
                }
                colorScheme="red"
              />
            </FormControl>
          </VStack>
        </CardBody>
      </Card>

      <Button
        colorScheme="brand"
        size="lg"
        onClick={handleSave}
        isLoading={isSaving}
      >
        Save Settings
      </Button>

      <RestoreBackupModal
        isOpen={isRestoreModalOpen}
        onClose={() => setIsRestoreModalOpen(false)}
        onSuccess={loadSettings}
      />
    </VStack>
  );
} 