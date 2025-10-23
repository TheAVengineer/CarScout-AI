# Restart Celery Worker
Write-Host "🔄 Restarting Celery Worker..."

# Stop existing Celery processes
Get-Process -Name "celery" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*celery*"} | Stop-Process -Force

Write-Host "✅ Stopped old workers"
Start-Sleep -Seconds 2

# Start Celery worker
Write-Host "🚀 Starting Celery worker..."
$env:PYTHONPATH = "C:\CarScout-AI"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\CarScout-AI; .\venv\Scripts\activate; celery -A workers.pipeline.celery_app worker --loglevel=info --pool=solo"

Write-Host "✅ Celery worker restarted!"
Write-Host ""
Write-Host "💡 Check the new PowerShell window for worker logs"
