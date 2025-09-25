# Instalação via PowerShell (irm) - FRP Bypass Professional

## 🚀 Instalação com Um Comando

### **Instalação Completa**
```powershell
# Execute no PowerShell como Administrador
irm https://raw.githubusercontent.com/frp-bypass/professional/main/install.ps1 | iex
```

### **Launcher GUI Rápido**
```powershell
# Para abrir apenas a interface gráfica
irm https://raw.githubusercontent.com/frp-bypass/professional/main/launch-gui.ps1 | iex
```

---

## 📋 O que Acontece Durante a Instalação

### **1. Verificação de Pré-requisitos** ✅
- Verifica Python 3.9+
- Verifica Node.js 16+ (para GUI)
- Verifica Git (opcional)
- Solicita privilégios de administrador se necessário

### **2. Download do Android SDK Platform Tools** 📱
- Baixa automaticamente ADB e Fastboot
- Configura no PATH do sistema
- Instala drivers necessários

### **3. Download do Projeto** 📥
- Clona repositório via Git (preferencial)
- Ou baixa ZIP como fallback
- Instala em `%LOCALAPPDATA%\FRPBypassPro`

### **4. Configuração Python** 🐍
- Cria ambiente virtual isolado
- Instala todas as dependências
- Configura cache e logs

### **5. Configuração GUI** 🎨
- Instala dependências Node.js
- Configura Electron + React
- Cria launchers automáticos

### **6. Criação de Atalhos** 🔗
- Atalho no Desktop para CLI
- Atalho no Desktop para GUI
- Comando global `frp-bypass`

### **7. Teste de Instalação** 🧪
- Executa testes automáticos
- Verifica conectividade
- Valida configuração

---

## 🎯 Comandos Disponíveis Após Instalação

### **Via Linha de Comando**
```powershell
# Comando global (disponível em qualquer lugar)
frp-bypass detect
frp-bypass bypass
frp-bypass test

# Ou diretamente no diretório
cd "$env:LOCALAPPDATA\FRPBypassPro"
python main.py detect
```

### **Via Interface Gráfica**
```powershell
# Launcher rápido
irm https://raw.githubusercontent.com/frp-bypass/professional/main/launch-gui.ps1 | iex

# Ou pelo atalho no Desktop
# "FRP Bypass Professional (GUI)"
```

---

## ⚙️ Opções de Instalação Avançada

### **Instalação Personalizada**
```powershell
# Baixar script primeiro
$script = irm https://raw.githubusercontent.com/frp-bypass/professional/main/install.ps1

# Executar com parâmetros
& ([scriptblock]::Create($script)) -InstallPath "C:\MeuDiretorio" -SkipGUI
```

### **Parâmetros Disponíveis**
- `-InstallPath`: Diretório de instalação customizado
- `-SkipGUI`: Pula instalação da interface gráfica
- `-DevMode`: Modo desenvolvedor (sem admin)
- `-Uninstall`: Remove instalação

### **Exemplos**
```powershell
# Instalação sem GUI
irm https://raw.githubusercontent.com/frp-bypass/professional/main/install.ps1 | iex -SkipGUI

# Instalação em diretório específico
$script = irm https://raw.githubusercontent.com/frp-bypass/professional/main/install.ps1
& ([scriptblock]::Create($script)) -InstallPath "D:\FRPBypass"

# Desinstalação
$script = irm https://raw.githubusercontent.com/frp-bypass/professional/main/install.ps1
& ([scriptblock]::Create($script)) -Uninstall
```

---

## 🔧 Solução de Problemas

### **Erro: "Execution Policy"**
```powershell
# Temporariamente
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Ou execute diretamente
powershell -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/frp-bypass/professional/main/install.ps1 | iex"
```

### **Erro: "Não é possível resolver o nome do host"**
```powershell
# Verifique conexão com internet
Test-NetConnection github.com -Port 443

# Ou use proxy se necessário
$webClient = New-Object System.Net.WebClient
$webClient.Proxy = [System.Net.WebRequest]::DefaultWebProxy
$webClient.Proxy.Credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials
```

### **Erro: "Acesso negado"**
```powershell
# Execute como Administrador
# Botão direito no PowerShell > "Executar como administrador"

# Ou via comando
Start-Process PowerShell -Verb RunAs -ArgumentList "-Command irm https://raw.githubusercontent.com/frp-bypass/professional/main/install.ps1 | iex"
```

### **Python/Node.js não encontrado**
```powershell
# Instalar Python
winget install Python.Python.3.11

# Instalar Node.js
winget install OpenJS.NodeJS

# Ou baixar manualmente:
# Python: https://python.org
# Node.js: https://nodejs.org
```

---

## 🌐 URLs de Instalação

### **Instalação Completa**
```
https://raw.githubusercontent.com/frp-bypass/professional/main/install.ps1
```

### **Launcher GUI**
```
https://raw.githubusercontent.com/frp-bypass/professional/main/launch-gui.ps1
```

### **Comando Curto (via bit.ly ou similar)**
```powershell
# Versão curta (se disponível)
irm bit.ly/frp-bypass-install | iex
irm bit.ly/frp-bypass-gui | iex
```

---

## 📱 Integração com Sistema

### **Variáveis de Ambiente Criadas**
- `PATH`: Inclui `%LOCALAPPDATA%\FRPBypassPro\bin`
- `PATH`: Inclui `%LOCALAPPDATA%\FRPBypassPro\platform-tools`

### **Arquivos Criados**
```
%LOCALAPPDATA%\FRPBypassPro\
├── main.py                 # CLI principal
├── core\                   # Módulos Python
├── gui\                    # Interface React/Electron
├── platform-tools\        # ADB/Fastboot
├── venv\                   # Ambiente Python
├── bin\frp-bypass.cmd     # Comando global
└── logs\                   # Logs de auditoria
```

### **Atalhos no Desktop**
- `FRP Bypass Professional.lnk` - Interface CLI
- `FRP Bypass Professional (GUI).lnk` - Interface gráfica

---

## 🔄 Atualizações

### **Atualização Automática**
```powershell
# Re-executar instalação (sobrescreve)
irm https://raw.githubusercontent.com/frp-bypass/professional/main/install.ps1 | iex
```

### **Atualização Manual**
```powershell
cd "$env:LOCALAPPDATA\FRPBypassPro"
git pull origin main
.\venv\Scripts\activate
pip install -r requirements.txt --upgrade
cd gui
npm update
```

---

## 🆘 Suporte

### **Logs de Instalação**
```powershell
# Verificar logs do PowerShell
Get-WinEvent -LogName "Windows PowerShell" | Where-Object {$_.Message -like "*frp-bypass*"}
```

### **Diagnóstico**
```powershell
# Após instalação, execute
frp-bypass test

# Ou
cd "$env:LOCALAPPDATA\FRPBypassPro"
python main.py test
```

### **Contato**
- 🐛 **Issues**: https://github.com/frp-bypass/professional/issues
- 📧 **Email**: support@frp-bypass-professional.com
- 💬 **Discord**: https://discord.gg/frp-bypass-pro

---

## ⚖️ Conformidade

### **Uso Legal**
- ✅ Use apenas em dispositivos próprios
- ✅ Obtenha autorização expressa quando necessário
- ✅ Respeite leis locais e internacionais
- ✅ Mantenha logs para auditoria

### **Disclaimer**
O instalador automaticamente:
- Apresenta termos de uso
- Registra instalação em logs
- Configura sistema de auditoria
- Solicita aceitação de responsabilidade

---

**🚀 Pronto para usar! Execute o comando e tenha o FRP Bypass Professional funcionando em minutos!**
