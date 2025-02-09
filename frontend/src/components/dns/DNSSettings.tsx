import React, { useState, useEffect } from 'react';
import {
  VStack,
  FormControl,
  FormLabel,
  Input,
  Switch,
  Button,
  useToast,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper
} from '@chakra-ui/react';
import { useDNSSettings } from '../../hooks/useDNSSettings';

interface DNSSettingsProps {
  onError: (error: string) => void;
}

export const DNSSettings: React.FC<DNSSettingsProps> = ({ onError }) => {
  const { settings, loading, saveSettings } = useDNSSettings();
  const [formData, setFormData] = useState({
    timeout: 5,
    retries: 3,
    cacheEnabled: true,
    cacheDuration: 300,
    preferredNameservers: '',
  });

  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await saveSettings(formData);
    } catch (error) {
      onError(error.message);
    }
  };

  return (
    <VStack spacing={4} align="stretch">
      <form onSubmit={handleSubmit}>
        <VStack spacing={4}>
          <FormControl>
            <FormLabel>Timeout (seconds)</FormLabel>
            <NumberInput
              value={formData.timeout}
              onChange={(_, value) => 
                setFormData(prev => ({ ...prev, timeout: value }))
              }
              min={1}
              max={30}
            >
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>

          <FormControl>
            <FormLabel>Retries</FormLabel>
            <NumberInput
              value={formData.retries}
              onChange={(_, value) => 
                setFormData(prev => ({ ...prev, retries: value }))
              }
              min={0}
              max={5}
            >
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>

          <FormControl>
            <FormLabel>Enable Cache</FormLabel>
            <Switch
              isChecked={formData.cacheEnabled}
              onChange={(e) =>
                setFormData(prev => ({ 
                  ...prev, 
                  cacheEnabled: e.target.checked 
                }))
              }
            />
          </FormControl>

          <FormControl>
            <FormLabel>Cache Duration (seconds)</FormLabel>
            <NumberInput
              value={formData.cacheDuration}
              onChange={(_, value) => 
                setFormData(prev => ({ ...prev, cacheDuration: value }))
              }
              min={60}
              max={3600}
            >
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>

          <FormControl>
            <FormLabel>Preferred Nameservers (comma-separated)</FormLabel>
            <Input
              value={formData.preferredNameservers}
              onChange={(e) =>
                setFormData(prev => ({ 
                  ...prev, 
                  preferredNameservers: e.target.value 
                }))
              }
              placeholder="8.8.8.8, 8.8.4.4"
            />
          </FormControl>

          <Button type="submit" colorScheme="blue" isLoading={loading}>
            Save Settings
          </Button>
        </VStack>
      </form>
    </VStack>
  );
}; 