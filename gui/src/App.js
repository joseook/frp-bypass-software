import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, Alert, Snackbar } from '@mui/material';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import DeviceManager from './components/DeviceManager';
import BypassManager from './components/BypassManager';
import SystemStats from './components/SystemStats';
import Settings from './components/Settings';
import Logs from './components/Logs';
import About from './components/About';
import './App.css';

function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [notification, setNotification] = useState(null);
  const [appConfig, setAppConfig] = useState(null);
  const [pythonStatus, setPythonStatus] = useState('connecting');

  // Tema Material-UI
  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
      primary: {
        main: '#1976d2',
      },
      secondary: {
        main: '#dc004e',
      },
      background: {
        default: darkMode ? '#121212' : '#fafafa',
        paper: darkMode ? '#1e1e1e' : '#ffffff',
      },
    },
    typography: {
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
          },
        },
      },
    },
  });

  // Inicialização
  useEffect(() => {
    initializeApp();
    setupEventListeners();
    
    return () => {
      // Cleanup listeners
      if (window.electronAPI) {
        window.electronAPI.removeAllListeners('python-log');
        window.electronAPI.removeAllListeners('python-status');
        window.electronAPI.removeAllListeners('show-notification');
      }
    };
  }, []);

  const initializeApp = async () => {
    try {
      // Carrega configuração da aplicação
      const config = await window.electronAPI.getAppConfig();
      setAppConfig(config);

      // Carrega configurações do usuário
      const settings = await window.electronAPI.getSettings();
      setDarkMode(settings.theme === 'dark');
    } catch (error) {
      console.error('Error initializing app:', error);
      showNotification('Erro ao inicializar aplicação', 'error');
    }
  };

  const setupEventListeners = () => {
    if (!window.electronAPI) return;

    // Listener para logs do Python
    window.electronAPI.onPythonLog((data) => {
      console.log('Python log:', data);
      // Aqui você pode processar os logs conforme necessário
    });

    // Listener para status do Python
    window.electronAPI.onPythonStatus((data) => {
      console.log('Python status:', data);
      setPythonStatus(data.status);
      
      if (data.status === 'disconnected') {
        showNotification('Conexão com backend perdida', 'error');
      }
    });

    // Listener para notificações
    window.electronAPI.onShowNotification((data) => {
      showNotification(data.body, data.type, data.title);
    });
  };

  const showNotification = (message, type = 'info', title = '') => {
    setNotification({
      message: title ? `${title}: ${message}` : message,
      type: type,
      open: true
    });
  };

  const handleCloseNotification = () => {
    setNotification(prev => prev ? { ...prev, open: false } : null);
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const toggleTheme = async () => {
    const newDarkMode = !darkMode;
    setDarkMode(newDarkMode);
    
    try {
      const settings = await window.electronAPI.getSettings();
      await window.electronAPI.saveSettings({
        ...settings,
        theme: newDarkMode ? 'dark' : 'light'
      });
    } catch (error) {
      console.error('Error saving theme setting:', error);
    }
  };

  // Verifica se está rodando no Electron
  if (!window.electronAPI) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        backgroundColor: '#f5f5f5'
      }}>
        <Alert severity="warning">
          Esta aplicação deve ser executada no Electron. 
          Execute `npm start` no diretório gui/ para iniciar corretamente.
        </Alert>
      </div>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', height: '100vh' }}>
          <Sidebar 
            open={sidebarOpen}
            onToggle={toggleSidebar}
            darkMode={darkMode}
            onToggleTheme={toggleTheme}
            pythonStatus={pythonStatus}
          />
          
          <Box 
            component="main" 
            sx={{ 
              flexGrow: 1, 
              p: 3,
              marginLeft: sidebarOpen ? '240px' : '60px',
              transition: theme.transitions.create('margin', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.leavingScreen,
              }),
              overflow: 'auto'
            }}
          >
            <Routes>
              <Route path="/" element={
                <Dashboard 
                  appConfig={appConfig}
                  onShowNotification={showNotification}
                />
              } />
              <Route path="/devices" element={
                <DeviceManager onShowNotification={showNotification} />
              } />
              <Route path="/bypass" element={
                <BypassManager onShowNotification={showNotification} />
              } />
              <Route path="/stats" element={
                <SystemStats onShowNotification={showNotification} />
              } />
              <Route path="/logs" element={
                <Logs onShowNotification={showNotification} />
              } />
              <Route path="/settings" element={
                <Settings 
                  onShowNotification={showNotification}
                  darkMode={darkMode}
                  onToggleTheme={toggleTheme}
                />
              } />
              <Route path="/about" element={
                <About appConfig={appConfig} />
              } />
            </Routes>
          </Box>
        </Box>

        {/* Notificações */}
        <Snackbar
          open={notification?.open || false}
          autoHideDuration={6000}
          onClose={handleCloseNotification}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert 
            onClose={handleCloseNotification} 
            severity={notification?.type || 'info'}
            variant="filled"
            sx={{ width: '100%' }}
          >
            {notification?.message}
          </Alert>
        </Snackbar>
      </Router>
    </ThemeProvider>
  );
}

export default App;
