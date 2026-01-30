# Setup script for Port Forwarding for LM Studio
# Forwards LM Studio port from Windows localhost to external interface
# so WSL2 can access it via Windows Host IP
# Run as administrator: PowerShell -ExecutionPolicy Bypass -File .\scripts\setup-lm-studio-port-forwarding.ps1

param(
    [int]$Port = 1235  # Default port, can be overridden: -Port 1234
)

Write-Host "Setting up Port Forwarding for LM Studio (port $Port)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check administrator rights
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: Script must be run as administrator!" -ForegroundColor Red
    Write-Host "Run PowerShell as administrator and execute:" -ForegroundColor Yellow
    Write-Host "   PowerShell -ExecutionPolicy Bypass -File .\scripts\setup-lm-studio-port-forwarding.ps1 [-Port 1235]" -ForegroundColor Yellow
    exit 1
}

Write-Host "Administrator rights confirmed" -ForegroundColor Green
Write-Host ""

# Get Windows Host IP that WSL uses to connect to Windows
# WSL typically uses the IP from resolv.conf (usually 10.255.255.254 or similar)
Write-Host "Detecting Windows Host IP for WSL..." -ForegroundColor Yellow

# Try to get IP from WSL resolv.conf first
$wslHostIp = ""
try {
    # Используем более надежный способ извлечения IP
    $resolvContent = wsl bash -c "cat /etc/resolv.conf 2>/dev/null | grep '^nameserver' | awk '{print `$2}' | head -1" 2>$null
    if ($LASTEXITCODE -eq 0 -and $resolvContent) {
        $wslHostIp = $resolvContent.Trim()
        # Убираем возможные лишние символы
        $wslHostIp = $wslHostIp -replace '[^0-9.]', ''
        # Проверяем, что это валидный IP адрес
        if ($wslHostIp -match '^\d+\.\d+\.\d+\.\d+$') {
            Write-Host "   WSL resolv.conf nameserver: $wslHostIp" -ForegroundColor Cyan
        } else {
            $wslHostIp = ""
        }
    }
} catch {
    # WSL might not be available, continue
}

# If we got IP from WSL, use it
if ($wslHostIp -and $wslHostIp -ne "127.0.0.1") {
    $windowsHostIp = $wslHostIp
    Write-Host "   Using WSL nameserver IP: $windowsHostIp" -ForegroundColor Green
} else {
    # Fallback: detect Windows network IP
    Write-Host "   WSL resolv.conf not available, detecting Windows network IP..." -ForegroundColor Yellow
    $windowsHostIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
        $_.IPAddress -notlike '127.*' -and 
        $_.IPAddress -notlike '169.254.*' -and
        ($_.PrefixOrigin -eq 'Dhcp' -or $_.SuffixOrigin -eq 'Dhcp')
    } | Select-Object -First 1).IPAddress

    if (-not $windowsHostIp) {
        # Fallback: get first non-loopback IPv4
        $windowsHostIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
            $_.IPAddress -notlike '127.*' -and 
            $_.IPAddress -notlike '169.254.*'
        } | Select-Object -First 1).IPAddress
    }

    if (-not $windowsHostIp) {
        Write-Host "   Could not detect Windows Host IP automatically" -ForegroundColor Yellow
        Write-Host "   Make sure you have an active network connection" -ForegroundColor Yellow
        Write-Host ""
        $windowsHostIp = Read-Host "Enter Windows Host IP address manually (or press Enter to use 127.0.0.1)"
        if ([string]::IsNullOrWhiteSpace($windowsHostIp)) {
            Write-Host "   WARNING: Using 127.0.0.1 (may not work from WSL)" -ForegroundColor Yellow
            $windowsHostIp = "127.0.0.1"
        }
    } else {
        Write-Host "   Windows network IP: $windowsHostIp" -ForegroundColor Green
        Write-Host "   Note: If WSL uses different IP, you may need to specify it manually" -ForegroundColor Yellow
    }
}

