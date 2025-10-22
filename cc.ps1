# Claude Code Multi-Platform Launcher - Demo PowerShell Script
# This is a demonstration script showing how to integrate cc-launcher
# Copy this to your preferred location and modify the PROJECT_PATH below

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

# ========= CONFIGURATION =========
# Default user config directory (as recommended in README)
$DefaultProjectPath = "$env:USERPROFILE\.claude\scripts\cc-launcher"

# Function to find launcher.py in user config directory
function Find-LauncherInUserConfig {
    param([string]$UserConfigPath)
    $Launcher = Join-Path $UserConfigPath "launcher.py"
    if (Test-Path $Launcher) {
        return $Launcher
    }
    return $null
}

# Try to find launcher.py in order of preference:
$Launcher = $null

# 1. Check if script is in the same directory as launcher.py (for development/testing)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptLauncher = Join-Path $ScriptDir "launcher.py"
if (Test-Path $ScriptLauncher) {
    $Launcher = $ScriptLauncher
    # Only show development message when not in standard location
    if ($ScriptLauncher -ne (Join-Path $DefaultProjectPath "launcher.py")) {
        Write-Host "Found launcher in script directory: $ScriptLauncher" -ForegroundColor Cyan
    }
}

# 2. Check user config directory (recommended location)
if (-not $Launcher) {
    $UserConfigLauncher = Find-LauncherInUserConfig $DefaultProjectPath
    if ($UserConfigLauncher) {
        $Launcher = $UserConfigLauncher
        Write-Host "Found launcher in user config directory: $UserConfigLauncher" -ForegroundColor Cyan
    }
}

# 3. Check environment variable override
if (-not $Launcher -and $env:CC_LAUNCHER_PROJECT_PATH) {
    $EnvLauncher = Find-LauncherInUserConfig $env:CC_LAUNCHER_PROJECT_PATH
    if ($EnvLauncher) {
        $Launcher = $EnvLauncher
        Write-Host "Found launcher via environment variable: $EnvLauncher" -ForegroundColor Cyan
    }
}

# 4. If still not found, show error and usage instructions
if (-not $Launcher) {
    Write-ColorOutput "❌ launcher.py not found!" "Red"
    Write-ColorOutput "Please ensure cc-launcher is properly installed:" "Yellow"
    Write-ColorOutput "  1. Recommended: Copy to $DefaultProjectPath" "Yellow"
    Write-ColorOutput "  2. Or set CC_LAUNCHER_PROJECT_PATH environment variable" "Yellow"
    Write-ColorOutput "  3. Or place cc.ps1 in the same directory as launcher.py" "Yellow"
    exit 1
}
# ===============================

# Write-Host function for colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )

    $colors = @{
        "Red" = "Red"
        "Green" = "Green"
        "Yellow" = "Yellow"
        "Cyan" = "Cyan"
        "Magenta" = "Magenta"
        "White" = "White"
        "Gray" = "Gray"
    }

    Write-Host $Message -ForegroundColor $colors[$Color]
}

# Check Python availability
function Find-PythonExecutable {
    $pythonCommands = @("python3", "python", "py", "python3.11", "python3.10", "python3.9")

    foreach ($cmd in $pythonCommands) {
        try {
            $versionOutput = & $cmd --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                $versionInfo = $versionOutput -split ' '
                if ($versionInfo.Length -ge 2) {
                    $version = $versionInfo[1]
                    $majorVersion = [int]($version -split '\.')[0]

                    if ($majorVersion -ge 3) {
                        Write-ColorOutput "✓ Using Python: $cmd (version: $version)" "Green"
                        return $cmd
                    }
                }
            }
        } catch {
            continue
        }
    }

    return $null
}

$PythonCmd = Find-PythonExecutable

if (-not $PythonCmd) {
    Write-ColorOutput "❌ Python 3+ not found. Please install Python 3.7 or higher." "Red"
    Write-ColorOutput "   Download from: https://www.python.org/downloads/" "Yellow"
    exit 1
}

# Check if launcher exists
if (-not (Test-Path $Launcher)) {
    Write-ColorOutput "❌ Launcher not found: $Launcher" "Red"
    Write-ColorOutput "   Please ensure cc-launcher is installed at: $ProjectPath" "Yellow"
    Write-ColorOutput "   Or set CC_LAUNCHER_PROJECT_PATH environment variable" "Yellow"
    exit 1
}

# Execute launcher
Write-ColorOutput "🚀 Launching cc-launcher..." "Magenta"
try {
    if ($Arguments.Count -gt 0) {
        $argumentList = @($Launcher) + $Arguments
        $process = Start-Process -FilePath $PythonCmd -ArgumentList $argumentList -Wait -PassThru -NoNewWindow
        $ExitCode = $process.ExitCode
    } else {
        $process = Start-Process -FilePath $PythonCmd -ArgumentList @($Launcher) -Wait -PassThru -NoNewWindow
        $ExitCode = $process.ExitCode
    }
} catch {
    Write-ColorOutput "❌ Failed to execute launcher: $_" "Red"
    exit 1
}

exit $ExitCode