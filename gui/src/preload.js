const { contextBridge, ipcRenderer } = require('electron');

// Expõe APIs seguras para o renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  // Configuração da aplicação
  getAppConfig: () => ipcRenderer.invoke('get-app-config'),
  saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
  getSettings: () => ipcRenderer.invoke('get-settings'),
  
  // Operações de arquivo
  selectFile: (options) => ipcRenderer.invoke('select-file', options),
  selectDirectory: () => ipcRenderer.invoke('select-directory'),
  saveFile: (options) => ipcRenderer.invoke('save-file', options),
  showItemInFolder: (path) => ipcRenderer.invoke('show-item-in-folder', path),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  
  // Comandos Python/FRP
  detectDevices: () => ipcRenderer.invoke('detect-devices'),
  getDeviceInfo: (serial) => ipcRenderer.invoke('get-device-info', serial),
  startBypass: (options) => ipcRenderer.invoke('start-bypass', options),
  getSystemStats: () => ipcRenderer.invoke('get-system-stats'),
  runSystemTest: () => ipcRenderer.invoke('run-system-test'),
  getLogs: (options) => ipcRenderer.invoke('get-logs', options),
  exportData: (data, filePath) => ipcRenderer.invoke('export-data', data, filePath),
  
  // Listeners para eventos
  onPythonLog: (callback) => {
    ipcRenderer.on('python-log', (event, data) => callback(data));
  },
  
  onPythonStatus: (callback) => {
    ipcRenderer.on('python-status', (event, data) => callback(data));
  },
  
  onShowNotification: (callback) => {
    ipcRenderer.on('show-notification', (event, data) => callback(data));
  },
  
  // Remove listeners
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  }
});

// Log de inicialização
console.log('Preload script loaded successfully');
