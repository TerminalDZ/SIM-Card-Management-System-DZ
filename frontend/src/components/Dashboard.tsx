import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { useApi, useApiCall, useWebSocket } from '../hooks/useApi';
import { ModemStatus, SimInfo, SmsMessage, BalanceResponse } from '../types';
import { 
  Signal, 
  Smartphone, 
  MessageSquare, 
  Send, 
  Trash2, 
  DollarSign, 
  RefreshCw,
  Wifi,
  Phone,
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react';

export default function Dashboard() {
  const [selectedTab, setSelectedTab] = useState('overview');
  const [newSms, setNewSms] = useState({ phone: '', message: '' });
  const [ussdCommand, setUssdCommand] = useState('');
  
  // API hooks
  const { data: status, loading: statusLoading, error: statusError, refetch: refetchStatus } = useApi<ModemStatus>('/status');
  const { data: simInfo, loading: simLoading, error: simError, refetch: refetchSimInfo } = useApi<SimInfo>('/sim-info');
  const { data: smsData, loading: smsLoading, error: smsError, refetch: refetchSms } = useApi<{messages: SmsMessage[]}>('/sms');
  const { call, loading: apiLoading, error: apiError } = useApiCall();

  // WebSocket for real-time updates
  useWebSocket('ws://localhost:8000/ws', (data) => {
    if (data.type === 'status_update') {
      refetchStatus();
    } else if (data.type === 'sms_sent' || data.type === 'sms_deleted') {
      refetchSms();
    }
  });

  const handleSendSms = async () => {
    if (!newSms.phone || !newSms.message) return;
    
    try {
      await call('POST', '/sms/send', {
        phone_number: newSms.phone,
        message: newSms.message
      });
      setNewSms({ phone: '', message: '' });
      refetchSms();
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

  const handleSendUssd = async () => {
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

  const getNetworkTypeColor = (type?: string) => {
    switch (type) {
      case 'LTE': return 'bg-green-500';
      case 'UMTS': return 'bg-blue-500';
      case 'GSM': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  const getSignalStrengthColor = (strength?: number) => {
    if (!strength) return 'bg-gray-500';
    if (strength >= 75) return 'bg-green-500';
    if (strength >= 50) return 'bg-yellow-500';
    if (strength >= 25) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  if (statusLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            SIM Card Management System
          </h1>
          <p className="text-gray-600">
            Professional control panel for Algerian mobile operators
          </p>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {/* Connection Status */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Connection</CardTitle>
              <Wifi className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                {status?.connected ? (
                  <>
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span className="text-sm font-medium text-green-700">Connected</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-4 w-4 text-red-500" />
                    <span className="text-sm font-medium text-red-700">Disconnected</span>
                  </>
                )}
              </div>
              {status?.port && (
                <p className="text-xs text-muted-foreground mt-1">Port: {status.port}</p>
              )}
            </CardContent>
          </Card>

          {/* Signal Strength */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Signal</CardTitle>
              <Signal className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold">
                  {simInfo?.signal_strength || 0}%
                </span>
              </div>
              <Progress 
                value={simInfo?.signal_strength || 0} 
                className={`mt-2 ${getSignalStrengthColor(simInfo?.signal_strength)}`}
              />
            </CardContent>
          </Card>

          {/* Network Type */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Network</CardTitle>
              <Smartphone className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <Badge className={getNetworkTypeColor(simInfo?.network_type)}>
                {simInfo?.network_type || 'Unknown'}
              </Badge>
              {simInfo?.network_operator && (
                <p className="text-xs text-muted-foreground mt-1">
                  {simInfo.network_operator}
                </p>
              )}
            </CardContent>
          </Card>

          {/* Operator */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Operator</CardTitle>
              <Phone className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-lg font-semibold">
                {simInfo?.operator?.name || 'Unknown'}
              </div>
              {simInfo?.msisdn && (
                <p className="text-xs text-muted-foreground">
                  {simInfo.msisdn}
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="sms">SMS</TabsTrigger>
            <TabsTrigger value="ussd">USSD</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* SIM Information */}
              <Card>
                <CardHeader>
                  <CardTitle>SIM Information</CardTitle>
                  <CardDescription>Detailed SIM card information</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {simLoading ? (
                    <div className="flex items-center space-x-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Loading SIM info...</span>
                    </div>
                  ) : simError ? (
                    <div className="text-red-600">{simError}</div>
                  ) : (
                    <div className="space-y-2">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm font-medium text-gray-500">IMSI</label>
                          <p className="font-mono text-sm">{simInfo?.imsi || 'N/A'}</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-gray-500">ICCID</label>
                          <p className="font-mono text-sm">{simInfo?.iccid || 'N/A'}</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-gray-500">IMEI</label>
                          <p className="font-mono text-sm">{simInfo?.imei || 'N/A'}</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-gray-500">Phone Number</label>
                          <p className="font-mono text-sm">{simInfo?.msisdn || 'N/A'}</p>
                        </div>
                      </div>
                    </div>
                  )}
                  <Button onClick={refetchSimInfo} variant="outline" size="sm">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh
                  </Button>
                </CardContent>
              </Card>

              {/* Quick Actions */}
              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                  <CardDescription>Common operations and balance check</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Button 
                    onClick={handleCheckBalance} 
                    disabled={apiLoading}
                    className="w-full"
                  >
                    <DollarSign className="h-4 w-4 mr-2" />
                    Check Balance
                  </Button>
                  
                  {simInfo?.operator?.common_services && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium">Common Services</h4>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(simInfo.operator.common_services).map(([key, code]) => (
                          <Button
                            key={key}
                            variant="outline"
                            size="sm"
                            onClick={() => setUssdCommand(code)}
                            className="text-xs"
                          >
                            {key.replace('_', ' ').toUpperCase()}
                          </Button>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* SMS Tab */}
          <TabsContent value="sms" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Send SMS */}
              <Card>
                <CardHeader>
                  <CardTitle>Send SMS</CardTitle>
                  <CardDescription>Send a new text message</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Phone Number</label>
                    <Input
                      placeholder="e.g., 0555123456"
                      value={newSms.phone}
                      onChange={(e) => setNewSms(prev => ({ ...prev, phone: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Message</label>
                    <Textarea
                      placeholder="Type your message here..."
                      value={newSms.message}
                      onChange={(e) => setNewSms(prev => ({ ...prev, message: e.target.value }))}
                      rows={4}
                    />
                  </div>
                  <Button 
                    onClick={handleSendSms}
                    disabled={apiLoading || !newSms.phone || !newSms.message}
                    className="w-full"
                  >
                    <Send className="h-4 w-4 mr-2" />
                    Send SMS
                  </Button>
                </CardContent>
              </Card>

              {/* SMS Inbox */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>SMS Inbox</CardTitle>
                    <CardDescription>Received and sent messages</CardDescription>
                  </div>
                  <Button onClick={refetchSms} variant="outline" size="sm">
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </CardHeader>
                <CardContent>
                  {smsLoading ? (
                    <div className="flex items-center space-x-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Loading messages...</span>
                    </div>
                  ) : smsError ? (
                    <div className="text-red-600">{smsError}</div>
                  ) : (
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {smsData?.messages?.length ? (
                        smsData.messages.map((msg) => (
                          <div key={msg.id} className="border rounded-lg p-3">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center space-x-2">
                                <Badge variant={msg.status.includes('REC') ? 'default' : 'secondary'}>
                                  {msg.status}
                                </Badge>
                                <span className="text-sm font-medium">{msg.phone_number}</span>
                              </div>
                              <Button
                                onClick={() => handleDeleteSms(msg.id)}
                                variant="outline"
                                size="sm"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                            <p className="text-sm mb-2">{msg.message}</p>
                            <p className="text-xs text-gray-500">{formatTimestamp(msg.timestamp)}</p>
                          </div>
                        ))
                      ) : (
                        <div className="text-center text-gray-500 py-8">
                          <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                          <p>No messages found</p>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* USSD Tab */}
          <TabsContent value="ussd" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>USSD Commands</CardTitle>
                <CardDescription>Send USSD codes for various services</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium">USSD Command</label>
                  <div className="flex space-x-2">
                    <Input
                      placeholder="e.g., *100#"
                      value={ussdCommand}
                      onChange={(e) => setUssdCommand(e.target.value)}
                    />
                    <Button 
                      onClick={handleSendUssd}
                      disabled={apiLoading || !ussdCommand}
                    >
                      Send
                    </Button>
                  </div>
                </div>
                
                {apiError && (
                  <div className="text-red-600 text-sm">{apiError}</div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Modem Settings</CardTitle>
                <CardDescription>Modem and connection information</CardDescription>
              </CardHeader>
              <CardContent>
                {statusLoading ? (
                  <div className="flex items-center space-x-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Loading status...</span>
                  </div>
                ) : statusError ? (
                  <div className="text-red-600">{statusError}</div>
                ) : (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-gray-500">Model</label>
                        <p className="font-mono text-sm">{status?.model || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">Firmware</label>
                        <p className="font-mono text-sm">{status?.firmware || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">Port</label>
                        <p className="font-mono text-sm">{status?.port || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">Status</label>
                        <p className="font-mono text-sm">
                          {status?.connected ? 'Connected' : 'Disconnected'}
                        </p>
                      </div>
                    </div>
                    
                    {simInfo?.operator?.apn_settings && (
                      <div className="mt-6">
                        <h4 className="text-sm font-medium mb-2">APN Settings</h4>
                        <div className="bg-gray-50 p-3 rounded-lg">
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            <div>
                              <span className="font-medium">Name:</span> {simInfo.operator.apn_settings.name}
                            </div>
                            <div>
                              <span className="font-medium">APN:</span> {simInfo.operator.apn_settings.apn}
                            </div>
                            <div>
                              <span className="font-medium">Auth:</span> {simInfo.operator.apn_settings.auth_type}
                            </div>
                            <div>
                              <span className="font-medium">Type:</span> {simInfo.operator.apn_settings.type}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
