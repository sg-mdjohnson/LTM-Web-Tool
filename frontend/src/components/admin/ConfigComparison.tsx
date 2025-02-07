import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardBody,
  Heading,
  VStack,
  HStack,
  Select,
  Button,
  Text,
  Box,
  useColorModeValue,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Badge,
  Spinner,
  Alert,
  AlertIcon,
  Divider,
  Switch,
  AlertTitle,
  AlertDescription,
  Collapse,
  Spacer,
} from '@chakra-ui/react';
import { DiffEditor } from '@monaco-editor/react';
import { CompareIcon, DownloadIcon, ChevronUpIcon, ChevronDownIcon } from '@chakra-ui/icons';
import api from '../../utils/api';

interface Device {
  id: number;
  name: string;
  host: string;
}

interface ConfigVersion {
  id: string;
  timestamp: string;
  author: string;
  comment?: string;
}

interface ComparisonResult {
  differences: {
    virtualServers: DiffSection[];
    pools: DiffSection[];
    monitors: DiffSection[];
    profiles: DiffSection[];
    irules: DiffSection[];
    policies: DiffSection[];
    certificates: DiffSection[];
    dataGroups: DiffSection[];
    nodes: DiffSection[];
  };
  summary: {
    total: number;
    added: number;
    modified: number;
    removed: number;
    securityImpact: boolean;
    serviceImpact: boolean;
  };
  analysis: {
    securityChanges: AnalysisItem[];
    serviceImpacts: AnalysisItem[];
    recommendations: AnalysisItem[];
  };
}

interface DiffSection {
  type: 'added' | 'modified' | 'removed';
  name: string;
  oldConfig?: string;
  newConfig: string;
}

interface AnalysisItem {
  type: 'warning' | 'info' | 'critical';
  message: string;
  details: string;
  affectedObjects: string[];
}

