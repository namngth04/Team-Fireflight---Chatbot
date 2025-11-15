#requires -version 5.1
Param(
    [switch]$NoMcp
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$activateScript = Join-Path $projectRoot ".venv\Scripts\Activate.ps1"
$activateScript = (Resolve-Path $activateScript).Path

function Start-Window {
    param (
        [string]$Title,
        [string]$Command
    )

    Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $Command | Out-Null
    Write-Host "👉 $Title started"
}

# FastAPI backend
$backendCmd = "cd `"$projectRoot`"; & `"$activateScript`"; uvicorn app.main:app --reload"
Start-Window -Title "FastAPI backend" -Command $backendCmd

if (-not $NoMcp) {
    $mcpCmd = "cd `"$projectRoot`"; & `"$activateScript`"; python -m app.mcp_server"
    Start-Window -Title "MCP server" -Command $mcpCmd
}

Write-Host ""
Write-Host "✅ Simple run script launched."
Write-Host "Use Ctrl+C trong từng cửa sổ để dừng dịch vụ."

