const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const Store = require('electron-store');

// Configuração da store
const store = new Store();

// Variáveis globais
let mainWindow;
let pythonProcess;
let isDev = process.env.NODE_ENV === 'development';

// Configuração de segurança
process.env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = 'true';

function createWindow() {
  // Cria a janela principal
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 1000,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(
      __dirname,
      '../assets',
      process.platform === 'win32' ? 'icon.ico' : (process.platform === 'darwin' ? 'icon.icns' : 'icon.png')
    ),
    titleBarStyle: 'default',
    show: false // NÃ£o mostra atÃ© estar pronta
  });

  // Carrega a aplicação React
  const startUrl = isDev 
    ? 'http://localhost:3000' 
    : `file://${path.join(__dirname, '../build/index.html')}`;
  
  mainWindow.loadURL(startUrl);

  // Mostra janela quando pronta
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Abre DevTools em desenvolvimento
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  // Manipula fechamento da janela
  mainWindow.on('closed', () => {
    mainWindow = null;
    // Mata processo Python se existir
    if (pythonProcess) {
      pythonProcess.kill();
    }
  });

  // Previne navegação externa
  mainWindow.webContents.on('will-navigate', (event, navigationUrl) => {
    const parsedUrl = new URL(navigationUrl);
    
    if (parsedUrl.origin !== startUrl) {
      event.preventDefault();
    }
  });

  // Manipula links externos
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

// Inicialização do Electron
app.whenReady().then(() => {
  createWindow();
  
  // Inicializa backend Python
  initializePythonBackend();
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  // Limpa recursos
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

// Inicializa backend Python
function initializePythonBackend() {
  const pythonPath = isDev ? 'python' : path.join(process.resourcesPath, 'python', 'python.exe');
  const scriptPath = isDev 
    ? path.join(__dirname, '../../main.py')
    : path.join(process.resourcesPath, 'main.py');
  
  // Inicia servidor Python em modo API
  pythonProcess = spawn(pythonPath, [scriptPath, '--api-mode'], {
    stdio: ['pipe', 'pipe', 'pipe']
  });
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python stdout: ${data}`);
    // Envia logs para o frontend
    if (mainWindow) {
      mainWindow.webContents.send('python-log', {
        type: 'stdout',
        message: data.toString()
      });
    }
  });
  
  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python stderr: ${data}`);
    if (mainWindow) {
      mainWindow.webContents.send('python-log', {
        type: 'stderr',
        message: data.toString()
      });
    }
  });
  
  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
    if (mainWindow) {
      mainWindow.webContents.send('python-status', {
        status: 'disconnected',
        code: code
      });
    }
  });
}

// IPC Handlers

// Configurações da aplicação
ipcMain.handle('get-app-config', () => {
  return {
    version: app.getVersion(),
    platform: process.platform,
    isDev: isDev,
    userDataPath: app.getPath('userData'),
    settings: store.store
  };
});

ipcMain.handle('save-settings', (event, settings) => {
  try {
    store.set('settings', settings);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-settings', () => {
  return store.get('settings', {
    theme: 'dark',
    autoScan: true,
    notifications: true,
    logLevel: 'info'
  });
});

// Operações de arquivo
ipcMain.handle('select-file', async (event, options) => {
  try {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openFile'],
      filters: options?.filters || []
    });
    
    return result;
  } catch (error) {
    return { canceled: true, error: error.message };
  }
});

ipcMain.handle('select-directory', async () => {
  try {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openDirectory']
    });
    
    return result;
  } catch (error) {
    return { canceled: true, error: error.message };
  }
});

