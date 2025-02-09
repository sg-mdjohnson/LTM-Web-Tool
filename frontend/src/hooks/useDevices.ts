import { useState, useCallback } from 'react';
import axios from 'axios';
import { Device, DeviceFormData, DeviceUpdateData } from '../types/device';

export const useDevices = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDevices = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/devices');
      setDevices(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to fetch devices');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const addDevice = async (deviceData: DeviceFormData) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('/api/devices', deviceData);
      setDevices(prev => [...prev, response.data]);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to add device');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateDevice = async (id: number, deviceData: Partial<DeviceFormData>) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.put(`/api/devices/${id}`, deviceData);
      setDevices(prev => 
        prev.map(device => 
          device.id === id ? { ...device, ...response.data } : device
        )
      );
      return response.data;
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update device');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteDevice = async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      await axios.delete(`/api/devices/${id}`);
      setDevices(prev => prev.filter(device => device.id !== id));
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to delete device');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async (id: number) => {
    setError(null);
    try {
      const response = await axios.post(`/api/devices/${id}/test`);
      const success = response.data.status === 'success';
      
      // Update device status in local state
      setDevices(prev =>
        prev.map(device =>
          device.id === id
            ? { ...device, status: success ? 'active' : 'error' }
            : device
        )
      );
      
      return success;
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to test connection');
      throw err;
    }
  };

  return {
    devices,
    loading,
    error,
    fetchDevices,
    addDevice,
    updateDevice,
    deleteDevice,
    testConnection
  };
}; 