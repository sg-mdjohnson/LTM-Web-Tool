import React from 'react';
import {
  Box,
  VStack,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  IconButton,
  useToast,
  Text,
  Progress,
  HStack,
  Badge
} from '@chakra-ui/react';
import { DownloadIcon, DeleteIcon, RepeatIcon } from '@chakra-ui/icons';
import { useBackups } from '../../hooks/useBackups';

export const BackupRestore: React.FC = () => {
  const { 
    backups, 
    loading, 
    error, 
    createBackup, 
    downloadBackup, 
    restoreBackup, 
    deleteBackup 
  } = useBackups();
  const toast = useToast();

  const handleCreateBackup = async () => {
    try {
      await createBackup();
      toast({
        title: 'Backup created successfully',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Error creating backup',
        description: error.message,
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleRestore = async (backupId: string) => {
    if (window.confirm('Are you sure you want to restore this backup? This will override current data.')) {
      try {
        await restoreBackup(backupId);
        toast({
          title: 'System restored successfully',
          status: 'success',
          duration: 3000,
        });
      } catch (error) {
        toast({
          title: 'Error restoring backup',
          description: error.message,
          status: 'error',
          duration: 5000,
        });
      }
    }
  };

  return (
    <Box>
      <VStack spacing={4} align="stretch">
        <HStack justify="space-between">
          <Button
            leftIcon={<RepeatIcon />}
            colorScheme="blue"
            onClick={handleCreateBackup}
            isLoading={loading}
          >
            Create New Backup
          </Button>
        </HStack>

        {error && (
          <Text color="red.500">
            {error}
          </Text>
        )}

        <Table variant="simple">
          <Thead>
            <Tr>
              <Th>Timestamp</Th>
              <Th>Size</Th>
              <Th>Type</Th>
              <Th>Status</Th>
              <Th>Actions</Th>
            </Tr>
          </Thead>
          <Tbody>
            {backups.map((backup) => (
              <Tr key={backup.id}>
                <Td>{new Date(backup.timestamp).toLocaleString()}</Td>
                <Td>{backup.size}</Td>
                <Td>
                  <Badge colorScheme={backup.type === 'auto' ? 'green' : 'blue'}>
                    {backup.type}
                  </Badge>
                </Td>
                <Td>
                  <Badge colorScheme={backup.status === 'completed' ? 'green' : 'yellow'}>
                    {backup.status}
                  </Badge>
                </Td>
                <Td>
                  <HStack spacing={2}>
                    <IconButton
                      aria-label="Download backup"
                      icon={<DownloadIcon />}
                      size="sm"
                      onClick={() => downloadBackup(backup.id)}
                    />
                    <Button
                      size="sm"
                      colorScheme="blue"
                      onClick={() => handleRestore(backup.id)}
                    >
                      Restore
                    </Button>
                    <IconButton
                      aria-label="Delete backup"
                      icon={<DeleteIcon />}
                      size="sm"
                      colorScheme="red"
                      onClick={() => deleteBackup(backup.id)}
                    />
                  </HStack>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </VStack>
    </Box>
  );
}; 