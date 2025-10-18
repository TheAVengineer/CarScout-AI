# Deployment Guide

## Prerequisites

- Docker and Docker Compose
- PostgreSQL 16+ with pgvector extension
- Redis 7+
- Object storage (R2/S3)
- Telegram Bot Token
- OpenAI API Key
- Stripe Account (for payments)

## Environment Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/CarScout-AI.git
cd CarScout-AI
```

2. **Copy environment template:**
```bash
cp .env.example .env
```

3. **Configure environment variables:**
Edit `.env` and set all required values:
- Database credentials
- Redis URL
- S3/R2 credentials
- Telegram bot tokens
- OpenAI API key
- Stripe keys

## Local Development

### Using Docker Compose

1. **Start all services:**
```bash
make docker-up
# or
docker-compose up -d
```

2. **Run database migrations:**
```bash
make migrate
# or
docker-compose exec api alembic upgrade head
```

3. **Check logs:**
```bash
docker-compose logs -f api
docker-compose logs -f worker-pipeline
```

4. **Access services:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Prometheus: http://localhost:9090

### Manual Setup

1. **Install dependencies:**
```bash
make dev-install
# or
pip install -e ".[dev]"
playwright install
```

2. **Start PostgreSQL and Redis:**
```bash
# Using Docker
docker run -d --name carscout-postgres \
  -e POSTGRES_USER=carscout \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=carscout_ai \
  -p 5432:5432 \
  pgvector/pgvector:pg16

docker run -d --name carscout-redis \
  -p 6379:6379 \
  redis:7-alpine
```

3. **Run migrations:**
```bash
alembic upgrade head
```

4. **Start API server:**
```bash
uvicorn apps.api.main:app --reload
```

5. **Start Celery workers:**
```bash
# In separate terminals
celery -A workers.pipeline.celery_app worker -Q scrape.new_raw -n worker-scrape@%h --concurrency=4
celery -A workers.pipeline.celery_app worker -Q parse.extract_fields,normalize.apply -n worker-pipeline@%h --concurrency=4
celery -A workers.pipeline.celery_app beat --loglevel=info
```

6. **Start Telegram bot:**
```bash
python -m apps.bot.main
```

## Production Deployment

### Option 1: Single VPS

1. **Provision a VPS** (recommended: 4 CPU, 8GB RAM)

2. **Install Docker and Docker Compose**

3. **Set up managed services:**
   - PostgreSQL: Neon, Supabase, or managed PostgreSQL
   - Redis: Upstash or Redis Cloud
   - S3: Cloudflare R2 or AWS S3

4. **Clone and configure:**
```bash
git clone https://github.com/yourusername/CarScout-AI.git
cd CarScout-AI
cp .env.example .env
# Edit .env with production values
```

5. **Deploy:**
```bash
docker-compose -f docker-compose.yml up -d
```

6. **Set up reverse proxy (Nginx):**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

7. **Enable SSL with Let's Encrypt:**
```bash
sudo certbot --nginx -d your-domain.com
```

### Option 2: Kubernetes

1. **Build and push Docker images:**
```bash
docker build -f infra/docker/Dockerfile.api -t your-registry/carscout-api:latest .
docker push your-registry/carscout-api:latest

docker build -f infra/docker/Dockerfile.bot -t your-registry/carscout-bot:latest .
docker push your-registry/carscout-bot:latest

docker build -f infra/docker/Dockerfile.worker -t your-registry/carscout-worker:latest .
docker push your-registry/carscout-worker:latest
```

2. **Create Kubernetes manifests** (see `infra/k8s/` for examples)

3. **Deploy:**
```bash
kubectl apply -f infra/k8s/
```

## Database Migrations

### Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations:
```bash
alembic upgrade head
```

### Rollback:
```bash
alembic downgrade -1
```

## Monitoring

### Prometheus Metrics
Access metrics at: `http://your-domain.com/metrics`

### Key Metrics to Monitor
- `carscout_scrape_pages_total` - Total pages scraped
- `carscout_listings_processed_total` - Listings processed
- `carscout_celery_task_duration_seconds` - Task duration
- `carscout_channel_posts_total` - Channel posts

### Alerting
Configure Prometheus alerts for:
- High error rates
- Queue backlogs
- Database connection issues
- API response time

## Backup and Recovery

### Database Backup:
```bash
pg_dump -h localhost -U carscout carscout_ai > backup.sql
```

### Restore:
```bash
psql -h localhost -U carscout carscout_ai < backup.sql
```

### Object Storage:
S3/R2 has built-in versioning and backups.

## Scaling

### Horizontal Scaling:
- Run multiple worker instances
- Use load balancer for API instances
- Scale Celery workers by queue

### Vertical Scaling:
- Increase worker concurrency
- Add more CPU/RAM to VPS
- Optimize database queries

## Troubleshooting

### Check service health:
```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/readiness
```

### View logs:
```bash
docker-compose logs -f [service-name]
```

### Access database:
```bash
make db-shell
```

### Access Redis:
```bash
make redis-shell
```

### Clear Celery queues:
```bash
celery -A workers.pipeline.celery_app purge
```
