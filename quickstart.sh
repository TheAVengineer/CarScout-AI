#!/bin/bash

# CarScout AI - Quick Start Script
# This script helps you get started quickly with the project

set -e

echo "🚗 CarScout AI - Quick Start"
echo "============================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual credentials before proceeding!"
    echo ""
    read -p "Press Enter once you've updated .env file, or Ctrl+C to exit..."
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Start services
echo "🚀 Starting Docker services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
else
    echo "❌ Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi

echo ""
echo "🗄️  Running database migrations..."
docker-compose exec -T api alembic upgrade head || echo "⚠️  Migrations will run on first API start"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Access the application:"
echo "   API:        http://localhost:8000"
echo "   API Docs:   http://localhost:8000/docs"
echo "   Prometheus: http://localhost:9090"
echo ""
echo "📝 Useful commands:"
echo "   View logs:       docker-compose logs -f"
echo "   Stop services:   docker-compose down"
echo "   Restart:         docker-compose restart"
echo "   DB shell:        make db-shell"
echo "   Redis shell:     make redis-shell"
echo ""
echo "📖 Next steps:"
echo "   1. Configure your Telegram bot token in .env"
echo "   2. Set up OpenAI API key for AI features"
echo "   3. Configure Stripe for subscriptions"
echo "   4. Read the documentation in docs/"
echo ""
echo "Happy car hunting! 🎯"
