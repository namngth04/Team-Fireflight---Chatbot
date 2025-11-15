#requires -version 5.1
Param(
    [switch]$IncludeFrontend
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$frontendDir = Join-Path $projectRoot "frontend"
$activateScript = Join-Path $projectRoot ".venv\Scripts\Activate.ps1"

if (-not (Test-Path $activateScript)) {
    throw "Virtual environment not found. Please run 'python -m venv .venv' and install dependencies first."
}

function Start-ServiceWindow {
    param (
        [string]$Title,
        [string]$Command,
        [string]$WorkingDirectory = $projectRoot
    )

    $psArgs = @("-NoExit", "-Command", $Command)
    Start-Process -FilePath "powershell" -ArgumentList $psArgs -WorkingDirectory $WorkingDirectory | Out-Null
    Write-Host "👉 Started $Title"
}

# FastAPI backend (includes Spoon agent)
$backendCmd = "cd `"$projectRoot`"; & `"$activateScript`"; uvicorn app.main:app --reload"
Start-ServiceWindow -Title "FastAPI (Spoon agent inside)" -Command $backendCmd

# MCP server
$mcpCmd = "cd `"$projectRoot`"; & `"$activateScript`"; python -m app.mcp_server"
Start-ServiceWindow -Title "MCP Server" -Command $mcpCmd

if ($IncludeFrontend) {
    $frontendCmd = "cd `"$frontendDir`"; npm run dev"
    Start-ServiceWindow -Title "Next.js Frontend" -Command $frontendCmd -WorkingDirectory $frontendDir
}

$defaultMcpPort = if ($env:MCP_SERVER_PORT) { $env:MCP_SERVER_PORT } else { 8001 }

Write-Host ""
Write-Host "✅ Services launched."
Write-Host "   - Backend + Spoon agent runs via uvicorn."
Write-Host "   - MCP server exposes tools over FastMCP (default http://localhost:$defaultMcpPort)."
if ($IncludeFrontend) {
    Write-Host "   - Frontend served via npm dev server."
}

