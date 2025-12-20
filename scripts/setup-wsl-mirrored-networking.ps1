# Setup script for Mirrored Networking Mode in WSL2
# This is a modern solution that makes WSL2 accessible from local network without port forwarding
# Run as administrator: PowerShell -ExecutionPolicy Bypass -File .\scripts\setup-wsl-mirrored-networking.ps1

Write-Host "Setting up Mirrored Networking Mode for WSL2" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check administrator rights
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: Script must be run as administrator!" -ForegroundColor Red
    Write-Host "Run PowerShell as administrator and execute:" -ForegroundColor Yellow
    Write-Host "   PowerShell -ExecutionPolicy Bypass -File .\scripts\setup-wsl-mirrored-networking.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "Administrator rights confirmed" -ForegroundColor Green
Write-Host ""

# Define path to .wslconfig
$wslConfigPath = "$env:USERPROFILE\.wslconfig"

Write-Host "Configuring .wslconfig..." -ForegroundColor Yellow

# Check if file exists
if (Test-Path $wslConfigPath) {
    Write-Host "   .wslconfig file already exists, creating backup..." -ForegroundColor Yellow
    $backupPath = "${wslConfigPath}.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $wslConfigPath $backupPath
    Write-Host "   Backup created: $backupPath" -ForegroundColor Green
    
    # Read existing file
    $content = Get-Content $wslConfigPath -Raw
    
    # Check if [wsl2] section already exists
    if ($content -match '\[wsl2\]') {
        # If exists, update networkingMode
        if ($content -match 'networkingMode\s*=') {
            $content = $content -replace 'networkingMode\s*=.*', 'networkingMode=mirrored'
            Write-Host "   Updated existing networkingMode" -ForegroundColor Green
        } else {
            # Add networkingMode to existing section
            $content = $content -replace '(\[wsl2\])', "`$1`nnetworkingMode=mirrored"
            Write-Host "   Added networkingMode to existing [wsl2] section" -ForegroundColor Green
        }
    } else {
        # Add new [wsl2] section
        $content += "`n[wsl2]`nnetworkingMode=mirrored`n"
        Write-Host "   Added new [wsl2] section with networkingMode=mirrored" -ForegroundColor Green
    }
} else {
    # Create new file
    $content = "[wsl2]`nnetworkingMode=mirrored`n"
    Write-Host "   Created new .wslconfig file" -ForegroundColor Green
}

# Write file
Set-Content -Path $wslConfigPath -Value $content -Encoding UTF8
Write-Host ".wslconfig file configured: $wslConfigPath" -ForegroundColor Green
Write-Host ""

# Configure firewall
Write-Host "Configuring firewall..." -ForegroundColor Yellow
$ports = @(3000, 8000)
foreach ($port in $ports) {
    $ruleName = "Astra Trainer Port $port"
    $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    if (-not $existingRule) {
        try {
            $desc = "Allows incoming connections on port $port for Astra Trainer"
            New-NetFirewallRule -DisplayName $ruleName `
                -Direction Inbound `
                -LocalPort $port `
                -Protocol TCP `
                -Action Allow `
                -Profile Private, Domain `
                -Description $desc | Out-Null
            Write-Host "Firewall rule for port $port created" -ForegroundColor Green
        } catch {
            Write-Host "Failed to create firewall rule for port $port : $_" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Firewall rule for port $port already exists" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Setup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: WSL2 restart is required to apply changes" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "   1. Close all WSL windows" -ForegroundColor White
Write-Host "   2. In PowerShell run: wsl --shutdown" -ForegroundColor White
Write-Host "   3. Start WSL again" -ForegroundColor White
Write-Host "   4. Run application: ./start-demo-wsl.sh" -ForegroundColor White
Write-Host ""
Write-Host "Benefits of Mirrored Networking Mode:" -ForegroundColor Cyan
Write-Host "   - WSL2 uses the same IP addresses as Windows host" -ForegroundColor White
Write-Host "   - No port forwarding configuration needed" -ForegroundColor White
Write-Host "   - Works automatically after WSL restart" -ForegroundColor White
Write-Host "   - More reliable solution" -ForegroundColor White
Write-Host ""
Write-Host "After WSL restart, use Windows host IP address to connect" -ForegroundColor Cyan
Write-Host '   To find IP: ipconfig | findstr IPv4' -ForegroundColor White
Write-Host "==================================================" -ForegroundColor Cyan
