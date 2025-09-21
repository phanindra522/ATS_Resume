# Docker Storage Migration Script for Windows

# This script helps move Docker Desktop from C: drive to D: drive

Write-Host "🐳 Docker Storage Migration to D: Drive" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Check current Docker status
Write-Host "1. Checking Docker status..." -ForegroundColor Yellow
docker version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Stop Docker Desktop
Write-Host "2. Stopping Docker Desktop..." -ForegroundColor Yellow
Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 5

# Stop WSL2
Write-Host "3. Stopping WSL2..." -ForegroundColor Yellow
wsl --shutdown

# Create D: drive directories
Write-Host "4. Creating directories on D: drive..." -ForegroundColor Yellow
$dockerDataDir = "D:\Docker"
$wslDataDir = "D:\Docker\wsl\data"
$volumeDir = "D:\Docker\volumes"

New-Item -ItemType Directory -Path $dockerDataDir -Force | Out-Null
New-Item -ItemType Directory -Path $wslDataDir -Force | Out-Null
New-Item -ItemType Directory -Path $volumeDir -Force | Out-Null

Write-Host "✅ Created directories:" -ForegroundColor Green
Write-Host "   - $dockerDataDir" -ForegroundColor Cyan
Write-Host "   - $wslDataDir" -ForegroundColor Cyan
Write-Host "   - $volumeDir" -ForegroundColor Cyan

# Export WSL2 distribution
Write-Host "5. Exporting WSL2 Docker distribution..." -ForegroundColor Yellow
$exportPath = "D:\Docker\docker-desktop-data.tar"
wsl --export docker-desktop-data $exportPath

if (Test-Path $exportPath) {
    Write-Host "✅ Exported WSL2 distribution to D: drive" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to export WSL2 distribution" -ForegroundColor Red
    exit 1
}

# Unregister old WSL2 distribution
Write-Host "6. Unregistering old WSL2 distribution..." -ForegroundColor Yellow
wsl --unregister docker-desktop-data

# Import WSL2 distribution to D: drive
Write-Host "7. Importing WSL2 distribution to D: drive..." -ForegroundColor Yellow
wsl --import docker-desktop-data "D:\Docker\wsl\docker-desktop-data" $exportPath

# Clean up export file
Remove-Item $exportPath -Force

Write-Host "✅ Docker data successfully moved to D: drive!" -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host "1. Start Docker Desktop" -ForegroundColor Cyan
Write-Host "2. Go to Docker Desktop Settings > Resources > Advanced" -ForegroundColor Cyan
Write-Host "3. Change Disk image location to: D:\Docker\wsl\data" -ForegroundColor Cyan
Write-Host "4. Apply and Restart Docker Desktop" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White
Write-Host "Disk space saved on C: drive!" -ForegroundColor Green