Write-Host ""

# Port to forward
$port = $Port

# Remove old rules for this port (including any IP addresses)
Write-Host "Removing old port forwarding rules for port $port..." -ForegroundColor Yellow
# Получаем все текущие правила и удаляем те, что для нашего порта
$existingRules = netsh interface portproxy show all 2>$null
if ($existingRules) {
    $existingRules | ForEach-Object {
        if ($_ -match ":\s*${port}\s+") {
            # Извлекаем IP адрес из строки правила
            if ($_ -match "(\d+\.\d+\.\d+\.\d+)\s+${port}") {
                $oldIp = $matches[1]
                netsh interface portproxy delete v4tov4 listenport=$port listenaddress=$oldIp 2>$null | Out-Null
            }
        }
    }
}
# Также удаляем для стандартных адресов
netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>$null | Out-Null
netsh interface portproxy delete v4tov4 listenport=$port listenaddress=127.0.0.1 2>$null | Out-Null
if ($windowsHostIp -and $windowsHostIp -match '^\d+\.\d+\.\d+\.\d+$') {
    netsh interface portproxy delete v4tov4 listenport=$port listenaddress=$windowsHostIp 2>$null | Out-Null
}
Write-Host "   Old rules removed" -ForegroundColor Green

Write-Host ""

# Add port forwarding rule: from external interface to localhost
# This allows WSL to connect via Windows Host IP -> localhost
Write-Host "Adding port forwarding rule..." -ForegroundColor Yellow
Write-Host "   Forwarding: ${windowsHostIp}:${port} -> 127.0.0.1:${port}" -ForegroundColor Cyan
Write-Host "   This allows WSL to access LM Studio via Windows Host IP" -ForegroundColor Gray
netsh interface portproxy add v4tov4 listenport=$port listenaddress=$windowsHostIp connectport=$port connectaddress=127.0.0.1

if ($LASTEXITCODE -eq 0) {
    Write-Host "   Port forwarding rule added successfully" -ForegroundColor Green
} else {
    Write-Host "   ERROR: Failed to add port forwarding rule" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Configure Windows Firewall
Write-Host "Configuring Windows Firewall..." -ForegroundColor Yellow
$firewallRuleName = "Astra Trainer - LM Studio Port $port"

# Remove old firewall rule if exists
Remove-NetFirewallRule -DisplayName $firewallRuleName -ErrorAction SilentlyContinue

# Add new firewall rule
New-NetFirewallRule -DisplayName $firewallRuleName `
    -Direction Inbound `
    -LocalPort $port `
    -Protocol TCP `
    -Action Allow `
    -Profile Private, Domain `
    | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "   Firewall rule added successfully" -ForegroundColor Green
} else {
    Write-Host "   WARNING: Failed to add firewall rule. You may need to allow port $port manually in Windows Firewall" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Port forwarding configured successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "   Port: $port" -ForegroundColor White
Write-Host "   Forwarding: ${windowsHostIp}:${port} -> 127.0.0.1:${port}" -ForegroundColor White
Write-Host ""
Write-Host "Usage in WSL:" -ForegroundColor Cyan
Write-Host "   Use Windows Host IP: http://${windowsHostIp}:${port}/v1" -ForegroundColor White
Write-Host "   Or configure in backend/.env: LLM_API_URL=http://${windowsHostIp}:${port}/v1" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Yellow
Write-Host "   - Make sure LM Studio is running in Windows" -ForegroundColor White
Write-Host "   - LM Studio must listen on localhost:${port}" -ForegroundColor White
Write-Host "   - If Windows Host IP changes, run this script again" -ForegroundColor White
Write-Host ""
Write-Host "To verify:" -ForegroundColor Cyan
Write-Host "   In WSL: curl http://${windowsHostIp}:${port}/v1/models" -ForegroundColor White
Write-Host "   Or check from Windows: curl http://localhost:${port}/v1/models" -ForegroundColor White
Write-Host ""

