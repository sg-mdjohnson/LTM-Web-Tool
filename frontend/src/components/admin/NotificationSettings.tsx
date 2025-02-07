import React from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Heading,
  VStack,
  FormControl,
  FormLabel,
  Input,
  Switch,
  Select,
  Button,
  useColorModeValue,
  HStack,
  Text,
  FormHelperText,
  Divider,
} from '@chakra-ui/react';

interface NotificationConfig {
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
}

interface Props {
  config: NotificationConfig;
  onChange: (config: NotificationConfig) => void;
  onTestEmail: () => Promise<void>;
}

export default function NotificationSettings({ config, onChange, onTestEmail }: Props) {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Card bg={bgColor} borderColor={borderColor}>
      <CardHeader>
        <Heading size="md">Email Notifications</Heading>
      </CardHeader>
      <CardBody>
        <VStack spacing={4} align="stretch">
          <FormControl display="flex" alignItems="center">
            <FormLabel mb="0">Enable Email Notifications</FormLabel>
            <Switch
              isChecked={config.email_notifications}
              onChange={(e) =>
                onChange({
                  ...config,
                  email_notifications: e.target.checked,
                })
              }
            />
          </FormControl>

          <FormControl>
            <FormLabel>Notification Email</FormLabel>
            <Input
              type="email"
              value={config.notification_email}
              onChange={(e) =>
                onChange({
                  ...config,
                  notification_email: e.target.value,
                })
              }
              isDisabled={!config.email_notifications}
              placeholder="admin@example.com"
            />
          </FormControl>

          <Divider />

          <Heading size="sm">SMTP Settings</Heading>

          <FormControl>
            <FormLabel>SMTP Server</FormLabel>
            <Input
              value={config.smtp_server}
              onChange={(e) =>
                onChange({
                  ...config,
                  smtp_server: e.target.value,
                })
              }
              isDisabled={!config.email_notifications}
              placeholder="smtp.example.com"
            />
          </FormControl>

          <FormControl>
            <FormLabel>SMTP Port</FormLabel>
            <Input
              type="number"
              value={config.smtp_port}
              onChange={(e) =>
                onChange({
                  ...config,
                  smtp_port: parseInt(e.target.value),
                })
              }
              isDisabled={!config.email_notifications}
            />
          </FormControl>

          <HStack spacing={4}>
            <FormControl flex={1}>
              <FormLabel>Username</FormLabel>
              <Input
                value={config.smtp_username}
                onChange={(e) =>
                  onChange({
                    ...config,
                    smtp_username: e.target.value,
                  })
                }
                isDisabled={!config.email_notifications}
              />
            </FormControl>

            <FormControl flex={1}>
              <FormLabel>Password</FormLabel>
              <Input
                type="password"
                value={config.smtp_password}
                onChange={(e) =>
                  onChange({
                    ...config,
                    smtp_password: e.target.value,
                  })
                }
                isDisabled={!config.email_notifications}
                placeholder="••••••••"
              />
            </FormControl>
          </HStack>

          <FormControl display="flex" alignItems="center">
            <FormLabel mb="0">Use TLS</FormLabel>
            <Switch
              isChecked={config.smtp_use_tls}
              onChange={(e) =>
                onChange({
                  ...config,
                  smtp_use_tls: e.target.checked,
                })
              }
              isDisabled={!config.email_notifications}
            />
          </FormControl>

          <Divider />

          <Heading size="sm">Notification Events</Heading>

          <VStack spacing={3} align="stretch">
            {Object.entries(config.notify_on).map(([key, value]) => (
              <FormControl key={key} display="flex" alignItems="center">
                <FormLabel mb="0">
                  {key.split('_').map(word => 
                    word.charAt(0).toUpperCase() + word.slice(1)
                  ).join(' ')}
                </FormLabel>
                <Switch
                  isChecked={value}
                  onChange={(e) =>
                    onChange({
                      ...config,
                      notify_on: {
                        ...config.notify_on,
                        [key]: e.target.checked,
                      },
                    })
                  }
                  isDisabled={!config.email_notifications}
                />
              </FormControl>
            ))}
          </VStack>

          <Button
            onClick={onTestEmail}
            isDisabled={!config.email_notifications}
            size="sm"
          >
            Send Test Email
          </Button>
        </VStack>
      </CardBody>
    </Card>
  );
} 