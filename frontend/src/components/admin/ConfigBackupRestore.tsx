import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  VStack,
  HStack,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  useToast,
  Badge,
  IconButton,
  useColorModeValue,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useDisclosure,
  FormControl,
  FormLabel,
  Input,
  Textarea,
} from '@chakra-ui/react';
import { DownloadIcon, RepeatIcon, DeleteIcon, AddIcon } from '@chakra-ui/icons';
import api from '../../utils/api';
import { useApiError } from '../../utils/api';
import LoadingSpinner from '../common/LoadingSpinner';

interface Backup {
  id: string;
  filename: string;
  timestamp: string;
  size: string;
  type: 'manual' | 'automatic';
  comment?: string;
  created_by: string;
  devices: string[];
}

export default function ConfigBackupRestore() {
  const [backups, setBackups] = useState<Backup[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [comment, setComment] = useState('');
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();
  const { handleError } = useApiError();
  const bgColor = useColorModeValue('white', 'gray.800');

  const fetchBackups = React.useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/api/admin/backups');
      setBackups(response.data.backups);
    } catch (error) {
      handleError(error);
    } finally {
      setIsLoading(false);
    }
  }, [handleError]);

  useEffect(() => {
    fetchBackups();
  }, [fetchBackups]);

  const handleCreateBackup = async () => {
    try {
      await api.post('/api/admin/backups', {
        comment,
        type: 'manual'
      });
      toast({
        title: 'Success',
        description: 'Backup created successfully',
        status: 'success',
        duration: 3000,
      });
      fetchBackups();
      onClose();
    } catch (error) {
      handleError(error);
    }
  };

  const handleRestore = async (backupId: string) => {
    try {
      await api.post(`/api/admin/backups/${backupId}/restore`);
      toast({
        title: 'Success',
        description: 'Configuration restored successfully',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      handleError(error);
    }
  };

  const handleDelete = async (backupId: string) => {
    try {
      await api.delete(`/api/admin/backups/${backupId}`);
      toast({
        title: 'Success',
        description: 'Backup deleted successfully',
        status: 'success',
        duration: 3000,
      });
      fetchBackups();
    } catch (error) {
      handleError(error);
    }
  };

  const handleDownload = async (backupId: string, filename: string) => {
    try {
      const response = await api.get(`/api/admin/backups/${backupId}/download`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      handleError(error);
    }
  };

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('comment', comment);

    try {
      await api.post('/api/admin/backups/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      toast({
        title: 'Success',
        description: 'Backup uploaded successfully',
        status: 'success',
        duration: 3000,
      });
      fetchBackups();
      onClose();
    } catch (error) {
      handleError(error);
    }
  };

  if (isLoading) return <LoadingSpinner message="Loading backups..." />;

  return (
    <Box bg={bgColor} p={4} borderRadius="lg" shadow="sm">
      <VStack spacing={4} align="stretch">
        <HStack justify="space-between">
          <Button
            leftIcon={<RepeatIcon />}
            onClick={fetchBackups}
          >
            Refresh
          </Button>
          <HStack>
            <Button
              leftIcon={<AddIcon />}
              onClick={onOpen}
            >
              Upload Backup
            </Button>
            <Button
              colorScheme="brand"
              onClick={onOpen}
            >
              Create Backup
            </Button>
          </HStack>
        </HStack>

        <Table variant="simple">
          <Thead>
            <Tr>
              <Th>Timestamp</Th>
              <Th>Filename</Th>
              <Th>Type</Th>
              <Th>Size</Th>
              <Th>Created By</Th>
              <Th>Comment</Th>
              <Th>Actions</Th>
            </Tr>
          </Thead>
          <Tbody>
            {backups.map((backup) => (
              <Tr key={backup.id}>
                <Td whiteSpace="nowrap">
                  {new Date(backup.timestamp).toLocaleString()}
                </Td>
                <Td>{backup.filename}</Td>
                <Td>
                  <Badge
                    colorScheme={backup.type === 'automatic' ? 'blue' : 'green'}
                  >
                    {backup.type}
                  </Badge>
                </Td>
                <Td>{backup.size}</Td>
                <Td>{backup.created_by}</Td>
                <Td>{backup.comment}</Td>
                <Td>
                  <HStack spacing={2}>
                    <IconButton
                      aria-label="Download backup"
                      icon={<DownloadIcon />}
                      size="sm"
                      onClick={() => handleDownload(backup.id, backup.filename)}
                    />
                    <Button
                      size="sm"
                      onClick={() => handleRestore(backup.id)}
                    >
                      Restore
                    </Button>
                    <IconButton
                      aria-label="Delete backup"
                      icon={<DeleteIcon />}
                      size="sm"
                      colorScheme="red"
                      onClick={() => handleDelete(backup.id)}
                    />
                  </HStack>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </VStack>

      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Create/Upload Backup</ModalHeader>
          <ModalBody>
            <VStack spacing={4}>
              <FormControl>
                <FormLabel>Upload Backup File (Optional)</FormLabel>
                <Input
                  type="file"
                  accept=".ucs,.tar.gz"
                  onChange={handleUpload}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Comment</FormLabel>
                <Textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Add a comment about this backup..."
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="brand"
              onClick={selectedFile ? handleUploadSubmit : handleCreateBackup}
            >
              {selectedFile ? 'Upload' : 'Create'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
} 