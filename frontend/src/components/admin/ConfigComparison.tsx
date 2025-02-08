import React, { useState } from 'react';
import {
  Box,
  Button,
  Grid,
  Select,
  Text,
  useToast,
  Heading,
  HStack,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Badge,
  Spinner,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Collapse,
  Spacer,
  Textarea,
} from '@chakra-ui/react';
import { DiffEditor } from '@monaco-editor/react';
import { ChevronUpIcon, ChevronDownIcon } from '@chakra-ui/icons';
import api from '../../utils/api';
import { useApiError } from '../../utils/api';
import LoadingSpinner from '../common/LoadingSpinner';

interface Device {
  id: number;
  name: string;
}

interface ConfigVersion {
  id: string;
  timestamp: string;
  comment?: string;
}

interface ComparisonResult {
  sections: {
    name: string;
    differences: {
      type: 'added' | 'removed' | 'modified';
      line: string;
      lineNumber: number;
    }[];
  }[];
}

export default function ConfigComparison() {
  const [sourceDevice, setSourceDevice] = useState<string>('');
  const [targetDevice, setTargetDevice] = useState<string>('');
  const [devices, setDevices] = useState<Device[]>([]);
  const [originalConfig, setOriginalConfig] = useState<string>('');
  const [modifiedConfig, setModifiedConfig] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [sourceVersion, setSourceVersion] = useState<string>('');
  const [targetVersion, setTargetVersion] = useState<string>('');
  const [versions, setVersions] = useState<ConfigVersion[]>([]);
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const toast = useToast();
  const { handleError } = useApiError();
  const [selectedSection, setSelectedSection] = useState<string | null>(null);
  const [showAnalysis, setShowAnalysis] = useState(false);

  const handleCompare = async () => {
    if (!sourceDevice || !targetDevice) {
      toast({
        title: 'Error',
        description: 'Please select both devices',
        status: 'error',
        duration: 3000,
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await api.post('/api/admin/compare-configs', {
        source_device: sourceDevice,
        target_device: targetDevice,
        source_version: sourceVersion || undefined,
        target_version: targetVersion || undefined,
      });

      setOriginalConfig(response.data.source_config);
      setModifiedConfig(response.data.target_config);
      setComparison(response.data.analysis);
    } catch (error) {
      handleError(error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadDevices = React.useCallback(async () => {
    try {
      const response = await api.get('/api/devices');
      setDevices(response.data);
    } catch (error) {
      handleError(error);
    }
  }, [handleError]);

  const loadVersions = async (deviceId: string) => {
    try {
      const response = await api.get(`/api/admin/config-versions/${deviceId}`);
      setVersions(response.data.versions);
    } catch (error) {
      handleError(error);
    }
  };

  React.useEffect(() => {
    loadDevices();
  }, [loadDevices]);

  React.useEffect(() => {
    if (sourceDevice) {
      loadVersions(sourceDevice);
    }
  }, [sourceDevice]);

  const getSectionCount = (type: 'added' | 'removed' | 'modified') => {
    if (!comparison) return 0;
    return comparison.sections.reduce((count, section) => {
      return count + section.differences.filter(d => d.type === type).length;
    }, 0);
  };

  const getDiffBadge = (type: 'added' | 'removed' | 'modified') => {
    const count = getSectionCount(type);
    const colors = {
      added: 'green',
      removed: 'red',
      modified: 'yellow'
    };
    return count > 0 ? (
      <Badge colorScheme={colors[type]} ml={2}>
        {count} {type}
      </Badge>
    ) : null;
  };

  const renderAnalysis = () => {
    if (!comparison) return null;

    return (
      <Box mt={4}>
        <Button
          rightIcon={showAnalysis ? <ChevronUpIcon /> : <ChevronDownIcon />}
          onClick={() => setShowAnalysis(!showAnalysis)}
          mb={2}
        >
          Configuration Analysis
        </Button>
        <Collapse in={showAnalysis}>
          <Box p={4} borderWidth={1} borderRadius="md">
            {comparison.sections.map((section, idx) => (
              <Box key={idx} mb={4}>
                <Button
                  variant="link"
                  onClick={() => setSelectedSection(section.name)}
                  mb={2}
                >
                  {section.name}
                </Button>
                {getDiffBadge('added')}
                {getDiffBadge('removed')}
                {getDiffBadge('modified')}
                {selectedSection === section.name && (
                  <Box pl={4}>
                    {section.differences.map((diff, i) => (
                      <Text
                        key={i}
                        color={
                          diff.type === 'added'
                            ? 'green.500'
                            : diff.type === 'removed'
                            ? 'red.500'
                            : 'yellow.500'
                        }
                      >
                        {diff.type}: Line {diff.lineNumber} - {diff.line}
                      </Text>
                    ))}
                  </Box>
                )}
              </Box>
            ))}
          </Box>
        </Collapse>
      </Box>
    );
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <Box>
      <Heading mb={6}>Configuration Comparison</Heading>
      <Tabs>
        <TabList>
          <Tab>Current Configs</Tab>
          <Tab>Version History</Tab>
        </TabList>
        <TabPanels>
          <TabPanel>
            <Grid templateColumns="repeat(2, 1fr)" gap={6} mb={6}>
              <Box>
                <Text mb={2}>Source Device</Text>
                <Select
                  value={sourceDevice}
                  onChange={(e) => setSourceDevice(e.target.value)}
                  placeholder="Select source device"
                >
                  {devices.map((device) => (
                    <option key={device.id} value={device.id}>
                      {device.name}
                    </option>
                  ))}
                </Select>
              </Box>
              <Box>
                <Text mb={2}>Target Device</Text>
                <Select
                  value={targetDevice}
                  onChange={(e) => setTargetDevice(e.target.value)}
                  placeholder="Select target device"
                >
                  {devices.map((device) => (
                    <option key={device.id} value={device.id}>
                      {device.name}
                    </option>
                  ))}
                </Select>
              </Box>
            </Grid>
          </TabPanel>
          <TabPanel>
            <Grid templateColumns="repeat(2, 1fr)" gap={6} mb={6}>
              <Box>
                <Text mb={2}>Source Version</Text>
                <Select
                  value={sourceVersion}
                  onChange={(e) => setSourceVersion(e.target.value)}
                  placeholder="Select version"
                >
                  {versions.map((version) => (
                    <option key={version.id} value={version.id}>
                      {new Date(version.timestamp).toLocaleString()} {version.comment}
                    </option>
                  ))}
                </Select>
              </Box>
              <Box>
                <Text mb={2}>Target Version</Text>
                <Select
                  value={targetVersion}
                  onChange={(e) => setTargetVersion(e.target.value)}
                  placeholder="Select version"
                >
                  {versions.map((version) => (
                    <option key={version.id} value={version.id}>
                      {new Date(version.timestamp).toLocaleString()} {version.comment}
                    </option>
                  ))}
                </Select>
              </Box>
            </Grid>
          </TabPanel>
        </TabPanels>
      </Tabs>

      <Button onClick={handleCompare} mb={6}>
        Compare Configurations
      </Button>

      {renderAnalysis()}

      {originalConfig && modifiedConfig && (
        <Box mt={4} height="600px">
          <DiffEditor
            height="100%"
            language="shell"
            original={originalConfig}
            modified={modifiedConfig}
            options={{
              readOnly: true,
              renderSideBySide: true,
            }}
          />
        </Box>
      )}
    </Box>
  );
} 