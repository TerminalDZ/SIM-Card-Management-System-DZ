import React, { useState, useEffect } from 'react';
import { useApi, useApiCall, useWebSocket } from '../hooks/useApi';
import { ModemStatus, SimInfo, SmsMessage, BalanceResponse } from '../types';
import { ErrorBoundary } from './ErrorBoundary';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorAlert } from './ErrorAlert';

export default function SimpleDashboard() {
  const [selectedTab, setSelectedTab] = useState('overview');
  const [newSms, setNewSms] = useState({ phone: '', message: '' });
  const [ussdCommand, setUssdCommand] = useState('');
  
  // API hooks
  const { data: status, loading: statusLoading, error: statusError, refetch: refetchStatus } = useApi<ModemStatus>('/status');
  const { data: simInfo, loading: simLoading, error: simError, refetch: refetchSimInfo } = useApi<SimInfo>('/sim-info');
  const { data: smsData, loading: smsLoading, error: smsError, refetch: refetchSms } = useApi<{messages: SmsMessage[]}>('/sms');
  const { data: simStatus, loading: simStatusLoading, refetch: refetchSimStatus } = useApi<any>('/sim-status');
  const { call, loading: apiLoading, error: apiError } = useApiCall();

  // WebSocket for real-time updates
  useWebSocket('ws://localhost:8000/ws', (data) => {
    if (data.type === 'status_update') {
      refetchStatus();
      refetchSimStatus();
    } else if (data.type === 'sms_sent' || data.type === 'sms_deleted') {
      refetchSms();
    } else if (data.type === 'sim_change') {
      refetchSimInfo();
      refetchSimStatus();
    }
  });

  const handleSendSms = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSms.phone || !newSms.message) return;
    
    try {
      await call('POST', '/sms/send', {
        phone_number: newSms.phone,
        message: newSms.message
      });
      setNewSms({ phone: '', message: '' });
      refetchSms();
      alert('SMS sent successfully!');
    } catch (error) {
      console.error('Failed to send SMS:', error);
    }
  };

  const handleDeleteSms = async (messageId: number) => {
    try {
      await call('DELETE', `/sms/${messageId}`);
      refetchSms();
    } catch (error) {
      console.error('Failed to delete SMS:', error);
    }
  };

  const handleSendUssd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ussdCommand) return;
    
    try {
      const response = await call('POST', '/ussd', { command: ussdCommand });
      alert(`USSD Response: ${response.response}`);
      setUssdCommand('');
    } catch (error) {
      console.error('Failed to send USSD:', error);
    }
  };

  const handleCheckBalance = async () => {
    try {
      const response = await call('GET', '/balance') as BalanceResponse;
      alert(`Balance for ${response.operator}: ${response.response}`);
    } catch (error) {
      console.error('Failed to check balance:', error);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  if (statusLoading) {
    return <LoadingSpinner text="Loading system..." />;
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb', padding: '24px' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '32px' }}>
          <h1 style={{ fontSize: '2rem', fontWeight: 'bold', color: '#111827', marginBottom: '8px' }}>
            SIM Card Management System
          </h1>
          <p style={{ color: '#6b7280' }}>
            Professional control panel for Algerian mobile operators
          </p>
        </div>

        {/* Status Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px', marginBottom: '32px' }}>
          {/* Connection Status */}
          <div style={{ backgroundColor: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '500', marginBottom: '16px' }}>Connection</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ 
                width: '12px', 
                height: '12px', 
                borderRadius: '50%', 
                backgroundColor: status?.connected ? '#10b981' : '#ef4444' 
              }}></div>
              <span style={{ fontWeight: '500' }}>
                {status?.connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            {status?.port && (
              <p style={{ fontSize: '0.875rem', color: '#6b7280', marginTop: '4px' }}>
                Port: {status.port}
              </p>
            )}
            
            {/* SIM Detection Status */}
            {simStatus && (
              <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #e5e7eb' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ 
                    width: '8px', 
                    height: '8px', 
                    borderRadius: '50%', 
                    backgroundColor: simStatus.sim_detected ? '#10b981' : '#f59e0b' 
                  }}></div>
                  <span style={{ fontSize: '0.875rem', fontWeight: '500' }}>
                    SIM: {simStatus.sim_detected ? 'Detected' : 'Not Detected'}
                  </span>
                </div>
                {simStatus.operator?.name && (
                  <p style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '4px' }}>
                    {simStatus.operator.name}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Signal Strength */}
          <div style={{ backgroundColor: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '500', marginBottom: '16px' }}>Signal</h3>
            <div style={{ fontSize: '2rem', fontWeight: 'bold' }}>
              {simInfo?.signal_strength || 0}%
            </div>
            <div style={{ 
              width: '100%', 
              height: '8px', 
              backgroundColor: '#e5e7eb', 
              borderRadius: '4px', 
              marginTop: '8px' 
            }}>
              <div style={{ 
                width: `${simInfo?.signal_strength || 0}%`, 
                height: '100%', 
                backgroundColor: '#10b981', 
                borderRadius: '4px' 
              }}></div>
            </div>
          </div>

          {/* Network Type */}
          <div style={{ backgroundColor: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '500', marginBottom: '16px' }}>Network</h3>
            <div style={{ 
              display: 'inline-block', 
              padding: '4px 12px', 
              backgroundColor: '#3b82f6', 
              color: 'white', 
              borderRadius: '20px', 
              fontSize: '0.875rem',
              fontWeight: '500'
            }}>
              {simInfo?.network_type || 'Unknown'}
            </div>
            {simInfo?.network_operator && (
              <p style={{ fontSize: '0.875rem', color: '#6b7280', marginTop: '8px' }}>
                {simInfo.network_operator}
              </p>
            )}
          </div>

          {/* Operator */}
          <div style={{ backgroundColor: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '500', marginBottom: '16px' }}>Operator</h3>
            <div style={{ fontSize: '1.25rem', fontWeight: '600' }}>
              {simInfo?.operator?.name || 'Unknown'}
            </div>
            {simInfo?.msisdn && (
              <p style={{ fontSize: '0.875rem', color: '#6b7280', marginTop: '4px' }}>
                {simInfo.msisdn}
              </p>
            )}
          </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', gap: '4px', backgroundColor: '#f3f4f6', padding: '4px', borderRadius: '8px', width: 'fit-content' }}>
            {['overview', 'sms', 'ussd', 'settings'].map((tab) => (
              <button
                key={tab}
                onClick={() => setSelectedTab(tab)}
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: '6px',
                  backgroundColor: selectedTab === tab ? 'white' : 'transparent',
                  color: selectedTab === tab ? '#111827' : '#6b7280',
                  fontWeight: selectedTab === tab ? '500' : '400',
                  cursor: 'pointer',
                  textTransform: 'capitalize'
                }}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        {selectedTab === 'overview' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>
            {/* SIM Information */}
            <div style={{ backgroundColor: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '16px' }}>SIM Information</h3>
              {simLoading ? (
                <LoadingSpinner text="Loading SIM info..." />
              ) : simError ? (
                <ErrorAlert error={simError} />
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div>
                    <label style={{ fontSize: '0.875rem', fontWeight: '500', color: '#6b7280' }}>IMSI</label>
                    <p style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{simInfo?.imsi || 'N/A'}</p>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.875rem', fontWeight: '500', color: '#6b7280' }}>ICCID</label>
                    <p style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{simInfo?.iccid || 'N/A'}</p>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.875rem', fontWeight: '500', color: '#6b7280' }}>IMEI</label>
                    <p style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{simInfo?.imei || 'N/A'}</p>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.875rem', fontWeight: '500', color: '#6b7280' }}>Phone Number</label>
                    <p style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{simInfo?.msisdn || 'N/A'}</p>
                  </div>
                </div>
              )}
              <button 
                onClick={refetchSimInfo}
                style={{
                  marginTop: '16px',
                  padding: '8px 16px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  backgroundColor: 'white',
                  cursor: 'pointer'
                }}
              >
                Refresh
              </button>
            </div>

            {/* Quick Actions */}
            <div style={{ backgroundColor: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '16px' }}>Quick Actions</h3>
              <button 
                onClick={handleCheckBalance}
                disabled={apiLoading}
                style={{
                  width: '100%',
                  padding: '12px',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: '500',
                  cursor: apiLoading ? 'not-allowed' : 'pointer',
                  opacity: apiLoading ? 0.6 : 1
                }}
              >
                Check Balance
              </button>
              
              {simInfo?.operator?.common_services && (
                <div style={{ marginTop: '16px' }}>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: '500', marginBottom: '8px' }}>Common Services</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                    {Object.entries(simInfo.operator.common_services).map(([key, code]) => (
                      <button
                        key={key}
                        onClick={() => setUssdCommand(code)}
                        style={{
                          padding: '6px 12px',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          backgroundColor: 'white',
                          fontSize: '0.75rem',
                          cursor: 'pointer'
                        }}
                      >
                        {key.replace('_', ' ').toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {selectedTab === 'sms' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>
            {/* Send SMS */}
            <div style={{ backgroundColor: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '16px' }}>Send SMS</h3>
              <form onSubmit={handleSendSms} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '4px' }}>Phone Number</label>
                  <input
                    type="text"
                    placeholder="e.g., 0555123456"
                    value={newSms.phone}
                    onChange={(e) => setNewSms(prev => ({ ...prev, phone: e.target.value }))}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                      fontSize: '0.875rem'
                    }}
                    required
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '4px' }}>Message</label>
                  <textarea
                    placeholder="Type your message here..."
                    value={newSms.message}
                    onChange={(e) => setNewSms(prev => ({ ...prev, message: e.target.value }))}
                    rows={4}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                      fontSize: '0.875rem',
                      resize: 'vertical'
                    }}
                    required
                  />
                </div>
                <button 
                  type="submit"
                  disabled={apiLoading || !newSms.phone || !newSms.message}
                  style={{
                    width: '100%',
                    padding: '12px',
                    backgroundColor: '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontWeight: '500',
                    cursor: (apiLoading || !newSms.phone || !newSms.message) ? 'not-allowed' : 'pointer',
                    opacity: (apiLoading || !newSms.phone || !newSms.message) ? 0.6 : 1
                  }}
                >
                  Send SMS
                </button>
              </form>
            </div>

            {/* SMS Inbox */}
            <div style={{ backgroundColor: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: '600' }}>SMS Inbox</h3>
                  <p style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                    {smsData?.messages ? `${smsData.messages.length} messages` : 'Loading...'}
                  </p>
                </div>
                <button 
                  onClick={refetchSms}
                  disabled={smsLoading}
                  style={{
                    padding: '6px 12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px',
                    backgroundColor: 'white',
                    cursor: smsLoading ? 'not-allowed' : 'pointer',
                    opacity: smsLoading ? 0.6 : 1
                  }}
                >
                  {smsLoading ? '🔄' : 'Refresh'}
                </button>
              </div>
              {smsLoading ? (
                <LoadingSpinner text="Loading messages..." />
              ) : smsError ? (
                <ErrorAlert error={smsError} />
              ) : (
                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  {smsData?.messages?.length ? (
                    smsData.messages.map((msg) => (
                      <div key={msg.id} style={{ 
                        border: '1px solid #e5e7eb', 
                        borderRadius: '8px', 
                        padding: '12px', 
                        marginBottom: '12px' 
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ 
                              padding: '2px 8px', 
                              backgroundColor: msg.status.includes('REC') ? '#3b82f6' : '#6b7280',
                              color: 'white',
                              borderRadius: '12px',
                              fontSize: '0.75rem'
                            }}>
                              {msg.status}
                            </span>
                            <span style={{ fontSize: '0.875rem', fontWeight: '500' }}>{msg.phone_number}</span>
                          </div>
                          <button
                            onClick={() => handleDeleteSms(msg.id)}
                            style={{
                              padding: '4px 8px',
                              border: '1px solid #ef4444',
                              borderRadius: '4px',
                              backgroundColor: 'white',
                              color: '#ef4444',
                              cursor: 'pointer',
                              fontSize: '0.75rem'
                            }}
                          >
                            Delete
                          </button>
                        </div>
                        <p style={{ fontSize: '0.875rem', marginBottom: '8px' }}>{msg.message}</p>
                        <p style={{ fontSize: '0.75rem', color: '#6b7280' }}>{formatTimestamp(msg.timestamp)}</p>
                      </div>
                    ))
                  ) : (
                    <div style={{ textAlign: 'center', color: '#6b7280', padding: '32px' }}>
                      <p>No messages found</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {selectedTab === 'ussd' && (
          <div style={{ backgroundColor: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', maxWidth: '600px' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '16px' }}>USSD Commands</h3>
            <form onSubmit={handleSendUssd} style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                placeholder="e.g., *100#"
                value={ussdCommand}
                onChange={(e) => setUssdCommand(e.target.value)}
                style={{
                  flex: 1,
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '0.875rem'
                }}
                required
              />
              <button 
                type="submit"
                disabled={apiLoading || !ussdCommand}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontWeight: '500',
                  cursor: (apiLoading || !ussdCommand) ? 'not-allowed' : 'pointer',
                  opacity: (apiLoading || !ussdCommand) ? 0.6 : 1
                }}
              >
                Send
              </button>
            </form>
            
            {apiError && (
              <ErrorAlert error={apiError} />
            )}
          </div>
        )}

        {selectedTab === 'settings' && (
          <div style={{ backgroundColor: 'white', padding: '24px', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', maxWidth: '800px' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '16px' }}>Modem Settings</h3>
            {statusLoading ? (
              <LoadingSpinner text="Loading status..." />
            ) : statusError ? (
              <ErrorAlert error={statusError} />
            ) : (
              <div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
                  <div>
                    <label style={{ fontSize: '0.875rem', fontWeight: '500', color: '#6b7280' }}>Model</label>
                    <p style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{status?.model || 'N/A'}</p>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.875rem', fontWeight: '500', color: '#6b7280' }}>Firmware</label>
                    <p style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{status?.firmware || 'N/A'}</p>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.875rem', fontWeight: '500', color: '#6b7280' }}>Port</label>
                    <p style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{status?.port || 'N/A'}</p>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.875rem', fontWeight: '500', color: '#6b7280' }}>Status</label>
                    <p style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                      {status?.connected ? 'Connected' : 'Disconnected'}
                    </p>
                  </div>
                </div>
                
                {simInfo?.operator?.apn_settings && (
                  <div>
                    <h4 style={{ fontSize: '0.875rem', fontWeight: '500', marginBottom: '8px' }}>APN Settings</h4>
                    <div style={{ backgroundColor: '#f9fafb', padding: '12px', borderRadius: '8px' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.875rem' }}>
                        <div>
                          <span style={{ fontWeight: '500' }}>Name:</span> {simInfo.operator.apn_settings.name}
                        </div>
                        <div>
                          <span style={{ fontWeight: '500' }}>APN:</span> {simInfo.operator.apn_settings.apn}
                        </div>
                        <div>
                          <span style={{ fontWeight: '500' }}>Auth:</span> {simInfo.operator.apn_settings.auth_type}
                        </div>
                        <div>
                          <span style={{ fontWeight: '500' }}>Type:</span> {simInfo.operator.apn_settings.type}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
