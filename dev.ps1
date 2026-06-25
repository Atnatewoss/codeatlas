param (
    [string]$Command = "help"
)

$ApiDir = Join-Path $PSScriptRoot "apps\api"
$WebDir = Join-Path $PSScriptRoot "apps\web"

switch ($Command) {
    "setup-api" {
        Write-Host "Installing API dependencies..." -ForegroundColor Cyan
        & pip install -r (Join-Path $ApiDir "requirements.txt")
    }
    "setup-web" {
        Write-Host "Installing web dependencies..." -ForegroundColor Cyan
        Push-Location $WebDir
        & npm install
        Pop-Location
    }
    "setup" {
        & "$PSCommandPath" setup-api
        & "$PSCommandPath" setup-web
    }
    "dev-api" {
        Write-Host "Starting API at http://localhost:8000" -ForegroundColor Cyan
        Push-Location $ApiDir
        & python -m app.main
        Pop-Location
    }
    "dev-web" {
        Write-Host "Starting web at http://localhost:3000" -ForegroundColor Cyan
        Push-Location $WebDir
        & npm run dev
        Pop-Location
    }
    "dev" {
        Write-Host "Starting API and web in separate windows..." -ForegroundColor Cyan
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ApiDir'; python -m app.main"
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$WebDir'; npm run dev"
        Write-Host "Both started. Close windows to stop." -ForegroundColor Green
    }
    "test" {
        Write-Host "Running API tests..." -ForegroundColor Cyan
        Push-Location $ApiDir
        & python -m pytest tests/ -v
        Pop-Location
    }
    "clean" {
        Write-Host "Cleaning..." -ForegroundColor Cyan
        Get-ChildItem -Path $PSScriptRoot -Directory -Filter "__pycache__" -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        $nextDir = Join-Path $WebDir ".next"
        if (Test-Path $nextDir) {
            Remove-Item -Recurse -Force $nextDir
        }
        Write-Host "Done" -ForegroundColor Green
    }
    default {
        Write-Host @"

CodeAtlas Dev Script
Usage: .\dev.ps1 <command>

Commands:
  setup       Install all dependencies
  setup-api   Install Python API dependencies
  setup-web   Install web frontend dependencies
  dev         Start API and web in parallel
  dev-api     Start API server only
  dev-web     Start web dev server only
  test        Run API tests
  clean       Remove caches

"@ -ForegroundColor White
    }
}
