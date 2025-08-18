import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

// Mock the API hooks
jest.mock('./hooks/useApi', () => ({
  useApi: jest.fn(() => ({
    data: null,
    loading: false,
    error: null,
    refetch: jest.fn(),
  })),
  useApiCall: jest.fn(() => ({
    call: jest.fn(),
    loading: false,
    error: null,
  })),
  useWebSocket: jest.fn(() => ({
    isConnected: false,
    sendMessage: jest.fn(),
  })),
}));

test('renders SIM Card Management System title', () => {
  render(<App />);
  const titleElement = screen.getByText(/SIM Card Management System/i);
  expect(titleElement).toBeInTheDocument();
});

test('renders connection status', () => {
  render(<App />);
  const connectionElement = screen.getByText(/Connection/i);
  expect(connectionElement).toBeInTheDocument();
});

test('renders signal strength', () => {
  render(<App />);
  const signalElement = screen.getByText(/Signal/i);
  expect(signalElement).toBeInTheDocument();
});

test('renders navigation tabs', () => {
  render(<App />);
  const overviewTab = screen.getByText(/overview/i);
  const smsTab = screen.getByText(/sms/i);
  const ussdTab = screen.getByText(/ussd/i);
  const settingsTab = screen.getByText(/settings/i);
  
  expect(overviewTab).toBeInTheDocument();
  expect(smsTab).toBeInTheDocument();
  expect(ussdTab).toBeInTheDocument();
  expect(settingsTab).toBeInTheDocument();
});
