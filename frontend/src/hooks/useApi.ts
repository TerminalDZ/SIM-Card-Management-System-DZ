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
      const response = await axios.get(`${API_BASE_URL}${endpoint}`);
      setState({ data: response.data, loading: false, error: null });
    } catch (error: any) {
      setState({ 
        data: null, 
        loading: false, 
        error: error.response?.data?.detail || error.message || 'An error occurred' 
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
      switch (method) {
        case 'GET':
          response = await axios.get(`${API_BASE_URL}${endpoint}`);
          break;
        case 'POST':
          response = await axios.post(`${API_BASE_URL}${endpoint}`, data);
          break;
        case 'DELETE':
          response = await axios.delete(`${API_BASE_URL}${endpoint}`);
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

  useEffect(() => {
    const ws = new WebSocket(url);
    
    ws.onopen = () => {
      setIsConnected(true);
      setSocket(ws);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      setSocket(null);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
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

    return () => {
      ws.close();
    };
  }, [url, onMessage]);

  const sendMessage = useCallback((data: any) => {
    if (socket && isConnected) {
      socket.send(JSON.stringify(data));
    }
  }, [socket, isConnected]);

  return { isConnected, sendMessage };
}
