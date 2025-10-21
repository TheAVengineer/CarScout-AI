# Start Celery Workers for CarScout AI
# This script starts the worker processes needed for the pipeline

Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "🚀 Starting CarScout AI Workers" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Check if Redis is running
Write-Host "🔍 Checking Redis..." -ForegroundColor Yellow
$redisCheck = docker ps --filter "name=carscout-redis" --filter "status=running" --format "{{.Names}}"
if ($redisCheck -ne "carscout-redis") {
    Write-Host "❌ Redis is not running!" -ForegroundColor Red
    Write-Host "   Start it with: docker start carscout-redis" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Redis is running" -ForegroundColor Green
Write-Host ""

# Check if PostgreSQL is running
Write-Host "🔍 Checking PostgreSQL..." -ForegroundColor Yellow
$pgCheck = docker ps --filter "name=carscout-postgres" --filter "status=running" --format "{{.Names}}"
if ($pgCheck -ne "carscout-postgres") {
    Write-Host "❌ PostgreSQL is not running!" -ForegroundColor Red
    Write-Host "   Start it with: docker start carscout-postgres" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ PostgreSQL is running" -ForegroundColor Green
Write-Host ""

# Start Celery worker
Write-Host "⚙️  Starting Celery worker..." -ForegroundColor Yellow
Write-Host "   (Press Ctrl+C to stop)" -ForegroundColor Gray
Write-Host ""

celery -A workers.pipeline.celery_app worker --loglevel=info --pool=solo
