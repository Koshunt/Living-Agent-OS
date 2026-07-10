<#
.SYNOPSIS
    One-click setup for Agent OS CC Switch Bridge.

.DESCRIPTION
    Creates a local Python venv, installs dependencies, runs tests,
    and generates CC Switch MCP config. No Conda needed.

.EXAMPLE
    .\setup.ps1
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$bridge = Split-Path -Parent $MyInvocation.MyCommand.Path
$agentHome = Split-Path $bridge -Parent
$venvDir = Join-Path $bridge ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$venvPip = Join-Path $venvDir "Scripts\pip.exe"

Write-Host ""
Write-Host "=== Agent OS CC Switch Bridge Setup ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/5] Detecting paths..." -ForegroundColor Yellow
Write-Host "  Agent OS: $agentHome"
Write-Host "  Bridge:   $bridge"
if (-not (Test-Path -LiteralPath (Join-Path $agentHome "Brain\BootProtocol.md"))) {
    throw "Agent OS not found at: $agentHome"
}
Write-Host "  Agent OS repository: OK"

# --- Step 2: Create venv ---
Write-Host ""
Write-Host "[2/5] Creating local Python environment..." -ForegroundColor Yellow
if (-not (Test-Path -LiteralPath $venvPython)) {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) {
        throw "Python is not installed or not in PATH. Install Python 3.10+ from https://python.org"
    }
    $version = & python --version
    Write-Host "  Found: $version"
    Write-Host "  Creating .venv at $venvDir..."
    & python -m venv $venvDir
    if ($LASTEXITCODE -ne 0) { throw "Failed to create virtual environment." }
} else {
    Write-Host "  Virtual environment already exists."
}

# --- Step 3: Install dependencies ---
Write-Host ""
Write-Host "[3/5] Installing dependencies..." -ForegroundColor Yellow
& $venvPip install -r (Join-Path $bridge "requirements.txt") --quiet
if ($LASTEXITCODE -ne 0) { throw "Failed to install dependencies." }
Write-Host "  Dependencies installed."

# --- Step 4: Run tests ---
Write-Host ""
Write-Host "[4/5] Running tests..." -ForegroundColor Yellow
& $venvPython (Join-Path $bridge "test_bridge.py")
if ($LASTEXITCODE -ne 0) { throw "Bridge tests failed." }
& $venvPython -m py_compile (Join-Path $bridge "server.py")
if ($LASTEXITCODE -ne 0) { throw "Server syntax check failed." }
& $venvPython (Join-Path $bridge "test_mcp_protocol.py")
if ($LASTEXITCODE -ne 0) { throw "MCP protocol test failed." }
Write-Host "  All tests passed."

# --- Step 5: Generate CC Switch config ---
Write-Host ""
Write-Host "[5/5] Generating CC Switch MCP config..." -ForegroundColor Yellow
$mcpConfig = @{
    server_id   = "agent"
    name        = "Agent OS"
    description = "Wake agent, sync Git memory, retrieve dynamic context."
    transport   = "stdio"
    command     = $venvPython
    args        = @((Join-Path $bridge "server.py"))
    env         = @{}
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
