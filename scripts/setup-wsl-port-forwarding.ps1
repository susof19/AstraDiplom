# Setup script for Port Forwarding in WSL2
# Forwards ports 3000 and 8000 from WSL2 to Windows host for local network access
# Run as administrator: PowerShell -ExecutionPolicy Bypass -File .\scripts\setup-wsl-port-forwarding.ps1

Write-Host "Setting up Port Forwarding for WSL2" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check administrator rights
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: Script must be run as administrator!" -ForegroundColor Red
    Write-Host "Run PowerShell as administrator and execute:" -ForegroundColor Yellow
    Write-Host "   PowerShell -ExecutionPolicy Bypass -File .\scripts\setup-wsl-port-forwarding.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "Administrator rights confirmed" -ForegroundColor Green
Write-Host ""

# Get WSL2 IP address
Write-Host "Detecting WSL2 IP address..." -ForegroundColor Yellow
$wslIp = wsl hostname -I 2>$null
if ($LASTEXITCODE -ne 0 -or -not $wslIp) {
    Write-Host "   Could not get WSL2 IP address automatically" -ForegroundColor Yellow
    Write-Host "   Make sure WSL2 is running" -ForegroundColor Yellow
    Write-Host ""
    $wslIp = Read-Host "Enter WSL2 IP address manually (or press Enter to use 127.0.0.1)"
    if ([string]::IsNullOrWhiteSpace($wslIp)) {
        $wslIp = "127.0.0.1"
        Write-Host "   Using 127.0.0.1 (will need update after WSL restart)" -ForegroundColor Yellow
    }
} else {
    $wslIp = $wslIp.Trim()
    Write-Host "   WSL2 IP address: $wslIp" -ForegroundColor Green
}

Write-Host ""

# Ports to forward
$ports = @(3000, 8000)

# Remove old rules
Write-Host "Removing old port forwarding rules..." -ForegroundColor Yellow
foreach ($port in $ports) {
    netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>$null
}
Write-Host "Cleanup completed" -ForegroundColor Green
Write-Host ""

# Create new rules
Write-Host "Creating port forwarding rules..." -ForegroundColor Yellow
foreach ($port in $ports) {
    try {
        netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0 connectport=$port connectaddress=$wslIp | Out-Null
        Write-Host "Port $port forwarded: 0.0.0.0:$port -> ${wslIp}:$port" -ForegroundColor Green
    } catch {
        Write-Host "Error configuring port $port : $_" -ForegroundColor Red
    }
}

Write-Host ""

# Configure firewall (if not already configured)
Write-Host "Checking firewall rules..." -ForegroundColor Yellow
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
Write-Host "Port forwarding setup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Forwarded ports:" -ForegroundColor Cyan
Write-Host "   - Port 3000 (Frontend): 0.0.0.0:3000 -> ${wslIp}:3000" -ForegroundColor White
Write-Host "   - Port 8000 (Backend):  0.0.0.0:8000 -> ${wslIp}:8000" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Yellow
if ($wslIp -eq "127.0.0.1") {
    Write-Host "   Using 127.0.0.1, which works but IP may change after WSL restart" -ForegroundColor Yellow
    Write-Host "   For permanent solution use mirrored networking mode (see setup-wsl-mirrored-networking.ps1)" -ForegroundColor Yellow
} else {
    Write-Host "   WSL2 IP address may change after WSL restart" -ForegroundColor Yellow
    Write-Host "   If connection stops working, run this script again" -ForegroundColor Yellow
    Write-Host "   Or use mirrored networking mode for permanent solution" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "To connect from other machines, use Windows host IP address" -ForegroundColor Cyan
Write-Host '   To find IP: ipconfig | findstr IPv4' -ForegroundColor White
Write-Host "==================================================" -ForegroundColor Cyan
