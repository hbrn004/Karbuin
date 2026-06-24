# setup_lan_access.ps1
# Run as Administrator (right-click PowerShell → Run as Administrator)
# Tujuan: buka port 8000 di Windows host agar HP Android di WiFi sama
#         bisa akses Karbuin yang running di WSL2.

$ErrorActionPreference = "Stop"
$port = 8000

# 1. Detect WSL IP
$wslIp = (wsl hostname -I).Trim().Split()[0]
Write-Host "WSL IP detected: $wslIp" -ForegroundColor Cyan

# 2. Add portproxy (Windows host:8000 → WSL:8000)
Write-Host "`n[1/3] Setting up port proxy..." -ForegroundColor Yellow
$existing = netsh interface portproxy show v4tov4 | Select-String ":$port"
if ($existing) {
    netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 | Out-Null
    Write-Host "  Removed existing rule"
}
netsh interface portproxy add v4tov4 `
    listenport=$port listenaddress=0.0.0.0 `
    connectport=$port connectaddress=$wslIp | Out-Null
Write-Host "  Done: Windows:8000 → WSL:$wslIp:8000" -ForegroundColor Green

# 3. Add firewall rule
Write-Host "`n[2/3] Opening Windows Firewall..." -ForegroundColor Yellow
$fwName = "Karbuin Web (port $port)"
$existingFw = Get-NetFirewallRule -DisplayName $fwName -ErrorAction SilentlyContinue
if ($existingFw) {
    Remove-NetFirewallRule -DisplayName $fwName | Out-Null
    Write-Host "  Removed existing rule"
}
New-NetFirewallRule -DisplayName $fwName `
    -Direction Inbound -Action Allow `
    -Protocol TCP -LocalPort $port `
    -Profile Any -EdgeTraversalPolicy Allow | Out-Null
Write-Host "  Done: firewall rule added" -ForegroundColor Green

# 4. Show status
Write-Host "`n[3/3] Verifying..." -ForegroundColor Yellow
Write-Host "`nPortproxy rules:" -ForegroundColor Cyan
netsh interface portproxy show v4tov4
Write-Host "`nFirewall rules:" -ForegroundColor Cyan
Get-NetFirewallRule -DisplayName $fwName | Format-Table DisplayName, Enabled, Direction, Action -AutoSize

# 5. Print LAN URLs
Write-Host "`n═══════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ Karbuin sekarang bisa diakses dari LAN" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
$ips = Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi*","Ethernet*" |
       Where-Object { $_.IPAddress -notlike "169.254*" -and $_.IPAddress -ne "127.0.0.1" } |
       ForEach-Object { $_.IPAddress }
foreach ($ip in $ips) {
    Write-Host "  → http://${ip}:${port}" -ForegroundColor White
}
Write-Host "`nHP Android harus konek WiFi yang sama. Buka URL di atas.`n"
