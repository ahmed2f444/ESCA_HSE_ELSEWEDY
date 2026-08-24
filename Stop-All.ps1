Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "Stopping ESCA HSE Management System (Ports 8080, 8000, 5180)" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host ""

$processes = Get-NetTCPConnection -LocalPort 8080, 8000, 5180 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

if ($processes) {
    foreach ($pid_val in $processes) {
        try {
            $p = Get-Process -Id $pid_val -ErrorAction SilentlyContinue
            if ($p) {
                Write-Host "Stopping process: $($p.ProcessName) (PID: $pid_val)..." -ForegroundColor Yellow
                Stop-Process -Id $pid_val -Force -ErrorAction SilentlyContinue
            }
        } catch {}
    }
    Write-Host "`nAll ESCA HSE services stopped successfully." -ForegroundColor Green
} else {
    Write-Host "No running services found on ports 8080, 8000, or 5180." -ForegroundColor Green
}

Write-Host "=======================================================================" -ForegroundColor Cyan