ipcMain.handle('save-file', async (event, options) => {
  try {
    const result = await dialog.showSaveDialog(mainWindow, {
      defaultPath: options?.defaultPath || 'export.json',
      filters: options?.filters || [
        { name: 'JSON Files', extensions: ['json'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    });
    
    return result;
  } catch (error) {
    return { canceled: true, error: error.message };
  }
});

// Operações do sistema
ipcMain.handle('show-item-in-folder', (event, fullPath) => {
  shell.showItemInFolder(fullPath);
});

ipcMain.handle('open-external', (event, url) => {
  shell.openExternal(url);
});

// Comandos Python
ipcMain.handle('python-command', async (event, command, args = []) => {
  return new Promise((resolve, reject) => {
    const pythonPath = isDev ? 'python' : path.join(process.resourcesPath, 'python', 'python.exe');
    const scriptPath = isDev 
      ? path.join(__dirname, '../../main.py')
      : path.join(process.resourcesPath, 'main.py');
    
    const fullArgs = [scriptPath, command, ...args];
    const process = spawn(pythonPath, fullArgs);
    
    let stdout = '';
    let stderr = '';
    
    process.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    process.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    process.on('close', (code) => {
      if (code === 0) {
        try {
          // Tenta parsear JSON se possível
          const result = JSON.parse(stdout);
          resolve(result);
        } catch {
          resolve({ output: stdout, success: true });
        }
      } else {
        reject({ error: stderr, code: code, success: false });
      }
    });
    
    process.on('error', (error) => {
      reject({ error: error.message, success: false });
    });
  });
});

// Detecção de dispositivos
ipcMain.handle('detect-devices', async () => {
  try {
    const result = await ipcMain.emit('python-command', null, 'detect', ['--json']);
    return result;
  } catch (error) {
    return { success: false, error: error.message, devices: [] };
  }
});

// Informações do dispositivo
ipcMain.handle('get-device-info', async (event, serial) => {
  try {
    const result = await ipcMain.emit('python-command', null, 'info', ['--serial', serial, '--json']);
    return result;
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Bypass FRP
ipcMain.handle('start-bypass', async (event, options) => {
  try {
    const args = [];
    
    if (options.serial) {
      args.push('--serial', options.serial);
    }
    
    if (options.method) {
      args.push('--method', options.method);
    }
    
    if (options.dryRun) {
      args.push('--dry-run');
    }
    
    args.push('--json');
    
    const result = await ipcMain.emit('python-command', null, 'bypass', args);
    return result;
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Estatísticas do sistema
ipcMain.handle('get-system-stats', async () => {
  try {
    const result = await ipcMain.emit('python-command', null, 'database', ['--json']);
    return result;
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Testes do sistema
ipcMain.handle('run-system-test', async () => {
  try {
    const result = await ipcMain.emit('python-command', null, 'test', ['--json']);
    return result;
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Logs da aplicação
ipcMain.handle('get-logs', async (event, options = {}) => {
  try {
    const logsDir = path.join(app.getPath('userData'), 'logs');
    
    if (!fs.existsSync(logsDir)) {
      return { success: false, error: 'Logs directory not found' };
    }
    
    const logFiles = fs.readdirSync(logsDir)
      .filter(file => file.endsWith('.json'))
      .sort()
      .reverse(); // Mais recentes primeiro
    
    const logs = [];
    const maxFiles = options.maxFiles || 5;
    
    for (let i = 0; i < Math.min(logFiles.length, maxFiles); i++) {
      const filePath = path.join(logsDir, logFiles[i]);
      try {
        const content = fs.readFileSync(filePath, 'utf8');
        const entries = JSON.parse(content);
        logs.push(...entries);
      } catch (error) {
        console.error(`Error reading log file ${logFiles[i]}:`, error);
      }
    }
    
    return {
      success: true,
      logs: logs.slice(0, options.maxEntries || 1000)
    };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Exportar dados
ipcMain.handle('export-data', async (event, data, filePath) => {
  try {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Notificações do sistema
function showNotification(title, body, type = 'info') {
  if (mainWindow) {
    mainWindow.webContents.send('show-notification', {
      title,
      body,
      type
    });
  }
}

// Exporta função para uso em outros módulos
module.exports = { showNotification };
