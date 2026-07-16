<#
.SYNOPSIS
    One-click setup for Agent OS Bridge (Windows & Linux).

.DESCRIPTION
    Detects or downloads Python, creates a local venv, installs dependencies,
    runs tests, and generates MCP config. No prior Conda needed.

.EXAMPLE
    PowerShell: .\setup.ps1
    Linux:      pwsh setup.ps1
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# --- Detect platform ---
$isWindows = [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT
$venvPythonRel = if ($isWindows) { "Scripts\python.exe" } else { "bin/python3" }
$venvPipRel   = if ($isWindows) { "Scripts\pip.exe" }    else { "bin/pip3" }

$bridge  = Split-Path -Parent $MyInvocation.MyCommand.Path
$agentHome = Split-Path $bridge -Parent
$venvDir   = Join-Path $bridge ".venv"
$venvPython = Join-Path $venvDir $venvPythonRel
$venvPip    = Join-Path $venvDir $venvPipRel
$reqFile    = Join-Path $bridge "requirements.txt"

Write-Host ""
Write-Host "=== Agent OS Bridge Setup ===" -ForegroundColor Cyan
Write-Host "  Platform: $([System.Environment]::OSVersion.Platform)"
Write-Host ""

Write-Host "[1/6] Detecting paths..." -ForegroundColor Yellow
Write-Host "  Agent OS: $agentHome"
Write-Host "  Bridge:   $bridge"
$bootFile = Join-Path (Join-Path $agentHome "Brain") "BootProtocol.md"
if (-not (Test-Path -LiteralPath $bootFile)) {
    throw "Agent OS not found at: $agentHome"
}
Write-Host "  Agent OS repository: OK"

# --- Step 2: Locate or install Python ---
Write-Host ""
Write-Host "[2/6] Locating Python..." -ForegroundColor Yellow
$pyExe = Get-Command python3, python -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source
if (-not $pyExe -or -not (Test-Path -LiteralPath $pyExe)) {
    if ($isWindows) {
        Write-Host "  Python not found. Downloading embedded Python..." -ForegroundColor Yellow
        $url = "https://www.python.org/ftp/python/3.12.9/python-3.12.9-embed-amd64.zip"
        $zipPath = Join-Path $bridge "python-embed.zip"
        $pyDir = Join-Path $bridge ".python"
        try {
            Invoke-WebRequest -Uri $url -OutFile $zipPath -UseBasicParsing
            Write-Host "  Downloaded embedded Python."
            Expand-Archive -LiteralPath $zipPath -DestinationPath $pyDir -Force
            Remove-Item -LiteralPath $zipPath -Force
            $embeddedPython = Get-ChildItem -LiteralPath $pyDir -Filter "python.exe" -Recurse | Select-Object -First 1 -ExpandProperty FullName
            if (-not $embeddedPython) { throw "Embedded Python extraction failed." }
            $pyExe = $embeddedPython
            Write-Host "  Embedded Python: $pyExe"
            Get-ChildItem -LiteralPath $pyDir -Filter "*._pth" | Rename-Item -NewName { $_.Name + ".disabled" }
            $getPip = Join-Path $bridge "get-pip.py"
            Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPip -UseBasicParsing
            & $pyExe $getPip --no-warn-script-location --quiet
            Remove-Item -LiteralPath $getPip -Force
        } catch {
            Write-Host "  Embedded Python download failed: $_" -ForegroundColor Red
            Write-Host "  Install Python 3.10+ from https://python.org and re-run setup.ps1" -ForegroundColor Yellow
            throw $_
        }
    } else {
        Write-Host "  Python not found." -ForegroundColor Yellow
        Write-Host "  Install it with: sudo apt install python3 python3-venv python3-pip" -ForegroundColor Yellow
        throw "Python is required. Install it and re-run setup.ps1."
    }
} else {
    $version = & $pyExe --version 2>&1
    Write-Host "  Found: $($version.Trim())"
}

# --- Step 3: Create venv ---
Write-Host ""
Write-Host "[3/6] Creating local Python environment..." -ForegroundColor Yellow
if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "  Creating .venv at $venvDir..."
    & $pyExe -m venv $venvDir
    if ($LASTEXITCODE -ne 0) { throw "Failed to create virtual environment." }
    Write-Host "  .venv created."
} else {
    Write-Host "  .venv already exists."
}

# --- Step 4: Install dependencies ---
Write-Host ""
Write-Host "[4/6] Installing dependencies..." -ForegroundColor Yellow
if (-not (Test-Path -LiteralPath $venvPip)) {
    # On some Linux distros, pip may be pip3 inside venv
    $venvPip = Join-Path $venvDir "bin/pip"
}
& $venvPip install -r $reqFile --quiet
if ($LASTEXITCODE -ne 0) { throw "Failed to install dependencies." }
Write-Host "  Dependencies installed."

# --- Step 5: Run tests ---
Write-Host ""
Write-Host "[5/6] Running tests..." -ForegroundColor Yellow
$testBridge = Join-Path $bridge "test_bridge.py"
if (Test-Path -LiteralPath $testBridge) {
    & $venvPython $testBridge
    if ($LASTEXITCODE -ne 0) { throw "Bridge tests failed." }
    Write-Host "  Bridge tests passed."
}
& $venvPython -m py_compile (Join-Path $bridge "server.py")
if ($LASTEXITCODE -ne 0) { throw "Server syntax check failed." }
Write-Host "  Server syntax OK."

$testMCP = Join-Path $bridge "test_mcp_protocol.py"
if (Test-Path -LiteralPath $testMCP) {
    & $venvPython $testMCP
    if ($LASTEXITCODE -ne 0) { throw "MCP protocol test failed." }
    Write-Host "  MCP protocol tests passed."
}

# --- Step 6: Generate MCP config ---
Write-Host ""
Write-Host "[6/6] Generating MCP config..." -ForegroundColor Yellow
$mcpConfig = @{
    server_id   = "agent"
    name        = "Agent OS"
    description = "Wake agent, sync Git memory, retrieve dynamic context."
    transport   = "stdio"
    command     = "$venvPython"
    args        = @("$(Join-Path $bridge server.py)")
    env         = @{}
} | ConvertTo-Json -Depth 3
$mcpConfigPath = Join-Path $bridge "mcp-config.json"
Set-Content -LiteralPath $mcpConfigPath -Value $mcpConfig -Encoding UTF8
Write-Host "  Generated: $mcpConfigPath"

# --- Done ---
Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Configure your AI client MCP to point to:"
Write-Host "     Command: $venvPython"
Write-Host "     Args:    $(Join-Path $bridge server.py)"
Write-Host ""
Write-Host "  2. (Optional) Run the setup wizard for your agent profile:"
if ($isWindows) {
    Write-Host "     .\scripts\setup_wizard.ps1"
} else {
    Write-Host "     pwsh scripts/setup_wizard.ps1"
}
Write-Host ""
Write-Host "Quick test:"
if ($isWindows) {
    Write-Host '  Run: .venv\Scripts\python.exe server.py'
} else {
    Write-Host '  Run: .venv/bin/python3 server.py'
}
Write-Host '  Then in your AI client: call agent_ping'
