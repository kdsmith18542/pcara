#!/bin/bash

# PCARA Development Startup Script

echo "🚀 Starting PCARA Development Environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your GEMINI_API_KEY before continuing."
    echo "   You can get a free API key from https://ai.google.dev/"
    exit 1
fi

# Check if GEMINI_API_KEY is set
if ! grep -q "GEMINI_API_KEY=your_gemini_api_key_here" .env; then
    echo "✅ GEMINI_API_KEY appears to be configured"
else
    echo "⚠️  Please set your GEMINI_API_KEY in the .env file"
    echo "   You can get a free API key from https://ai.google.dev/"
    exit 1
fi

echo "🐳 Building and starting Docker containers..."

# Stop any existing containers
docker-compose -f docker-compose.dev.yml down

# Build and start services
docker-compose -f docker-compose.dev.yml up --build -d

echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service status..."

# Check if PostgreSQL is ready
if docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U pcara_user > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Check if Redis is ready
if docker-compose -f docker-compose.dev.yml exec redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# Check if API Gateway is responding
if curl -s http://localhost:8081/health > /dev/null; then
    echo "✅ API Gateway is ready"
else
    echo "❌ API Gateway is not ready"
fi

# Check if Frontend is ready
if curl -s http://localhost:3001 > /dev/null; then
    echo "✅ Frontend is ready"
else
    echo "❌ Frontend is not ready"
fi

echo ""
echo "🎉 PCARA Development Environment Started!"
echo ""
echo "📍 Service URLs:"
echo "   Frontend:    http://localhost:3001"
echo "   API Gateway: http://localhost:8081"
echo "   API Docs:    http://localhost:8081/docs"
echo "   ChromaDB:    http://localhost:8001"
echo ""
echo "📋 Next steps:"
echo "   1. Open http://localhost:3001 in your browser"
echo "   2. Register a new account"
echo "   3. Add a repository for analysis"
echo ""
echo "🔍 To view logs:"
echo "   docker-compose -f docker-compose.dev.yml logs -f [service_name]"
echo ""
echo "🛑 To stop:"
echo "   docker-compose -f docker-compose.dev.yml down"