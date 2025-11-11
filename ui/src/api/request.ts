/**
 * Centralized Axios instance for API requests
 * Provides consistent configuration and error handling
 */
import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE ?? '/api';

/**
 * Create and configure axios instance
 */
const request: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

/**
 * Request interceptor
 */
request.interceptors.request.use(
  (config) => {
    // Add any auth tokens or headers here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor for error handling
 */
request.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    // Handle common errors
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const message = (error.response.data as any)?.detail || error.message;
      
      switch (status) {
        case 400:
          console.error('Bad Request:', message);
          break;
        case 404:
          console.error('Not Found:', message);
          break;
        case 409:
          console.error('Conflict:', message);
          break;
        case 500:
          console.error('Server Error:', message);
          break;
        default:
          console.error(`HTTP ${status}:`, message);
      }
    } else if (error.request) {
      // Request made but no response received
      console.error('Network Error: No response received');
    } else {
      // Error in request setup
      console.error('Request Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

export default request;







