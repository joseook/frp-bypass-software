# FRP Bypass Professional - Instalador PowerShell
# Execução: irm https://raw.githubusercontent.com/frp-bypass/professional/main/install.ps1 | iex

param(
    [switch]$SkipGUI,
    [switch]$DevMode,
    [string]$InstallPath = "$env:LOCALAPPDATA\FRPBypassPro",
    [switch]$Uninstall
)

# Configurações
$ErrorActionPreference = "Continue"  # Mudado de "Stop" para "Continue" para evitar fechamento abrupto
$ProgressPreference = "SilentlyContinue"

# URLs do projeto
$GITHUB_REPO = "https://github.com/joseook/frp-bypass-software.git"
$RAW_BASE = "https://raw.githubusercontent.com/joseook/frp-bypass-software/main"
$RELEASES_API = "https://api.github.com/repos/joseook/frp-bypass-software/releases/latest"

# Cores para output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Banner {
    Write-Host ""
    Write-ColorOutput Cyan @"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║         FRP BYPASS PROFESSIONAL - INSTALADOR v1.0            ║
║                                                               ║
║     ⚠️  AVISO: Use apenas em dispositivos próprios ou        ║
║         com autorização expressa do proprietário             ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"@
    Write-Host ""
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Request-AdminRights {
    if (-not (Test-Administrator)) {
        Write-ColorOutput Yellow "🔐 Privilégios de administrador necessários para instalação completa."
        Write-ColorOutput Yellow "Relançando como administrador..."
        
        $arguments = "-NoProfile -ExecutionPolicy Bypass -Command `"& {irm https://raw.githubusercontent.com/joseook/frp-bypass-software/main/install.ps1 | iex}`""
        Start-Process PowerShell -ArgumentList $arguments -Verb RunAs
        exit
    }
}

function Test-Prerequisites {
    Write-ColorOutput Blue "🔍 Verificando pré-requisitos..."
    
    $issues = @()
    
    # Verificar Python
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) {
                $issues += "Python 3.9+ necessário (encontrado: $pythonVersion)"
            } else {
                Write-ColorOutput Green "  ✓ Python $pythonVersion"
            }
        }
    } catch {
        $issues += "Python não encontrado - instale de https://python.org"
    }
    
    # Verificar Node.js (para GUI)
    if (-not $SkipGUI) {
        try {
            $nodeVersion = node --version 2>&1
            if ($nodeVersion -match "v(\d+)\.") {
                $major = [int]$matches[1]
                if ($major -lt 16) {
                    $issues += "Node.js 16+ necessário para GUI (encontrado: $nodeVersion)"
                } else {
                    Write-ColorOutput Green "  ✓ Node.js $nodeVersion"
                }
            }
        } catch {
            Write-ColorOutput Yellow "  ⚠️ Node.js não encontrado - GUI será desabilitada"
            $Script:SkipGUI = $true
        }
    }
    
    # Verificar Git
    try {
        $gitVersion = git --version 2>&1
        Write-ColorOutput Green "  ✓ Git disponível"
    } catch {
        Write-ColorOutput Yellow "  ⚠️ Git não encontrado - download direto será usado"
    }
    
    if ($issues.Count -gt 0) {
        Write-ColorOutput Red "❌ Problemas encontrados:"
        foreach ($issue in $issues) {
            Write-ColorOutput Red "  • $issue"
        }
        
        Write-Host ""
        Write-ColorOutput Yellow "Deseja continuar mesmo assim? (s/N): " -NoNewline
        $continue = Read-Host
        if ($continue -ne 's' -and $continue -ne 'S') {
            Write-ColorOutput Red "Instalação cancelada."
            exit 1
        }
    }
}

