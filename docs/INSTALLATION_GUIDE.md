# Guia de Instalação - FRP Bypass Professional

## 📋 Pré-requisitos

### Sistema Operacional
- **Windows**: 10/11 (64-bit)
- **Linux**: Ubuntu 20.04+, Debian 11+, CentOS 8+
- **macOS**: 10.15+ (Intel ou Apple Silicon)

### Software Necessário
- **Python**: 3.9 ou superior
- **Git**: Para clonagem do repositório (opcional)
- **Android SDK Platform Tools**: ADB e Fastboot

## 🚀 Instalação Rápida

### Método 1: Setup Automático (Recomendado)

```bash
# 1. Clone o repositório
git clone https://github.com/frp-bypass/professional.git
cd frp-software

# 2. Execute o setup automático
python setup.py install
```

### Método 2: Instalação Manual

```bash
# 1. Instale dependências Python
pip install -r requirements.txt

# 2. Configure ambiente
python setup.py demo

# 3. Teste instalação
python main.py test
```

## 📦 Instalação de Dependências por Sistema

### Windows

#### Python
1. Baixe Python 3.9+ de https://python.org
2. Durante instalação, marque "Add Python to PATH"
3. Verifique: `python --version`

#### Android SDK Platform Tools
1. Baixe de: https://developer.android.com/studio/releases/platform-tools
2. Extraia para `C:\platform-tools`
3. Adicione ao PATH do sistema:
   - Painel de Controle → Sistema → Configurações Avançadas
   - Variáveis de Ambiente → PATH → Adicionar `C:\platform-tools`
4. Verifique: `adb version` e `fastboot --version`

#### Drivers USB
- **Samsung**: Samsung USB Drivers
- **LG**: LG Mobile Switch
- **Xiaomi**: Mi USB Drivers
- **Universal**: Google USB Driver

### Linux (Ubuntu/Debian)

```bash
# Python e pip
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Android tools
sudo apt install android-tools-adb android-tools-fastboot

# Dependências de desenvolvimento
sudo apt install build-essential libusb-1.0-0-dev

# Regras udev para dispositivos Android
sudo apt install android-udev
sudo usermod -a -G plugdev $USER
```

### Linux (CentOS/RHEL)

```bash
# Python e pip
sudo dnf install python3 python3-pip

# Android tools
sudo dnf install android-tools

# Dependências
sudo dnf groupinstall "Development Tools"
sudo dnf install libusbx-devel
```

### macOS

```bash
# Homebrew (se não instalado)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python
brew install python@3.9

# Android tools
brew install android-platform-tools

# Dependências
brew install libusb
```

## 🔧 Configuração Avançada

### Configuração de Ambiente Virtual (Recomendado)

```bash
# Criar ambiente virtual
python -m venv frp-env

# Ativar ambiente virtual
# Windows:
frp-env\Scripts\activate
# Linux/macOS:
source frp-env/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### Configuração de Drivers USB (Windows)

1. **Modo de Desenvolvedor no Android**:
   - Configurações → Sobre o telefone
   - Toque 7x em "Número da compilação"
   - Configurações → Opções do desenvolvedor
   - Ative "Depuração USB"

2. **Instalação de Drivers**:
   - Conecte dispositivo
   - Gerenciador de Dispositivos
   - Instale driver apropriado

### Configuração de Permissões (Linux)

```bash
# Arquivo de regras udev
sudo nano /etc/udev/rules.d/51-android.rules

# Adicione (exemplo para Samsung):
SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", MODE="0666", GROUP="plugdev"

# Recarregue regras
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## ✅ Verificação da Instalação

### Teste Completo
```bash
python main.py test
```

### Testes Individuais

```bash
# Verificar Python e dependências
python --version
pip list

# Verificar Android tools
adb version
fastboot --version

# Testar detecção de dispositivos
python main.py detect

# Verificar base de dados
python main.py database
```

## 🔑 Configuração de Licença

### Licença de Demonstração
```bash
# Criar licença demo (válida por 365 dias)
python setup.py demo
```

### Licença Profissional
```bash
# Instalar licença comercial
python -c "from core.security import LicenseManager; lm = LicenseManager(); lm.install_license('YOUR-LICENSE-KEY', 'Your Name', 'Your Organization')"
```

## 📁 Estrutura de Diretórios Pós-Instalação

```
frp-software/
├── core/                    # Módulos principais
├── database/                # Base de dados de dispositivos
├── logs/                    # Logs de auditoria
├── temp/                    # Arquivos temporários
├── exports/                 # Dados exportados
├── backups/                 # Backups de dispositivos
├── license.key              # Arquivo de licença
├── config.json              # Configurações do sistema
└── main.py                  # Interface principal
```

## 🚨 Solução de Problemas

### Erro: "Python não encontrado"
```bash
# Windows: Reinstale Python marcando "Add to PATH"
# Linux: sudo apt install python3
# macOS: brew install python@3.9
```

### Erro: "ADB não encontrado"
```bash
# Instale Android SDK Platform Tools
# Adicione ao PATH do sistema
# Teste: adb version
```

### Erro: "Dispositivo não detectado"
```bash
# Verifique drivers USB
# Ative depuração USB no dispositivo
# Teste: adb devices
```

### Erro: "Permissão negada" (Linux)
```bash
sudo usermod -a -G plugdev $USER
# Faça logout/login
```

### Erro: "Licença inválida"
```bash
# Crie licença demo
python setup.py demo
# Ou instale licença válida
```

## 📞 Suporte

Se encontrar problemas durante a instalação:

1. **Verifique logs**: `logs/audit_YYYYMMDD.json`
2. **Execute diagnóstico**: `python main.py test --verbose`
3. **Consulte FAQ**: `docs/faq.md`
4. **Reporte bug**: GitHub Issues

## 🔄 Atualizações

### Atualização Manual
```bash
git pull origin main
pip install -r requirements.txt --upgrade
python setup.py check
```

### Verificar Versão
```bash
python main.py --version
```

## 🎯 Próximos Passos

Após instalação bem-sucedida:

1. **Leia a documentação**: `README.md`
2. **Execute tutorial**: `docs/tutorial.md`
3. **Teste com dispositivo**: `python main.py detect`
4. **Configure licença**: Se necessário
5. **Inicie bypass**: `python main.py bypass --help`

---

**Instalação concluída com sucesso! 🎉**
