import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Heading,
  VStack,
  Button,
  Text,
  HStack,
  Badge,
  useToast,
  Divider,
  Alert,
  AlertIcon,
  Progress,
  useColorModeValue,
} from '@chakra-ui/react';
import { RepeatIcon, DeleteIcon, SettingsIcon } from '@chakra-ui/icons';
import api from '../../utils/api';

interface MaintenanceTask {
  name: string;
  description: string;
  lastRun?: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  type: 'f5' | 'system' | 'database';
}

export default function MaintenanceTasks() {
  const [tasks, setTasks] = useState<Record<string, MaintenanceTask>>({
    verify_connections: {
      name: 'Verify F5 Connections',
      description: 'Test connectivity to all registered F5 devices',
      type: 'f5',
      status: 'idle',
    },
    sync_device_configs: {
      name: 'Sync Device Configurations',
      description: 'Synchronize and cache F5 device configurations',
      type: 'f5',
      status: 'idle',
    },
    cleanup_logs: {
      name: 'Clean Up Logs',
      description: 'Remove old logs based on retention policy',
      type: 'system',
      status: 'idle',
    },
    optimize_database: {
      name: 'Optimize Database',
      description: 'Optimize database performance and clean up old records',
      type: 'database',
      status: 'idle',
    },
    verify_ssl_certs: {
      name: 'Verify SSL Certificates',
      description: 'Check SSL certificate expiration on F5 devices',
      type: 'f5',
      status: 'idle',
    },
  });

  const [isRunning, setIsRunning] = useState(false);
  const toast = useToast();
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  const runTask = async (taskId: string) => {
    setTasks(prev => ({
      ...prev,
      [taskId]: { ...prev[taskId], status: 'running' },
    }));
    setIsRunning(true);

    try {
      const response = await api.post(`/api/admin/maintenance/${taskId}`);
      if (response.data.status === 'success') {
        setTasks(prev => ({
          ...prev,
          [taskId]: {
            ...prev[taskId],
            status: 'completed',
            lastRun: new Date().toISOString(),
          },
        }));
        toast({
          title: 'Success',
          description: `${tasks[taskId].name} completed successfully`,
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
      }
    } catch (error) {
      setTasks(prev => ({
        ...prev,
        [taskId]: { ...prev[taskId], status: 'failed' },
      }));
      toast({
        title: 'Error',
        description: `Failed to run ${tasks[taskId].name}`,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsRunning(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      idle: 'gray',
      running: 'blue',
      completed: 'green',
      failed: 'red',
    };
    return <Badge colorScheme={colors[status]}>{status.toUpperCase()}</Badge>;
  };

  const getTaskIcon = (type: string) => {
    switch (type) {
      case 'f5':
        return <SettingsIcon />;
      case 'system':
        return <RepeatIcon />;
      case 'database':
        return <DeleteIcon />;
      default:
        return null;
    }
  };

  return (
    <Card bg={bgColor} borderColor={borderColor}>
      <CardHeader>
        <Heading size="md">Maintenance Tasks</Heading>
      </CardHeader>
      <CardBody>
        <VStack spacing={4} align="stretch">
          {Object.entries(tasks).map(([taskId, task]) => (
            <VStack
              key={taskId}
              p={4}
              borderWidth={1}
              borderRadius="md"
              align="stretch"
              spacing={2}
            >
              <HStack justify="space-between">
                <HStack>
                  {getTaskIcon(task.type)}
                  <Text fontWeight="medium">{task.name}</Text>
                </HStack>
                {getStatusBadge(task.status)}
              </HStack>
              
              <Text fontSize="sm" color="gray.500">
                {task.description}
              </Text>
              
              {task.lastRun && (
                <Text fontSize="xs" color="gray.400">
                  Last run: {new Date(task.lastRun).toLocaleString()}
                </Text>
              )}

              {task.status === 'running' && (
                <Progress size="xs" isIndeterminate colorScheme="brand" />
              )}

              <Button
                size="sm"
                onClick={() => runTask(taskId)}
                isDisabled={isRunning}
                colorScheme={task.status === 'failed' ? 'red' : 'brand'}
                variant="outline"
              >
                Run Task
              </Button>
            </VStack>
          ))}

          <Divider />

          <Alert status="info" size="sm">
            <AlertIcon />
            Some tasks may take several minutes to complete. You can continue using
            the application while tasks are running.
          </Alert>
        </VStack>
      </CardBody>
    </Card>
  );
} 