export default function ConfigComparison() {
  const [sourceDevice, setSourceDevice] = useState<string>('');
  const [targetDevice, setTargetDevice] = useState<string>('');
  const [sourceVersion, setSourceVersion] = useState<string>('current');
  const [targetVersion, setTargetVersion] = useState<string>('current');
  const [devices, setDevices] = useState<Device[]>([]);
  const [versions, setVersions] = useState<Record<string, ConfigVersion[]>>({});
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSection, setSelectedSection] = useState<string>('virtualServers');
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [filterSecurityChanges, setFilterSecurityChanges] = useState(false);
  const [filterServiceImpacts, setFilterServiceImpacts] = useState(false);

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  const loadDevices = async () => {
    try {
      const response = await api.get('/api/admin/devices');
      if (response.data.status === 'success') {
        setDevices(response.data.devices);
      }
    } catch (error) {
      setError('Failed to load devices');
    }
  };

  const loadVersions = async (deviceId: string) => {
    if (!deviceId || deviceId === 'current') return;
    
    try {
      const response = await api.get(`/api/admin/devices/${deviceId}/configs`);
      if (response.data.status === 'success') {
        setVersions(prev => ({
          ...prev,
          [deviceId]: response.data.versions,
        }));
      }
    } catch (error) {
      setError('Failed to load configuration versions');
    }
  };

  const handleCompare = async () => {
    if (!sourceDevice || !targetDevice) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/admin/configs/compare', {
        sourceDevice,
        targetDevice,
        sourceVersion,
        targetVersion,
      });

      if (response.data.status === 'success') {
        setComparison(response.data.comparison);
      }
    } catch (error) {
      setError('Failed to compare configurations');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async () => {
    if (!comparison) return;

    try {
      const response = await api.get('/api/admin/configs/compare/export', {
        params: {
          sourceDevice,
          targetDevice,
          sourceVersion,
          targetVersion,
        },
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `config-comparison-${new Date().toISOString()}.html`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      setError('Failed to export comparison');
    }
  };

  const getSectionCount = (section: string) => {
    if (!comparison) return 0;
    return comparison.differences[section as keyof typeof comparison.differences].length;
  };

  const getDiffBadge = (type: string) => {
    const colors: Record<string, string> = {
      added: 'green',
      modified: 'yellow',
      removed: 'red',
    };
    return <Badge colorScheme={colors[type]}>{type.toUpperCase()}</Badge>;
  };

  const renderAnalysis = () => {
    if (!comparison?.analysis) return null;

    return (
      <VStack spacing={4} align="stretch">
        <HStack>
          <Heading size="sm">Configuration Analysis</Heading>
          <Spacer />
          <Switch
            isChecked={filterSecurityChanges}
            onChange={(e) => setFilterSecurityChanges(e.target.checked)}
            mr={2}
          >
            Security Changes
          </Switch>
          <Switch
            isChecked={filterServiceImpacts}
            onChange={(e) => setFilterServiceImpacts(e.target.checked)}
          >
            Service Impacts
          </Switch>
        </HStack>

        {comparison.analysis.securityChanges.length > 0 && filterSecurityChanges && (
          <Box>
            <Text fontWeight="medium" mb={2}>Security Changes</Text>
            <VStack spacing={2} align="stretch">
              {comparison.analysis.securityChanges.map((item, index) => (
                <Alert
                  key={index}
                  status={item.type === 'critical' ? 'error' : 'warning'}
                  variant="left-accent"
                >
                  <VStack align="stretch" spacing={1}>
                    <AlertTitle>{item.message}</AlertTitle>
                    <AlertDescription fontSize="sm">
                      {item.details}
                      {item.affectedObjects.length > 0 && (
                        <Text mt={1}>
                          Affected objects: {item.affectedObjects.join(', ')}
                        </Text>
                      )}
                    </AlertDescription>
                  </VStack>
                </Alert>
              ))}
            </VStack>
          </Box>
        )}

        {comparison.analysis.serviceImpacts.length > 0 && filterServiceImpacts && (
          <Box>
            <Text fontWeight="medium" mb={2}>Service Impacts</Text>
            <VStack spacing={2} align="stretch">
              {comparison.analysis.serviceImpacts.map((item, index) => (
                <Alert
                  key={index}
                  status={item.type === 'critical' ? 'error' : 'warning'}
                  variant="left-accent"
                >
                  <VStack align="stretch" spacing={1}>
                    <AlertTitle>{item.message}</AlertTitle>
                    <AlertDescription fontSize="sm">
                      {item.details}
                      {item.affectedObjects.length > 0 && (
                        <Text mt={1}>
                          Affected objects: {item.affectedObjects.join(', ')}
                        </Text>
                      )}
                    </AlertDescription>
                  </VStack>
                </Alert>
              ))}
            </VStack>
          </Box>
        )}

        {comparison.analysis.recommendations.length > 0 && (
          <Box>
            <Text fontWeight="medium" mb={2}>Recommendations</Text>
            <VStack spacing={2} align="stretch">
              {comparison.analysis.recommendations.map((item, index) => (
                <Alert key={index} status="info" variant="left-accent">
                  <AlertDescription>{item.message}</AlertDescription>
                </Alert>
              ))}
            </VStack>
          </Box>
        )}
      </VStack>
    );
  };

  return (
    <Card bg={bgColor} borderColor={borderColor}>
      <CardHeader>
        <HStack justify="space-between">
          <Heading size="md">Configuration Comparison</Heading>
          {comparison && (
            <Button
              leftIcon={<DownloadIcon />}
              onClick={handleExport}
              size="sm"
              colorScheme="brand"
            >
              Export Report
            </Button>
          )}
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack spacing={4} align="stretch">
          <HStack spacing={4}>
            <Box flex={1}>
              <Text mb={2}>Source Device</Text>
              <Select
                value={sourceDevice}
                onChange={(e) => {
                  setSourceDevice(e.target.value);
                  loadVersions(e.target.value);
                }}
                placeholder="Select source device"
              >
                {devices.map(device => (
                  <option key={device.id} value={device.id}>
                    {device.name} ({device.host})
                  </option>
                ))}
              </Select>
            </Box>
            <Box flex={1}>
              <Text mb={2}>Source Version</Text>
              <Select
                value={sourceVersion}
                onChange={(e) => setSourceVersion(e.target.value)}
                isDisabled={!sourceDevice}
              >
                <option value="current">Current Configuration</option>
                {versions[sourceDevice]?.map(version => (
                  <option key={version.id} value={version.id}>
                    {new Date(version.timestamp).toLocaleString()} - {version.author}
                  </option>
                ))}
              </Select>
            </Box>
          </HStack>

          <HStack spacing={4}>
            <Box flex={1}>
              <Text mb={2}>Target Device</Text>
              <Select
                value={targetDevice}
                onChange={(e) => {
                  setTargetDevice(e.target.value);
                  loadVersions(e.target.value);
                }}
                placeholder="Select target device"
              >
                {devices.map(device => (
                  <option key={device.id} value={device.id}>
                    {device.name} ({device.host})
                  </option>
                ))}
              </Select>
            </Box>
            <Box flex={1}>
              <Text mb={2}>Target Version</Text>
              <Select
                value={targetVersion}
                onChange={(e) => setTargetVersion(e.target.value)}
                isDisabled={!targetDevice}
              >
                <option value="current">Current Configuration</option>
                {versions[targetDevice]?.map(version => (
                  <option key={version.id} value={version.id}>
                    {new Date(version.timestamp).toLocaleString()} - {version.author}
                  </option>
                ))}
              </Select>
            </Box>
          </HStack>

          <Button
            leftIcon={<CompareIcon />}
            onClick={handleCompare}
            isLoading={isLoading}
            isDisabled={!sourceDevice || !targetDevice}
            colorScheme="brand"
          >
            Compare Configurations
          </Button>

          {error && (
            <Alert status="error">
              <AlertIcon />
              {error}
            </Alert>
          )}

          {comparison && (
            <>
              <Divider />
              
              <HStack spacing={4} wrap="wrap">
                <Badge colorScheme="blue">
                  Total Differences: {comparison.summary.total}
                </Badge>
                <Badge colorScheme="green">
                  Added: {comparison.summary.added}
                </Badge>
                <Badge colorScheme="yellow">
                  Modified: {comparison.summary.modified}
                </Badge>
                <Badge colorScheme="red">
                  Removed: {comparison.summary.removed}
                </Badge>
                {comparison.summary.securityImpact && (
                  <Badge colorScheme="red">Security Impact</Badge>
                )}
                {comparison.summary.serviceImpact && (
                  <Badge colorScheme="orange">Service Impact</Badge>
                )}
              </HStack>

              <Button
                size="sm"
                variant="ghost"
                rightIcon={showAnalysis ? <ChevronUpIcon /> : <ChevronDownIcon />}
                onClick={() => setShowAnalysis(!showAnalysis)}
              >
                Configuration Analysis
              </Button>

              <Collapse in={showAnalysis}>
                {renderAnalysis()}
              </Collapse>

              <Tabs onChange={(index) => {
                const sections = [
                  'virtualServers',
                  'pools',
                  'monitors',
                  'profiles',
                  'irules',
                  'policies',
                  'certificates',
                  'dataGroups',
                  'nodes'
                ];
                setSelectedSection(sections[index]);
              }}>
                <TabList flexWrap="wrap">
                  <Tab>Virtual Servers ({getSectionCount('virtualServers')})</Tab>
                  <Tab>Pools ({getSectionCount('pools')})</Tab>
                  <Tab>Monitors ({getSectionCount('monitors')})</Tab>
                  <Tab>Profiles ({getSectionCount('profiles')})</Tab>
                  <Tab>iRules ({getSectionCount('irules')})</Tab>
                  <Tab>Policies ({getSectionCount('policies')})</Tab>
                  <Tab>Certificates ({getSectionCount('certificates')})</Tab>
                  <Tab>Data Groups ({getSectionCount('dataGroups')})</Tab>
                  <Tab>Nodes ({getSectionCount('nodes')})</Tab>
                </TabList>

                <TabPanels>
                  {['virtualServers', 'pools', 'monitors', 'profiles', 'irules', 'policies', 'certificates', 'dataGroups', 'nodes'].map((section) => (
                    <TabPanel key={section}>
                      <VStack spacing={4} align="stretch">
                        {comparison.differences[section as keyof typeof comparison.differences].map((diff, index) => (
                          <Box key={index} borderWidth={1} borderRadius="md" p={4}>
                            <HStack justify="space-between" mb={2}>
                              <Text fontWeight="medium">{diff.name}</Text>
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
      </CardBody>
    </Card>
  );
} 