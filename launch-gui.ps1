# FRP Bypass Professional - GUI Quick Launcher
# Execução rápida: irm https://raw.githubusercontent.com/frp-bypass/professional/main/launch-gui.ps1 | iex

param(
    [string]$InstallPath = "$env:LOCALAPPDATA\FRPBypassPro",
    [switch]$ForceReinstall,
    [switch]$SkipUpdate
)

$ErrorActionPreference = "Stop"

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    } else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Show-QuickBanner {
    Write-Host ""
    Write-ColorOutput Cyan @"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║         FRP BYPASS PROFESSIONAL - QUICK GUI LAUNCHER         ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"@
    Write-Host ""
}

function Test-Installation {
    return (Test-Path "$InstallPath\main.py") -and (Test-Path "$InstallPath\gui\package.json")
}

function Quick-Install {
    Write-ColorOutput Yellow "🚀 Instalação não encontrada. Executando instalação rápida..."
    
    $installScript = "irm https://raw.githubusercontent.com/joseook/frp-bypass-software/main/install.ps1 | iex"
    Invoke-Expression $installScript
    
    if (-not (Test-Installation)) {
        Write-ColorOutput Red "❌ Falha na instalação automática."
        Write-ColorOutput Yellow "Execute manualmente: irm https://raw.githubusercontent.com/joseook/frp-bypass-software/main/install.ps1 | iex"
        exit 1
    }
}

function Start-GUI {
    Write-ColorOutput Blue "🎨 Iniciando interface gráfica..."
    
    $guiPath = "$InstallPath\gui"
    
    if (-not (Test-Path $guiPath)) {
        Write-ColorOutput Red "❌ Diretório GUI não encontrado."
        exit 1
    }
    
    Push-Location $guiPath
    
    try {
        # Verificar se node_modules existe
        if (-not (Test-Path "node_modules") -or $ForceReinstall) {
            Write-ColorOutput Blue "📦 Instalando dependências da GUI..."
            npm install --silent
        }
        
        # Verificar se o backend Python está rodando
        $pythonPath = "$InstallPath\venv\Scripts\python.exe"
        if (-not (Test-Path $pythonPath)) {
            $pythonPath = "python"
        }
        
        # Iniciar backend em background
        Write-ColorOutput Blue "🐍 Iniciando backend Python..."
        $backendJob = Start-Job -ScriptBlock {
            param($InstallPath, $PythonPath)
            Set-Location $InstallPath
            & $PythonPath main.py --api-mode
        } -ArgumentList $InstallPath, $pythonPath
        
        # Aguardar um pouco para o backend inicializar
        Start-Sleep -Seconds 3
        
        # Iniciar GUI
        Write-ColorOutput Green "✨ Abrindo FRP Bypass Professional GUI..."
        Write-ColorOutput Yellow "Aguarde a interface carregar..."
        
        npm start
        
    } catch {
        Write-ColorOutput Red "❌ Erro ao iniciar GUI: $($_.Exception.Message)"
        exit 1
    } finally {
        # Limpar job do backend
        if ($backendJob) {
            Stop-Job $backendJob -ErrorAction SilentlyContinue
            Remove-Job $backendJob -ErrorAction SilentlyContinue
        }
        Pop-Location
    }
}

function Check-Prerequisites {
    Write-ColorOutput Blue "🔍 Verificando pré-requisitos..."
    
    # Node.js
    try {
        $nodeVersion = node --version
        Write-ColorOutput Green "  ✓ Node.js $nodeVersion"
    } catch {
        Write-ColorOutput Red "❌ Node.js não encontrado!"
        Write-ColorOutput Yellow "Instale Node.js 16+ de: https://nodejs.org"
        exit 1
    }
    
    # Python
    try {
        $pythonVersion = python --version
        Write-ColorOutput Green "  ✓ Python $pythonVersion"
    } catch {
        Write-ColorOutput Red "❌ Python não encontrado!"
        Write-ColorOutput Yellow "Instale Python 3.9+ de: https://python.org"
        exit 1
    }
}

function Show-WelcomeMessage {
    Write-ColorOutput Green @"

🎉 FRP Bypass Professional GUI será aberto em instantes!

📱 Recursos disponíveis:
  • Dashboard em tempo real
  • Detecção automática de dispositivos
  • Bypass FRP com interface visual
  • Monitoramento de progresso
  • Logs e estatísticas

⚠️  IMPORTANTE:
  • Use apenas em dispositivos próprios
  • Certifique-se de ter autorização
  • Leia os termos de uso

🌐 A interface será aberta no navegador padrão
📊 Backend Python rodará em segundo plano

"@
}

# Função principal
function Main {
    Show-QuickBanner
    
    # Verificar se instalação existe
    if (-not (Test-Installation) -or $ForceReinstall) {
        Quick-Install
    }
    
    Check-Prerequisites
    Show-WelcomeMessage
    Start-GUI
}

# Executar launcher
try {
    Main
} catch {
    Write-ColorOutput Red "💥 Erro no launcher: $($_.Exception.Message)"
    Write-Host ""
    Write-ColorOutput Yellow "💡 Soluções:"
    Write-ColorOutput White "  1. Execute como administrador"
        Write-ColorOutput White "  2. Instale manualmente: irm https://raw.githubusercontent.com/joseook/frp-bypass-software/main/install.ps1 | iex"
    Write-ColorOutput White "  3. Verifique se Node.js e Python estão instalados"
    Write-Host ""
    Write-ColorOutput Cyan "Para suporte: https://github.com/joseook/frp-bypass-software/issues"
    
    Read-Host "Pressione Enter para sair"
    exit 1
}