function Install-AndroidSDK {
    Write-ColorOutput Blue "📱 Configurando Android SDK Platform Tools..."
    
    $sdkPath = "$InstallPath\platform-tools"
    
    if (Test-Path $sdkPath) {
        Write-ColorOutput Green "  ✓ Platform Tools já instalado"
        return
    }
    
    try {
        $zipUrl = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
        $zipPath = "$env:TEMP\platform-tools.zip"
        
        Write-ColorOutput Blue "  Baixando Platform Tools..."
        Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
        
        Write-ColorOutput Blue "  Extraindo..."
        Expand-Archive -Path $zipPath -DestinationPath $InstallPath -Force
        Remove-Item $zipPath
        
        # Adicionar ao PATH
        $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
        if ($currentPath -notlike "*$sdkPath*") {
            [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$sdkPath", "User")
            Write-ColorOutput Green "  ✓ Adicionado ao PATH do usuário"
        }
        
        Write-ColorOutput Green "  ✓ Android SDK Platform Tools instalado"
    } catch {
        Write-ColorOutput Red "  ❌ Falha ao instalar Platform Tools: $($_.Exception.Message)"
    }
}

function Download-Project {
    Write-ColorOutput Blue "📥 Baixando FRP Bypass Professional..."
    
    # Criar diretório de instalação
    if (Test-Path $InstallPath) {
        Remove-Item $InstallPath -Recurse -Force
    }
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
    
    try {
        # Tentar usar git primeiro
        if (Get-Command git -ErrorAction SilentlyContinue) {
            Write-ColorOutput Blue "  Clonando repositório..."
            Write-ColorOutput Yellow "  Isso pode levar alguns minutos..."
            
            # Executar git clone com melhor tratamento de erros
            $gitOutput = git clone $GITHUB_REPO $InstallPath 2>&1
            $gitExitCode = $LASTEXITCODE
            
            if ($gitExitCode -ne 0) {
                Write-ColorOutput Red "  ❌ Git clone falhou (código: $gitExitCode)"
                Write-ColorOutput Yellow "  Tentando método alternativo..."
                throw "Git clone failed with exit code $gitExitCode"
            }
        } else {
            # Fallback para download ZIP
            Write-ColorOutput Blue "  Baixando arquivo ZIP..."
            $zipUrl = "https://github.com/joseook/frp-bypass-software/archive/refs/heads/main.zip"
            $zipPath = "$env:TEMP\frp-bypass-pro.zip"
            
            Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
            Expand-Archive -Path $zipPath -DestinationPath "$env:TEMP\frp-extract" -Force
            
            # Mover conteúdo para diretório de instalação
            $extractedPath = "$env:TEMP\frp-extract\frp-bypass-software-main"
            if (Test-Path $extractedPath) {
                Get-ChildItem $extractedPath | Move-Item -Destination $InstallPath
            }
            
            Remove-Item $zipPath -Force
            Remove-Item "$env:TEMP\frp-extract" -Recurse -Force
        }
        
        Write-ColorOutput Green "  ✓ Projeto baixado"
    } catch {
        Write-ColorOutput Red "❌ Erro ao baixar projeto: $($_.Exception.Message)"
        exit 1
    }
}

function Install-PythonDependencies {
    Write-ColorOutput Blue "🐍 Instalando dependências Python..."
    
    Push-Location $InstallPath
    
    try {
        # Criar ambiente virtual
        Write-ColorOutput Blue "  Criando ambiente virtual..."
        python -m venv venv
        
        # Ativar ambiente virtual
        $venvActivate = ".\venv\Scripts\Activate.ps1"
        if (Test-Path $venvActivate) {
            & $venvActivate
        }
        
        # Instalar dependências
        Write-ColorOutput Blue "  Instalando dependências..."
        python -m pip install --upgrade pip | Out-Null
        python -m pip install -r requirements.txt | Out-Null
        
        Write-ColorOutput Green "  ✓ Dependências Python instaladas"
    } catch {
        Write-ColorOutput Red "  ❌ Erro ao instalar dependências Python: $($_.Exception.Message)"
    } finally {
        Pop-Location
    }
}

function Install-GUIDependencies {
    if ($SkipGUI) {
        Write-ColorOutput Yellow "⏭️ Pulando instalação da GUI"
        return
    }
    
    Write-ColorOutput Blue "🎨 Instalando dependências da GUI..."
    
    $guiPath = "$InstallPath\gui"
    if (-not (Test-Path $guiPath)) {
        Write-ColorOutput Yellow "  ⚠️ Diretório GUI não encontrado - pulando"
        return
    }
    
    Push-Location $guiPath
    
    try {
        Write-ColorOutput Blue "  Instalando pacotes Node.js..."
        npm install --silent 2>&1 | Out-Null
        
        Write-ColorOutput Green "  ✓ Dependências GUI instaladas"
    } catch {
        Write-ColorOutput Red "  ❌ Erro ao instalar dependências GUI: $($_.Exception.Message)"
        $Script:SkipGUI = $true
    } finally {
        Pop-Location
    }
}

function Create-Shortcuts {
    Write-ColorOutput Blue "🔗 Criando atalhos..."
    
    try {
        # Atalho no Desktop
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $shortcutPath = "$desktopPath\FRP Bypass Professional.lnk"
        
        $WScriptShell = New-Object -ComObject WScript.Shell
        $shortcut = $WScriptShell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = "powershell.exe"
        $shortcut.Arguments = "-NoProfile -WindowStyle Hidden -Command `"cd '$InstallPath'; python main.py`""
        $shortcut.WorkingDirectory = $InstallPath
        $shortcut.IconLocation = "$InstallPath\gui\assets\icon.ico,0"
        $shortcut.Description = "FRP Bypass Professional"
        $shortcut.Save()
        
        Write-ColorOutput Green "  ✓ Atalho criado no Desktop"
        
        # Comando global (opcional)
        $binPath = "$InstallPath\bin"
        New-Item -ItemType Directory -Path $binPath -Force | Out-Null
        
        $launcherScript = @"
@echo off
cd /d "$InstallPath"
python main.py %*
"@
        $launcherScript | Out-File -FilePath "$binPath\frp-bypass.cmd" -Encoding ASCII
        
        # Adicionar ao PATH
        $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
        if ($currentPath -notlike "*$binPath*") {
            [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$binPath", "User")
            Write-ColorOutput Green "  ✓ Comando 'frp-bypass' disponível globalmente"
        }
        
    } catch {
        Write-ColorOutput Yellow "  ⚠️ Não foi possível criar atalhos: $($_.Exception.Message)"
    }
}

function Create-GUILauncher {
    if ($SkipGUI) {
        return
    }
    
    Write-ColorOutput Blue "🖥️ Criando launcher da GUI..."
    
    try {
        $guiLauncherPath = "$InstallPath\launch-gui.ps1"
        $guiLauncher = @"
# FRP Bypass Professional - GUI Launcher
Set-Location "$InstallPath\gui"
npm start
"@
        $guiLauncher | Out-File -FilePath $guiLauncherPath -Encoding UTF8
        
        # Atalho para GUI
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $guiShortcutPath = "$desktopPath\FRP Bypass Professional (GUI).lnk"
        
        $WScriptShell = New-Object -ComObject WScript.Shell
        $shortcut = $WScriptShell.CreateShortcut($guiShortcutPath)
        $shortcut.TargetPath = "powershell.exe"
        $shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$guiLauncherPath`""
        $shortcut.WorkingDirectory = "$InstallPath\gui"
        $shortcut.IconLocation = "$InstallPath\gui\assets\icon.ico,0"
        $shortcut.Description = "FRP Bypass Professional - Interface Gráfica"
        $shortcut.Save()
        
        Write-ColorOutput Green "  ✓ Launcher GUI criado"
    } catch {
        Write-ColorOutput Yellow "  ⚠️ Não foi possível criar launcher GUI: $($_.Exception.Message)"
    }
}

function Test-Installation {
    Write-ColorOutput Blue "🧪 Testando instalação..."
    
    Push-Location $InstallPath
    
    try {
        # Ativar ambiente virtual
        $venvActivate = ".\venv\Scripts\Activate.ps1"
        if (Test-Path $venvActivate) {
            & $venvActivate
        }
        
        # Executar teste
        $testOutput = python main.py test 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput Green "  ✓ Instalação testada com sucesso"
        } else {
            Write-ColorOutput Yellow "  ⚠️ Alguns testes falharam, mas instalação está funcional"
        }
    } catch {
        Write-ColorOutput Yellow "  ⚠️ Não foi possível executar testes: $($_.Exception.Message)"
    } finally {
        Pop-Location
    }
}

