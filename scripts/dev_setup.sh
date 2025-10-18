#!/bin/bash
set -e

echo "🚀 CarScout AI - Development Environment Setup"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
echo "📦 Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please update .env with your actual credentials:${NC}"
    echo "   - OPENAI_API_KEY"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - TELEGRAM_CHANNEL_ID"
    echo ""
    read -p "Press Enter after updating .env file..."
fi
echo -e "${GREEN}✅ .env file exists${NC}"
echo ""

# Start infrastructure services
echo "🐳 Starting infrastructure services (PostgreSQL, Redis)..."
docker-compose up -d postgres redis
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Wait for PostgreSQL
until docker-compose exec -T postgres pg_isready -U carscout > /dev/null 2>&1; do
    echo "   Still waiting for PostgreSQL..."
    sleep 2
done
echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
echo ""

# Create Python virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Created virtual environment${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate
echo -e "${GREEN}✅ Activated virtual environment${NC}"
echo ""

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -e ".[dev]"
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head
echo -e "${GREEN}✅ Database migrations complete${NC}"
echo ""

# Seed database
echo "🌱 Seeding database with initial data..."
python scripts/seed_database.py
echo -e "${GREEN}✅ Database seeded${NC}"
echo ""

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d
echo -e "${GREEN}✅ All services started${NC}"
echo ""

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Show service status
echo ""
echo "📊 Service Status:"
echo "=================="
docker-compose ps
echo ""

# Show logs tail
echo "📜 Recent logs:"
echo "==============="
docker-compose logs --tail=20
echo ""

# Show access URLs
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo "🌐 Access URLs:"
echo "   API:        http://localhost:8000"
echo "   API Docs:   http://localhost:8000/docs"
echo "   Prometheus: http://localhost:9090"
echo "   Flower:     http://localhost:5555"
echo ""
echo "📝 Useful commands:"
echo "   View logs:         docker-compose logs -f"
echo "   Stop services:     docker-compose down"
echo "   Restart services:  docker-compose restart"
echo "   Run scraper:       docker-compose exec worker scrapy crawl mobile_bg"
echo "   Open shell:        docker-compose exec api python"
echo "   Run tests:         docker-compose exec api pytest"
echo ""
echo "🔧 Next steps:"
echo "   1. Update .env with your credentials"
echo "   2. Test the API at http://localhost:8000/docs"
echo "   3. Run a scraper: docker-compose exec worker scrapy crawl mobile_bg"
echo "   4. Check Flower for task monitoring: http://localhost:5555"
echo ""
