import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Button,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  PhoneAndroid,
  Security,
  Speed,
  Assessment,
  Refresh,
  PlayArrow,
  Warning
} from '@mui/icons-material';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Dashboard = ({ appConfig, onShowNotification }) => {
  const [systemStats, setSystemStats] = useState(null);
  const [connectedDevices, setConnectedDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    loadDashboardData();
    
    // Auto-refresh a cada 30 segundos
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Carrega estatísticas do sistema
      const statsResult = await window.electronAPI.getSystemStats();
      if (statsResult.success) {
        setSystemStats(statsResult.data);
      }
      
      // Detecta dispositivos conectados
      const devicesResult = await window.electronAPI.detectDevices();
      if (devicesResult.success) {
        setConnectedDevices(devicesResult.devices || []);
      }
      
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      onShowNotification('Erro ao carregar dados do dashboard', 'error');
    } finally {
      setLoading(false);
    }
  };

  const runQuickTest = async () => {
    try {
      onShowNotification('Executando teste rápido do sistema...', 'info');
      
      const result = await window.electronAPI.runSystemTest();
      
      if (result.success) {
        onShowNotification('Teste do sistema concluído com sucesso', 'success');
      } else {
        onShowNotification('Teste do sistema falhou: ' + result.error, 'error');
      }
    } catch (error) {
      console.error('Error running system test:', error);
      onShowNotification('Erro ao executar teste do sistema', 'error');
    }
  };

  // Dados para gráficos
  const deviceStatusData = connectedDevices.reduce((acc, device) => {
    const status = device.frp_locked ? 'FRP Bloqueado' : 'FRP Livre';
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {});

  const pieData = Object.entries(deviceStatusData).map(([key, value]) => ({
    name: key,
    value: value
  }));

  const manufacturerData = connectedDevices.reduce((acc, device) => {
    const manufacturer = device.manufacturer.toUpperCase();
    acc[manufacturer] = (acc[manufacturer] || 0) + 1;
    return acc;
  }, {});

  const barData = Object.entries(manufacturerData).map(([key, value]) => ({
    manufacturer: key,
    count: value
  }));

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadDashboardData}
            disabled={loading}
            sx={{ mr: 1 }}
          >
            Atualizar
          </Button>
          <Button
            variant="contained"
            startIcon={<PlayArrow />}
            onClick={runQuickTest}
            color="secondary"
          >
            Teste Rápido
          </Button>
        </Box>
      </Box>

      {/* Status Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <PhoneAndroid color="primary" sx={{ fontSize: 40, mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Dispositivos Conectados
                  </Typography>
                  <Typography variant="h4">
                    {connectedDevices.length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Security color="error" sx={{ fontSize: 40, mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    FRP Bloqueados
                  </Typography>
                  <Typography variant="h4">
                    {connectedDevices.filter(d => d.frp_locked).length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Speed color="success" sx={{ fontSize: 40, mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Taxa de Sucesso
                  </Typography>
                  <Typography variant="h4">
                    {systemStats?.average_success_rate || 0}%
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Assessment color="info" sx={{ fontSize: 40, mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Dispositivos Suportados
                  </Typography>
                  <Typography variant="h4">
                    {systemStats?.total_devices || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Dispositivos Conectados */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '400px' }}>
            <Typography variant="h6" gutterBottom>
              Dispositivos Conectados
            </Typography>
            
            {loading ? (
              <Box display="flex" justifyContent="center" alignItems="center" height="300px">
                <CircularProgress />
              </Box>
            ) : connectedDevices.length === 0 ? (
              <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" height="300px">
                <PhoneAndroid sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                <Typography color="textSecondary" align="center">
                  Nenhum dispositivo conectado
                </Typography>
                <Typography variant="body2" color="textSecondary" align="center" mt={1}>
                  Conecte um dispositivo Android via USB
                </Typography>
              </Box>
            ) : (
              <Box sx={{ maxHeight: '320px', overflow: 'auto' }}>
                {connectedDevices.map((device, index) => (
                  <Card key={index} sx={{ mb: 1 }}>
                    <CardContent sx={{ py: 1 }}>
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Box>
                          <Typography variant="subtitle2">
                            {device.manufacturer.toUpperCase()} {device.model}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            Serial: {device.serial}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            Android: {device.android_version || 'N/A'} | Modo: {device.mode}
                          </Typography>
                        </Box>
                        <Box>
                          <Chip
                            label={device.frp_locked ? 'FRP Bloqueado' : 'FRP Livre'}
                            color={device.frp_locked ? 'error' : 'success'}
                            size="small"
                            sx={{ mb: 1 }}
                          />
                          <br />
                          <Chip
                            label={device.is_frp_bypassable ? 'Bypass Possível' : 'Bypass Não Possível'}
                            color={device.is_frp_bypassable ? 'info' : 'default'}
                            size="small"
                          />
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Status FRP - Gráfico Pizza */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '400px' }}>
            <Typography variant="h6" gutterBottom>
              Status FRP dos Dispositivos
            </Typography>
            
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="90%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Box display="flex" justifyContent="center" alignItems="center" height="300px">
                <Typography color="textSecondary">
                  Nenhum dispositivo para exibir
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Fabricantes - Gráfico Barras */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '300px' }}>
            <Typography variant="h6" gutterBottom>
              Dispositivos por Fabricante
            </Typography>
            
            {barData.length > 0 ? (
              <ResponsiveContainer width="100%" height="90%">
                <BarChart data={barData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="manufacturer" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#1976d2" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Box display="flex" justifyContent="center" alignItems="center" height="200px">
                <Typography color="textSecondary">
                  Nenhum dispositivo para exibir
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Informações do Sistema */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '300px' }}>
            <Typography variant="h6" gutterBottom>
              Informações do Sistema
            </Typography>
            
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Versão da Aplicação
              </Typography>
              <Typography variant="body1" gutterBottom>
                {appConfig?.version || 'N/A'}
              </Typography>

              <Typography variant="body2" color="textSecondary" gutterBottom sx={{ mt: 2 }}>
                Plataforma
              </Typography>
              <Typography variant="body1" gutterBottom>
                {appConfig?.platform || 'N/A'}
              </Typography>

              <Typography variant="body2" color="textSecondary" gutterBottom sx={{ mt: 2 }}>
                Base de Dados
              </Typography>
              <Typography variant="body1" gutterBottom>
                {systemStats?.total_devices || 0} dispositivos, {systemStats?.manufacturers || 0} fabricantes
              </Typography>

              <Typography variant="body2" color="textSecondary" gutterBottom sx={{ mt: 2 }}>
                Última Atualização
              </Typography>
              <Typography variant="body1">
                {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Nunca'}
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Avisos e Status */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Status e Avisos
            </Typography>
            
            <Box sx={{ mt: 2 }}>
              <Alert severity="info" sx={{ mb: 1 }}>
                Sistema funcionando normalmente. {connectedDevices.length} dispositivo(s) detectado(s).
              </Alert>
              
              {connectedDevices.some(d => d.frp_locked) && (
                <Alert severity="warning" icon={<Warning />} sx={{ mb: 1 }}>
                  {connectedDevices.filter(d => d.frp_locked).length} dispositivo(s) com FRP ativo detectado(s).
                  Certifique-se de ter autorização antes de prosseguir com o bypass.
                </Alert>
              )}
              
              {systemStats && systemStats.average_success_rate < 70 && (
                <Alert severity="error" sx={{ mb: 1 }}>
                  Taxa de sucesso abaixo do esperado ({systemStats.average_success_rate}%). 
                  Verifique a base de dados e métodos de bypass.
                </Alert>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
