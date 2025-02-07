import React from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Heading,
  VStack,
  FormControl,
  FormLabel,
  Select,
  Switch,
  HStack,
  Text,
  useColorModeValue,
} from '@chakra-ui/react';

interface BackupConfig {
  enabled: boolean;
  frequency: 'daily' | 'weekly' | 'monthly';
  time: string;
  retention_days: number;
}

interface Props {
  config: BackupConfig;
  onChange: (config: BackupConfig) => void;
}

export default function BackupSchedule({ config, onChange }: Props) {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Card bg={bgColor} borderColor={borderColor}>
      <CardHeader>
        <Heading size="md">Backup Schedule</Heading>
      </CardHeader>
      <CardBody>
        <VStack spacing={4} align="stretch">
          <FormControl display="flex" alignItems="center">
            <FormLabel mb="0">Enable Automatic Backups</FormLabel>
            <Switch
              isChecked={config.enabled}
              onChange={(e) =>
                onChange({ ...config, enabled: e.target.checked })
              }
            />
          </FormControl>

          <FormControl>
            <FormLabel>Backup Frequency</FormLabel>
            <Select
              value={config.frequency}
              onChange={(e) =>
                onChange({
                  ...config,
                  frequency: e.target.value as BackupConfig['frequency'],
                })
              }
              isDisabled={!config.enabled}
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </Select>
          </FormControl>

          <FormControl>
            <FormLabel>Backup Time</FormLabel>
            <Select
              value={config.time}
              onChange={(e) =>
                onChange({ ...config, time: e.target.value })
              }
              isDisabled={!config.enabled}
            >
              {Array.from({ length: 24 }).map((_, i) => (
                <option key={i} value={`${i.toString().padStart(2, '0')}:00`}>
                  {`${i.toString().padStart(2, '0')}:00`}
                </option>
              ))}
            </Select>
          </FormControl>

          <FormControl>
            <FormLabel>Retention Period (days)</FormLabel>
            <Select
              value={config.retention_days}
              onChange={(e) =>
                onChange({
                  ...config,
                  retention_days: parseInt(e.target.value),
                })
              }
              isDisabled={!config.enabled}
            >
              <option value={7}>7 days</option>
              <option value={14}>14 days</option>
              <option value={30}>30 days</option>
              <option value={90}>90 days</option>
            </Select>
          </FormControl>

          {config.enabled && (
            <Text fontSize="sm" color="gray.500">
              Next backup scheduled for:{' '}
              {new Date().toLocaleString()} ({config.frequency})
            </Text>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
} 