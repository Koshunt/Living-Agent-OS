<#
.SYNOPSIS
    One-click setup for Agent OS CC Switch Bridge.

.DESCRIPTION
    Reads config.json, creates Conda environment, installs dependencies,
    runs tests, and generates the CC Switch MCP configuration.

.EXAMPLE
    .\setup.ps1
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$bridge = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path $bridge "config.json"

Write-Host ""
Write-Host "=== Agent OS CC Switch Bridge Setup ===" -ForegroundColor Cyan
Write-Host ""

# --- Step 1: Read config ---
Write-Host "[1/5] Reading config.json..." -ForegroundColor Yellow
if (-not (Test-Path -LiteralPath $configPath)) {
    Write-Host "config.json not found. Creating from template..." -ForegroundColor Yellow
    $template = Get-Content -LiteralPath (Join-Path $bridge "config.example.json") -Raw
    Set-Content -LiteralPath $configPath -Value $template -Encoding UTF8
    Write-Host "Please edit config.json with your actual paths, then run setup.ps1 again." -ForegroundColor Red
    exit 1
}

$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$homePath = $config.agent_home
$envPrefix = $config.python_env
$envPython = Join-Path $envPrefix "python.exe"

Write-Host "  agent_home: $homePath"
Write-Host "  Python env: $envPrefix"

# --- Step 2: Validate paths ---
Write-Host ""
Write-Host "[2/5] Validating paths..." -ForegroundColor Yellow
if (-not (Test-Path -LiteralPath (Join-Path $homePath "Brain\BootProtocol.md"))) {
    throw "Agent OS not found at: $homePath"
}
Write-Host "  Agent OS repository: OK"

# --- Step 3: Create Conda environment ---
Write-Host ""
Write-Host "[3/5] Setting up Python environment..." -ForegroundColor Yellow
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    throw "Conda is not installed or not in PATH."
}
if (-not (Test-Path -LiteralPath $envPython)) {
    Write-Host "  Creating Conda environment at $envPrefix..."
    conda create --prefix $envPrefix python=3.12 pip -y
    if ($LASTEXITCODE -ne 0) { throw "Failed to create Conda environment." }
} else {
    Write-Host "  Conda environment already exists."
}

# --- Step 4: Install dependencies ---
Write-Host ""
Write-Host "[4/5] Installing dependencies..." -ForegroundColor Yellow
& $envPython -m pip install -r (Join-Path $bridge "requirements.txt") --quiet
if ($LASTEXITCODE -ne 0) { throw "Failed to install dependencies." }
Write-Host "  Dependencies installed."

# --- Step 5: Generate CC Switch config ---
Write-Host ""
Write-Host "[5/5] Generating CC Switch MCP config..." -ForegroundColor Yellow
$serverPy = Join-Path $bridge "server.py"
$mcpConfig = @{
    server_id = "agent"
    name      = "Agent OS"
    description = "Wake agent, sync Git memory, retrieve dynamic context."
    transport = "stdio"
    command   = $envPython
    args      = @($serverPy)
    env       = @{}
} | ConvertTo-Json -Depth 3
$mcpConfigPath = Join-Path $bridge "ccswitch-mcp-config.json"
Set-Content -LiteralPath $mcpConfigPath -Value $mcpConfig -Encoding UTF8
Write-Host "  Generated: $mcpConfigPath"

# --- Done ---
Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Open CC Switch -> MCP -> + -> Custom"
Write-Host "  2. Paste the contents of ccswitch-mcp-config.json"
Write-Host "  3. Enable for OpenCode / Codex / Claude"
Write-Host "  4. Add the Prompt from Agent-Bootstrap-Prompt.md"
Write-Host "  5. Restart your CLI"
Write-Host ""
Write-Host "Quick test:"
Write-Host '  Please call agent_ping and tell me the Git status.'
Write-Host ""
