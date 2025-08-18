import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useApi<T>(endpoint: string, dependencies: any[] = []) {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      const response = await axios.get(`${API_BASE_URL}${endpoint}`, {
        timeout: 10000 // 10 second timeout
      });
      setState({ data: response.data, loading: false, error: null });
    } catch (error: any) {
      console.warn(`API call failed for ${endpoint}:`, error.message);
      setState({ 
        data: null, 
        loading: false, 
        error: error.response?.data?.detail || error.message || 'Connection timeout' 
      });
    }
  }, [endpoint]);

  useEffect(() => {
    fetchData();
  }, [fetchData, ...dependencies]);

  return { ...state, refetch: fetchData };
}

export function useApiCall() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const call = useCallback(async (method: 'GET' | 'POST' | 'DELETE', endpoint: string, data?: any) => {
    try {
      setLoading(true);
      setError(null);
      
      let response;
      const config = { timeout: 15000 }; // 15 second timeout for user actions
      
      switch (method) {
        case 'GET':
          response = await axios.get(`${API_BASE_URL}${endpoint}`, config);
          break;
        case 'POST':
          response = await axios.post(`${API_BASE_URL}${endpoint}`, data, config);
          break;
        case 'DELETE':
          response = await axios.delete(`${API_BASE_URL}${endpoint}`, config);
          break;
        default:
          throw new Error(`Unsupported method: ${method}`);
      }
      
      return response.data;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'An error occurred';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  return { call, loading, error };
}

export function useWebSocket(url: string, onMessage?: (data: any) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const maxRetries = 5;
  const retryDelay = 3000; // 3 seconds

  useEffect(() => {
    let reconnectTimer: NodeJS.Timeout;
    let ws: WebSocket;

    const connect = () => {
      try {
        ws = new WebSocket(url);
        
        ws.onopen = () => {
          console.log('WebSocket connected');
          setIsConnected(true);
          setSocket(ws);
          setRetryCount(0); // Reset retry count on successful connection
        };
        
        ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          setIsConnected(false);
          setSocket(null);
          
          // Only retry if it wasn't a clean close and we haven't exceeded max retries
          if (event.code !== 1000 && retryCount < maxRetries) {
            console.log(`Retrying WebSocket connection (${retryCount + 1}/${maxRetries}) in ${retryDelay}ms...`);
            reconnectTimer = setTimeout(() => {
              setRetryCount(prev => prev + 1);
              connect();
            }, retryDelay);
          }
        };
        
        ws.onerror = (error) => {
          console.log('WebSocket connection to', url, 'failed:', error);
          setIsConnected(false);
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            onMessage?.(data);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        setIsConnected(false);
      }
    };

    // Initial connection
    connect();

    return () => {
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      if (ws) {
        ws.close(1000, 'Component unmounting'); // Clean close
      }
    };
  }, [url, onMessage, retryCount]);

  const sendMessage = useCallback((data: any) => {
    if (socket && isConnected && socket.readyState === WebSocket.OPEN) {
      try {
        socket.send(JSON.stringify(data));
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
      }
    }
  }, [socket, isConnected]);

  return { isConnected, sendMessage, retryCount };
}