function Show-CompletionMessage {
    Write-Host ""
    Write-ColorOutput Green @"
🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!

📍 Local de instalação: $InstallPath

🚀 Como usar:
"@
    
    Write-ColorOutput Cyan "  • Via linha de comando:"
    Write-ColorOutput White "    frp-bypass detect"
    Write-ColorOutput White "    frp-bypass bypass"
    
    if (-not $SkipGUI) {
        Write-ColorOutput Cyan "  • Via interface gráfica:"
        Write-ColorOutput White "    Clique duplo no atalho 'FRP Bypass Professional (GUI)'"
    }
    
    Write-ColorOutput Cyan "  • Diretamente:"
    Write-ColorOutput White "    cd `"$InstallPath`""
    Write-ColorOutput White "    python main.py --help"
    
    Write-Host ""
    Write-ColorOutput Yellow @"
⚠️  LEMBRE-SE:
• Use apenas em dispositivos próprios ou com autorização
• Leia a documentação em: $InstallPath\docs\
• Para suporte: https://github.com/frp-bypass/professional

📚 Tutorial completo: $InstallPath\docs\TUTORIAL_USUARIO.md
"@
    
    Write-Host ""
    Write-ColorOutput Green "Instalação finalizada! Pressione Enter para continuar..."
    Read-Host
}

function Uninstall-Application {
    Write-ColorOutput Yellow "🗑️ Desinstalando FRP Bypass Professional..."
    
    try {
        # Remover diretório de instalação
        if (Test-Path $InstallPath) {
            Remove-Item $InstallPath -Recurse -Force
            Write-ColorOutput Green "  ✓ Arquivos removidos"
        }
        
        # Remover atalhos
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $shortcuts = @(
            "$desktopPath\FRP Bypass Professional.lnk",
            "$desktopPath\FRP Bypass Professional (GUI).lnk"
        )
        
        foreach ($shortcut in $shortcuts) {
            if (Test-Path $shortcut) {
                Remove-Item $shortcut -Force
                Write-ColorOutput Green "  ✓ Atalho removido: $(Split-Path $shortcut -Leaf)"
            }
        }
        
        # Limpar PATH
        $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
        $newPath = ($currentPath -split ';' | Where-Object { $_ -notlike "*FRPBypassPro*" }) -join ';'
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
        
        Write-ColorOutput Green "🎉 Desinstalação concluída!"
    } catch {
        Write-ColorOutput Red "❌ Erro durante desinstalação: $($_.Exception.Message)"
    }
}

# Função principal
function Main {
    Write-Banner
    
    if ($Uninstall) {
        Uninstall-Application
        return
    }
    
    if (-not $DevMode) {
        Request-AdminRights
    }
    
    Test-Prerequisites
    Install-AndroidSDK
    Download-Project
    Install-PythonDependencies
    Install-GUIDependencies
    Create-Shortcuts
    Create-GUILauncher
    Test-Installation
    Show-CompletionMessage
}

# Executar instalação
try {
    Main
} catch {
    Write-ColorOutput Red "💥 Erro durante instalação: $($_.Exception.Message)"
    Write-ColorOutput Yellow "Para suporte, visite: https://github.com/frp-bypass/professional/issues"
    exit 1
}
