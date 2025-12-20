# Windows Firewall setup script for Astra Trainer
# Allows incoming connections on ports 3000 and 8000 from local network
# Run as administrator: PowerShell -ExecutionPolicy Bypass -File .\scripts\setup-windows-firewall.ps1

Write-Host "Setting up Windows Firewall for Astra Trainer" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check administrator rights
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: Script must be run as administrator!" -ForegroundColor Red
    Write-Host "Run PowerShell as administrator and execute:" -ForegroundColor Yellow
    Write-Host "   PowerShell -ExecutionPolicy Bypass -File .\scripts\setup-windows-firewall.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "Administrator rights confirmed" -ForegroundColor Green
Write-Host ""

# Remove old rules (if exist)
Write-Host "Removing old rules (if exist)..." -ForegroundColor Yellow
Remove-NetFirewallRule -DisplayName "Astra Trainer Frontend" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "Astra Trainer Backend" -ErrorAction SilentlyContinue
Write-Host "Cleanup completed" -ForegroundColor Green
Write-Host ""

# Create rules for Frontend (port 3000)
Write-Host "Creating rule for Frontend (port 3000)..." -ForegroundColor Yellow
try {
    $desc = "Allows incoming connections to Frontend Astra Trainer on port 3000"
    New-NetFirewallRule -DisplayName "Astra Trainer Frontend" `
        -Direction Inbound `
        -LocalPort 3000 `
        -Protocol TCP `
        -Action Allow `
        -Profile Private, Domain `
        -Description $desc
    Write-Host "Frontend rule created" -ForegroundColor Green
} catch {
    Write-Host "Error creating Frontend rule: $_" -ForegroundColor Red
    exit 1
}

# Create rules for Backend (port 8000)
Write-Host "Creating rule for Backend (port 8000)..." -ForegroundColor Yellow
try {
    $desc = "Allows incoming connections to Backend Astra Trainer on port 8000"
    New-NetFirewallRule -DisplayName "Astra Trainer Backend" `
        -Direction Inbound `
        -LocalPort 8000 `
        -Protocol TCP `
        -Action Allow `
        -Profile Private, Domain `
        -Description $desc
    Write-Host "Backend rule created" -ForegroundColor Green
} catch {
    Write-Host "Error creating Backend rule: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Firewall setup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Created rules:" -ForegroundColor Cyan
Write-Host "   - Astra Trainer Frontend (port 3000)" -ForegroundColor White
Write-Host "   - Astra Trainer Backend (port 8000)" -ForegroundColor White
Write-Host ""
Write-Host "You can now connect to services from local network" -ForegroundColor Yellow
Write-Host "Use IP address shown when running start-demo-wsl.sh" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan
