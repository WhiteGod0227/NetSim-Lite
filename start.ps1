$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (!(Test-Path '.venv\Scripts\python.exe')) { throw 'Follow the first-time setup in README.md before launching.' }
if (!(Test-Path 'frontend\node_modules')) { throw 'Run npm.cmd install in frontend first.' }
foreach ($port in @(8000,5173)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
        throw "Port $port is already in use. If NetSim is already running, open http://127.0.0.1:5173. Otherwise stop the existing service before launching."
    }
}
$backend = Start-Process -FilePath "$PSScriptRoot\.venv\Scripts\python.exe" -ArgumentList '-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru
try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 25; $attempt++) {
        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 1
            if ($health.status -eq 'ok') { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 200 }
        if ($backend.HasExited) { throw 'Backend failed to start. Run the backend command in README.md to view its error.' }
    }
    if (!$ready) { throw 'Backend did not become ready on port 8000.' }
    Write-Host 'NetSim Lite: http://127.0.0.1:5173 — Ctrl+C to stop'
    Set-Location -LiteralPath "$PSScriptRoot\frontend"
    npm.cmd run dev -- --strictPort
} finally {
    # Windows virtual-environment Python may launch a child interpreter.
    Get-CimInstance Win32_Process -Filter "ParentProcessId = $($backend.Id)" -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -eq 'python.exe' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
    if (!$backend.HasExited) { Stop-Process -Id $backend.Id }
}
