import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Heading,
  VStack,
  HStack,
  Button,
  Text,
  Box,
  useColorModeValue,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  useToast,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Alert,
  AlertIcon,
  Progress,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  useDisclosure,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  Select,
} from '@chakra-ui/react';
import {
  DownloadIcon,
  RepeatIcon,
  ChevronDownIcon,
  DeleteIcon,
  InfoIcon,
  WarningIcon,
  CompareIcon,
} from '@chakra-ui/icons';
import api from '../../utils/api';
import BackupDiffViewer from './BackupDiffViewer';

interface BackupEntry {
  id: string;
  timestamp: string;
  type: 'manual' | 'scheduled';
  author: string;
  size: string;
  devices: string[];
  comment?: string;
  status: 'success' | 'partial' | 'failed';
  version: string;
}

interface RestoreOptions {
  backupId: string;
  selectedDevices: string[];
  dryRun: boolean;
  comment: string;
}

export default function ConfigBackupRestore() {
  const [backups, setBackups] = useState<BackupEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isBackingUp, setIsBackingUp] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedBackup, setSelectedBackup] = useState<BackupEntry | null>(null);
  const [restoreOptions, setRestoreOptions] = useState<RestoreOptions>({
    backupId: '',
    selectedDevices: [],
    dryRun: true,
    comment: '',
  });
  const [showDiffViewer, setShowDiffViewer] = useState(false);
  const [selectedBackupForDiff, setSelectedBackupForDiff] = useState<BackupEntry | null>(null);

  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    loadBackups();
  }, []);

  const loadBackups = async () => {
    try {
      const response = await api.get('/api/admin/backups');
      if (response.data.status === 'success') {
        setBackups(response.data.backups);
      }
    } catch (error) {
      setError('Failed to load backups');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackup = async () => {
    setIsBackingUp(true);
    try {
      const response = await api.post('/api/admin/backups/create', {
        type: 'manual',
        comment: 'Manual backup',
      });

      if (response.data.status === 'success') {
        toast({
          title: 'Success',
          description: 'Backup created successfully',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
        loadBackups();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create backup',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsBackingUp(false);
    }
  };

  const handleDownload = async (backup: BackupEntry) => {
    try {
      const response = await api.get(`/api/admin/backups/${backup.id}/download`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `backup-${backup.timestamp}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to download backup',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleDelete = async (backup: BackupEntry) => {
    try {
      await api.delete(`/api/admin/backups/${backup.id}`);
      toast({
        title: 'Success',
        description: 'Backup deleted successfully',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      loadBackups();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete backup',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleRestore = async () => {
    try {
      const response = await api.post('/api/admin/backups/restore', restoreOptions);
      
      if (response.data.status === 'success') {
        toast({
          title: 'Success',
          description: restoreOptions.dryRun ? 
            'Dry run completed successfully' : 
            'Configuration restored successfully',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
        onClose();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to restore configuration',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      success: 'green',
      partial: 'yellow',
      failed: 'red',
    };
    return <Badge colorScheme={colors[status]}>{status.toUpperCase()}</Badge>;
  };

  return (
    <Card bg={bgColor} borderColor={borderColor}>
      <CardHeader>
        <HStack justify="space-between">
          <Heading size="md">Configuration Backups</Heading>
          <Button
            leftIcon={<RepeatIcon />}
            onClick={handleBackup}
            isLoading={isBackingUp}
            colorScheme="brand"
          >
            Create Backup
          </Button>
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack spacing={4} align="stretch">
          {error && (
            <Alert status="error">
              <AlertIcon />
              {error}
            </Alert>
          )}

          <Table variant="simple" size="sm">
            <Thead>
              <Tr>
                <Th>Timestamp</Th>
                <Th>Type</Th>
                <Th>Author</Th>
                <Th>Size</Th>
                <Th>Status</Th>
                <Th>Version</Th>
                <Th>Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              {backups.map((backup) => (
                <Tr key={backup.id}>
                  <Td>
                    <VStack align="start" spacing={0}>
                      <Text>{new Date(backup.timestamp).toLocaleString()}</Text>
                      {backup.comment && (
                        <Text fontSize="xs" color="gray.500">
                          {backup.comment}
                        </Text>
                      )}
                    </VStack>
                  </Td>
                  <Td>
                    <Badge>{backup.type}</Badge>
                  </Td>
                  <Td>{backup.author}</Td>
                  <Td>{backup.size}</Td>
                  <Td>{getStatusBadge(backup.status)}</Td>
                  <Td>{backup.version}</Td>
                  <Td>
                    <HStack spacing={2}>
                      <IconButton
                        aria-label="Download backup"
                        icon={<DownloadIcon />}
                        size="sm"
                        onClick={() => handleDownload(backup)}
                      />
                      <Menu>
                        <MenuButton
                          as={IconButton}
                          icon={<ChevronDownIcon />}
                          size="sm"
                          variant="outline"
                        />
                        <MenuList>
                          <MenuItem
                            icon={<RepeatIcon />}
                            onClick={() => {
                              setSelectedBackup(backup);
                              setRestoreOptions({
                                backupId: backup.id,
                                selectedDevices: backup.devices,
                                dryRun: true,
                                comment: '',
                              });
                              onOpen();
                            }}
                          >
                            Restore
                          </MenuItem>
                          <MenuItem
                            icon={<CompareIcon />}
                            onClick={() => {
                              setSelectedBackupForDiff(backup);
                              setShowDiffViewer(true);
                            }}
                          >
                            Compare
                          </MenuItem>
                          <MenuItem
                            icon={<InfoIcon />}
                            onClick={() => {
                              // Show backup details
                            }}
                          >
                            View Details
                          </MenuItem>
                          <MenuItem
                            icon={<DeleteIcon />}
                            onClick={() => handleDelete(backup)}
                            color="red.500"
                          >
                            Delete
                          </MenuItem>
                        </MenuList>
                      </Menu>
                    </HStack>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>

          <Modal isOpen={isOpen} onClose={onClose} size="xl">
            <ModalOverlay />
            <ModalContent>
              <ModalHeader>Restore Configuration</ModalHeader>
              <ModalCloseButton />
              <ModalBody>
                <VStack spacing={4} align="stretch">
                  <Alert status="warning">
                    <AlertIcon />
                    <Text fontSize="sm">
                      Restoring a configuration will overwrite the current settings.
                      Consider running a dry run first to review the changes.
                    </Text>
                  </Alert>

                  <FormControl>
                    <FormLabel>Target Devices</FormLabel>
                    <Select
                      multiple
                      value={restoreOptions.selectedDevices}
                      onChange={(e) => {
                        const selected = Array.from(e.target.selectedOptions).map(
                          (option) => option.value
                        );
                        setRestoreOptions((prev) => ({
                          ...prev,
                          selectedDevices: selected,
                        }));
                      }}
                    >
                      {selectedBackup?.devices.map((device) => (
                        <option key={device} value={device}>
                          {device}
                        </option>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl>
                    <FormLabel>Comment</FormLabel>
                    <Textarea
                      value={restoreOptions.comment}
                      onChange={(e) =>
                        setRestoreOptions((prev) => ({
                          ...prev,
                          comment: e.target.value,
                        }))
                      }
                      placeholder="Add a comment about this restore operation"
                    />
                  </FormControl>

                  <FormControl display="flex" alignItems="center">
                    <FormLabel mb="0">Dry Run</FormLabel>
                    <Input
                      type="checkbox"
                      checked={restoreOptions.dryRun}
                      onChange={(e) =>
                        setRestoreOptions((prev) => ({
                          ...prev,
                          dryRun: e.target.checked,
                        }))
                      }
                    />
                  </FormControl>
                </VStack>
              </ModalBody>

              <ModalFooter>
                <Button variant="ghost" mr={3} onClick={onClose}>
                  Cancel
                </Button>
                <Button
                  colorScheme={restoreOptions.dryRun ? 'blue' : 'red'}
                  onClick={handleRestore}
                >
                  {restoreOptions.dryRun ? 'Run Dry Run' : 'Restore Configuration'}
                </Button>
              </ModalFooter>
            </ModalContent>
          </Modal>

          {selectedBackupForDiff && (
            <BackupDiffViewer
              isOpen={showDiffViewer}
              onClose={() => {
                setShowDiffViewer(false);
                setSelectedBackupForDiff(null);
              }}
              sourceBackup={selectedBackupForDiff}
              backups={backups}
            />
          )}
        </VStack>
      </CardBody>
    </Card>
  );
} 