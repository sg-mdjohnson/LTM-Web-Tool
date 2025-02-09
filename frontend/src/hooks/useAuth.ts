import { useState, useCallback, useEffect } from 'react';
import axios from 'axios';
import { User } from '../types/auth';

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkAuth = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        const response = await axios.get('/api/auth/me');
        setUser(response.data);
      }
    } catch (err) {
      localStorage.removeItem('token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (username: string, password: string) => {
    try {
      const response = await axios.post('/api/auth/login', {
        username,
        password
      });
      localStorage.setItem('token', response.data.token);
      setUser(response.data.user);
      return response.data.user;
    } catch (err) {
      throw new Error(err.response?.data?.message || 'Login failed');
    }
  };

  const register = async (username: string, email: string, password: string) => {
    try {
      const response = await axios.post('/api/auth/register', {
        username,
        email,
        password
      });
      return response.data;
    } catch (err) {
      throw new Error(err.response?.data?.message || 'Registration failed');
    }
  };

  const logout = async () => {
    try {
      await axios.post('/api/auth/logout');
    } finally {
      localStorage.removeItem('token');
      setUser(null);
    }
  };

  const requestPasswordReset = async (email: string) => {
    try {
      await axios.post('/api/auth/forgot-password', { email });
    } catch (err) {
      throw new Error(err.response?.data?.message || 'Failed to send reset email');
    }
  };

  const resetPassword = async (token: string, newPassword: string) => {
    try {
      await axios.post('/api/auth/reset-password', {
        token,
        password: newPassword
      });
    } catch (err) {
      throw new Error(err.response?.data?.message || 'Password reset failed');
    }
  };

  return {
    user,
    loading,
    error,
    login,
    register,
    logout,
    requestPasswordReset,
    resetPassword,
    checkAuth
  };
}; 