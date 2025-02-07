import React, { useState } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Button,
  VStack,
  HStack,
  Text,
  Box,
  Select,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Badge,
  Spinner,
  Alert,
  AlertIcon,
  useColorModeValue,
  Divider,
} from '@chakra-ui/react';
import { DiffEditor } from '@monaco-editor/react';
import { DownloadIcon } from '@chakra-ui/icons';
import api from '../../utils/api';
import { BackupEntry } from '../../types';

interface BackupDiffProps {
  isOpen: boolean;
  onClose: () => void;
  sourceBackup: BackupEntry;
  backups: BackupEntry[];
}

interface DiffResult {
  sections: {
    virtualServers: DiffSection[];
    pools: DiffSection[];
    monitors: DiffSection[];
    profiles: DiffSection[];
    irules: DiffSection[];
    policies: DiffSection[];
    certificates: DiffSection[];
  };
  summary: {
    total: number;
    added: number;
    modified: number;
    removed: number;
  };
}

interface DiffSection {
  name: string;
  type: 'added' | 'modified' | 'removed';
  oldConfig?: string;
  newConfig: string;
  device: string;
}

export default function BackupDiffViewer({ isOpen, onClose, sourceBackup, backups }: BackupDiffProps) {
  const [targetBackup, setTargetBackup] = useState<string>('');
  const [selectedDevice, setSelectedDevice] = useState<string>('all');
  const [diffResult, setDiffResult] = useState<DiffResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  const handleCompare = async () => {
    if (!targetBackup) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/admin/backups/compare', {
        sourceId: sourceBackup.id,
        targetId: targetBackup,
        device: selectedDevice === 'all' ? undefined : selectedDevice,
      });

      if (response.data.status === 'success') {
        setDiffResult(response.data.diff);
      }
    } catch (error) {
      setError('Failed to compare backups');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async () => {
    if (!diffResult) return;

    try {
      const response = await api.get('/api/admin/backups/compare/export', {
        params: {
          sourceId: sourceBackup.id,
          targetId: targetBackup,
          device: selectedDevice === 'all' ? undefined : selectedDevice,
        },
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `backup-diff-${new Date().toISOString()}.html`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      setError('Failed to export comparison');
    }
  };

  const getSectionCount = (section: keyof DiffResult['sections']) => {
    if (!diffResult) return 0;
    return diffResult.sections[section].length;
  };

  const getDiffBadge = (type: string) => {
    const colors: Record<string, string> = {
      added: 'green',
      modified: 'yellow',
      removed: 'red',
    };
    return <Badge colorScheme={colors[type]}>{type.toUpperCase()}</Badge>;
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="6xl">
      <ModalOverlay />
      <ModalContent maxHeight="90vh">
        <ModalHeader>Compare Backup Configurations</ModalHeader>
        <ModalCloseButton />
        
        <ModalBody overflowY="auto">
          <VStack spacing={4} align="stretch">
            <HStack spacing={4}>
              <Box flex={1}>
                <Text mb={2}>Source Backup</Text>
                <Text fontWeight="medium">
                  {new Date(sourceBackup.timestamp).toLocaleString()} - {sourceBackup.author}
                </Text>
              </Box>

              <Box flex={1}>
                <Text mb={2}>Target Backup</Text>
                <Select
                  value={targetBackup}
                  onChange={(e) => setTargetBackup(e.target.value)}
                  placeholder="Select target backup"
                >
                  {backups
                    .filter((b) => b.id !== sourceBackup.id)
                    .map((backup) => (
                      <option key={backup.id} value={backup.id}>
                        {new Date(backup.timestamp).toLocaleString()} - {backup.author}
                      </option>
                    ))}
                </Select>
              </Box>

              <Box flex={1}>
                <Text mb={2}>Device</Text>
                <Select
                  value={selectedDevice}
                  onChange={(e) => setSelectedDevice(e.target.value)}
                >
                  <option value="all">All Devices</option>
                  {sourceBackup.devices.map((device: string) => (
                    <option key={device} value={device}>
                      {device}
                    </option>
                  ))}
                </Select>
              </Box>
            </HStack>

            <Button
              onClick={handleCompare}
              isLoading={isLoading}
              isDisabled={!targetBackup}
              colorScheme="brand"
            >
              Compare Backups
            </Button>

            {error && (
              <Alert status="error">
                <AlertIcon />
                {error}
              </Alert>
            )}

            {diffResult && (
              <>
                <Divider />
                
                <HStack spacing={4}>
                  <Badge colorScheme="blue">
                    Total Changes: {diffResult.summary.total}
                  </Badge>
                  <Badge colorScheme="green">
                    Added: {diffResult.summary.added}
                  </Badge>
                  <Badge colorScheme="yellow">
                    Modified: {diffResult.summary.modified}
                  </Badge>
                  <Badge colorScheme="red">
                    Removed: {diffResult.summary.removed}
                  </Badge>
                  <Button
                    size="sm"
                    leftIcon={<DownloadIcon />}
                    onClick={handleExport}
                    ml="auto"
                  >
                    Export Report
                  </Button>
                </HStack>

                <Tabs>
                  <TabList flexWrap="wrap">
                    <Tab>Virtual Servers ({getSectionCount('virtualServers')})</Tab>
                    <Tab>Pools ({getSectionCount('pools')})</Tab>
                    <Tab>Monitors ({getSectionCount('monitors')})</Tab>
                    <Tab>Profiles ({getSectionCount('profiles')})</Tab>
                    <Tab>iRules ({getSectionCount('irules')})</Tab>
                    <Tab>Policies ({getSectionCount('policies')})</Tab>
                    <Tab>Certificates ({getSectionCount('certificates')})</Tab>
                  </TabList>

                  <TabPanels>
                    {Object.entries(diffResult.sections).map(([section, diffs]) => (
                      <TabPanel key={section}>
                        <VStack spacing={4} align="stretch">
                          {diffs.map((diff, index) => (
                            <Box
                              key={index}
                              borderWidth={1}
                              borderRadius="md"
                              p={4}
                              bg={bgColor}
                              borderColor={borderColor}
                            >
                              <HStack justify="space-between" mb={2}>
                                <VStack align="start" spacing={0}>
                                  <Text fontWeight="medium">{diff.name}</Text>
                                  <Text fontSize="sm" color="gray.500">
                                    Device: {diff.device}
                                  </Text>
                                </VStack>
                                {getDiffBadge(diff.type)}
                              </HStack>
                              <Box height="300px" borderWidth={1} borderRadius="md">
                                <DiffEditor
                                  height="100%"
                                  language="shell"
                                  original={diff.oldConfig || ''}
                                  modified={diff.newConfig}
                                  options={{
                                    readOnly: true,
                                    renderSideBySide: true,
                                    minimap: { enabled: false },
                                  }}
                                />
                              </Box>
                            </Box>
                          ))}
                        </VStack>
                      </TabPanel>
                    ))}
                  </TabPanels>
                </Tabs>
              </>
            )}
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button onClick={onClose}>Close</Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
} 