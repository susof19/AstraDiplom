# Скрипт для проверки настроек port forwarding
param(
    [int]$Port = 1235
)

Write-Host "Checking port forwarding for port ${Port}" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Проверка текущих правил port forwarding
Write-Host "Current port forwarding rules:" -ForegroundColor Yellow
$rules = netsh interface portproxy show all 2>$null

$portPattern = ":${Port} "
if ($rules -match $portPattern) {
    Write-Host "   Found rules for port ${Port}:" -ForegroundColor Green
    $rules | Select-String $portPattern | ForEach-Object {
        Write-Host "   $_" -ForegroundColor White
    }
} else {
    Write-Host "   No rules found for port ${Port}" -ForegroundColor Red
}

Write-Host ""

# Проверка firewall правил
Write-Host "Windows Firewall rules:" -ForegroundColor Yellow
$firewallRules = Get-NetFirewallRule -DisplayName "*LM Studio*" -ErrorAction SilentlyContinue
if ($firewallRules) {
    Write-Host "   Found firewall rules:" -ForegroundColor Green
    $firewallRules | ForEach-Object {
        Write-Host "   - $($_.DisplayName) (Enabled: $($_.Enabled))" -ForegroundColor White
    }
} else {
    Write-Host "   No firewall rules found for LM Studio" -ForegroundColor Yellow
}

Write-Host ""

# Показать все правила port forwarding
Write-Host "All port forwarding rules:" -ForegroundColor Yellow
$allRules = netsh interface portproxy show all 2>$null
if ($allRules) {
    Write-Host "$allRules" -ForegroundColor White
} else {
    Write-Host "   No port forwarding rules found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
