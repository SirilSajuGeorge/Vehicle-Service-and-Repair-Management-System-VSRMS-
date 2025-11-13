#!/bin/bash

# VSRMS Docker Startup Script
# Makes it easy to run the Vehicle Service & Repair Management System

set -e

echo "🚗 Starting VSRMS (Vehicle Service & Repair Management System)"
echo "=================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Docker daemon is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is installed and running"

# Create instance directory if it doesn't exist
mkdir -p instance
echo "✅ Created instance directory for database"

# Build and start the application
echo "🔧 Building and starting VSRMS..."
docker-compose up --build -d

# Wait a moment for the application to start
echo "⏳ Waiting for application to start..."
sleep 10

# Check if the application is healthy
if docker-compose ps | grep -q "Up (healthy)"; then
    echo "✅ VSRMS is running successfully!"
elif docker-compose ps | grep -q "Up"; then
    echo "⚠️  VSRMS is starting up (health check in progress)..."
else
    echo "❌ VSRMS failed to start. Check logs with: docker-compose logs"
    exit 1
fi

echo ""
echo "🎉 VSRMS is now ready!"
echo "=================================================="
echo "🌐 Access the application at: http://localhost:5000"
echo "👨‍💼 Admin Login:"
echo "   📧 Email:    admin@vsrms.com"
echo "   🔐 Password: admin123"
echo ""
echo "📝 Useful Commands:"
echo "   🔍 View logs:        docker-compose logs -f"
echo "   ⏹️  Stop service:     docker-compose down"
echo "   🔄 Restart service:  docker-compose restart"
echo "   📊 Check status:     docker-compose ps"
echo ""
echo "⚠️  IMPORTANT: Change the default admin password after first login!"
echo "=================================================="
