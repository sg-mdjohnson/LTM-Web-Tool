import React, { useRef, useState } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  VStack,
  Text,
  Input,
  Progress,
  Alert,
  AlertIcon,
  useToast,
  Box,
} from '@chakra-ui/react';
import { WarningIcon } from '@chakra-ui/icons';
import api from '../../utils/api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function RestoreBackupModal({ isOpen, onClose, onSuccess }: Props) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const toast = useToast();

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.zip')) {
      toast({
        title: 'Invalid File',
        description: 'Please select a valid backup file (.zip)',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('backup', file);

    try {
      const response = await api.post('/api/admin/restore', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = (progressEvent.loaded / progressEvent.total) * 100;
          setUploadProgress(Math.round(progress));
        },
      });

      if (response.data.status === 'success') {
        toast({
          title: 'Success',
          description: 'Backup restored successfully',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
        onSuccess();
        handleClose();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to restore backup',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleClose = () => {
    setIsUploading(false);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="md">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Restore Backup</ModalHeader>
        <ModalCloseButton />

        <ModalBody>
          <VStack spacing={4} align="stretch">
            <Alert status="warning">
              <AlertIcon />
              <Text fontSize="sm">
                Restoring a backup will overwrite current settings and data.
                This action cannot be undone.
              </Text>
            </Alert>

            <Box>
              <Input
                type="file"
                accept=".zip"
                onChange={handleFileChange}
                ref={fileInputRef}
                disabled={isUploading}
              />
              <Text fontSize="xs" color="gray.500" mt={1}>
                Select a backup file (.zip) to restore
              </Text>
            </Box>

            {isUploading && (
              <Box>
                <Text mb={2}>Uploading... {uploadProgress}%</Text>
                <Progress
                  value={uploadProgress}
                  size="sm"
                  colorScheme="brand"
                  isAnimated
                />
              </Box>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={handleClose}>
            Cancel
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
} 