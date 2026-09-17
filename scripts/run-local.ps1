$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (!(Test-Path -LiteralPath $pythonPath)) { throw 'Create .venv and install requirements first.' }
$apiListener = Get-NetTCPConnection -LocalPort 8010 -State Listen -ErrorAction SilentlyContinue
$dashboardListener = Get-NetTCPConnection -LocalPort 8510 -State Listen -ErrorAction SilentlyContinue
if ($apiListener -or $dashboardListener) {
    throw 'Port 8010 or 8510 is already in use. The application may already be running; open its URL or stop the existing processes before restarting.'
}
$apiProcess = Start-Process -FilePath $pythonPath -ArgumentList '-m uvicorn api.main:app --host 127.0.0.1 --port 8010' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot 'api.log') -RedirectStandardError (Join-Path $projectRoot 'api-error.log') -PassThru
$dashboardProcess = Start-Process -FilePath $pythonPath -ArgumentList '-m streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8510 --server.headless true' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot 'dashboard.log') -RedirectStandardError (Join-Path $projectRoot 'dashboard-error.log') -PassThru
Write-Output "Started process IDs: API $($apiProcess.Id), dashboard $($dashboardProcess.Id). Logs are saved in the project directory."
Write-Output 'Dashboard: http://127.0.0.1:8510 | API docs: http://127.0.0.1:8010/docs'
