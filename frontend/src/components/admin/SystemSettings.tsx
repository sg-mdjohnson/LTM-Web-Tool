import React from 'react';
import {
  Box,
  VStack,
  FormControl,
  FormLabel,
  Input,
  Switch,
  Button,
  useToast,
  Heading,
  Divider,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper
} from '@chakra-ui/react';
import { useSystemSettings } from '../../hooks/useSystemSettings';

export const SystemSettings: React.FC = () => {
  const { settings, loading, updateSettings } = useSystemSettings();
  const toast = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateSettings(settings);
      toast({
        title: 'Settings updated',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error updating settings',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  return (
    <Box>
      <form onSubmit={handleSubmit}>
        <VStack spacing={6} align="stretch">
          <Box>
            <Heading size="md" mb={4}>General Settings</Heading>
            <VStack spacing={4}>
              <FormControl>
                <FormLabel>Site Name</FormLabel>
                <Input
                  value={settings?.siteName}
                  onChange={(e) => updateSettings({ ...settings, siteName: e.target.value })}
                />
              </FormControl>

              <FormControl>
                <FormLabel>Admin Email</FormLabel>
                <Input
                  type="email"
                  value={settings?.adminEmail}
                  onChange={(e) => updateSettings({ ...settings, adminEmail: e.target.value })}
                />
              </FormControl>
            </VStack>
          </Box>

          <Divider />

          <Box>
            <Heading size="md" mb={4}>Security Settings</Heading>
            <VStack spacing={4}>
              <FormControl display="flex" alignItems="center">
                <FormLabel mb="0">Enable Two-Factor Authentication</FormLabel>
                <Switch
                  isChecked={settings?.twoFactorEnabled}
                  onChange={(e) => updateSettings({ 
                    ...settings, 
                    twoFactorEnabled: e.target.checked 
                  })}
                />
              </FormControl>

              <FormControl>
                <FormLabel>Session Timeout (minutes)</FormLabel>
                <NumberInput
                  value={settings?.sessionTimeout}
                  onChange={(_, value) => updateSettings({ 
                    ...settings, 
                    sessionTimeout: value 
                  })}
                  min={5}
                  max={120}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
              </FormControl>
            </VStack>
          </Box>

          <Divider />

          <Box>
            <Heading size="md" mb={4}>Backup Settings</Heading>
            <VStack spacing={4}>
              <FormControl display="flex" alignItems="center">
                <FormLabel mb="0">Enable Automatic Backups</FormLabel>
                <Switch
                  isChecked={settings?.autoBackupEnabled}
                  onChange={(e) => updateSettings({ 
                    ...settings, 
                    autoBackupEnabled: e.target.checked 
                  })}
                />
              </FormControl>

              <FormControl>
                <FormLabel>Backup Retention Days</FormLabel>
                <NumberInput
                  value={settings?.backupRetentionDays}
                  onChange={(_, value) => updateSettings({ 
                    ...settings, 
                    backupRetentionDays: value 
                  })}
                  min={1}
                  max={90}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
              </FormControl>
            </VStack>
          </Box>

          <Button
            type="submit"
            colorScheme="blue"
            isLoading={loading}
            alignSelf="flex-end"
          >
            Save Settings
          </Button>
        </VStack>
      </form>
    </Box>
  );
}; 