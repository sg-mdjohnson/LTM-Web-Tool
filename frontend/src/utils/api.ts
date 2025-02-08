import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Add request interceptor for auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`, config);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status}`, response);
    return response;
  },
  (error) => {
    console.error('API Error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      data: error.response?.data,
    });
    if (error.response) {
      console.error('API Error Response:', error.response);
      if (error.response.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
      return Promise.reject(error.response.data);
    } else if (error.request) {
      console.error('API No Response:', error.request);
      return Promise.reject(new Error('No response from server'));
    } else {
      console.error('API Request Error:', error.message);
      return Promise.reject(error);
    }
  }
);

export default api;

// Custom hook for API errors
export function useApiError() {
  const navigate = useNavigate();

  return {
    handleError: (error: any) => {
      if (error.response) {
        switch (error.response.status) {
          case 401:
            navigate('/login');
            break;
          case 403:
            // Handle forbidden
            break;
          case 404:
            // Handle not found
            break;
          default:
            // Handle other errors
            break;
        }
      }
      return error.response?.data?.message || 'An error occurred';
    },
  };
} 