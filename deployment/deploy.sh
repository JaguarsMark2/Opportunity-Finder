#!/bin/bash

# Opportunity Finder Production Deployment Script
# This script deploys the application to production

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups"
ENV_FILE="$PROJECT_ROOT/.env.production"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Opportunity Finder Deployment${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Check if .env.production exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: .env.production file not found${NC}"
    echo "Please copy deployment/.env.production.template to .env.production and fill in your values"
    exit 1
fi

# Source environment variables
echo -e "${YELLOW}Loading environment variables...${NC}"
set -a
source "$ENV_FILE"
set +a

# Create necessary directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p "$BACKUP_DIR"
mkdir -p "$PROJECT_ROOT/deployment/ssl"
mkdir -p "$PROJECT_ROOT/logs/nginx"
mkdir -p "$PROJECT_ROOT/logs/gunicorn"

# Check required variables
echo -e "${YELLOW}Checking required environment variables...${NC}"
required_vars=("SECRET_KEY" "POSTGRES_PASSWORD" "STRIPE_SECRET_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "${RED}Error: Missing required environment variables:${NC}"
    printf '%s\n' "${missing_vars[@]}"
    exit 1
fi

# Build frontend
echo -e "${YELLOW}Building frontend...${NC}"
cd "$PROJECT_ROOT/frontend"
npm install
npm run build

# Check if SSL certificates exist
if [ ! -f "$PROJECT_ROOT/deployment/ssl/cert.pem" ] || [ ! -f "$PROJECT_ROOT/deployment/ssl/key.pem" ]; then
    echo -e "${YELLOW}SSL certificates not found${NC}"
    echo "Please run 'sudo ./deployment/setup-ssl.sh your-domain.com' to set up SSL"
    echo "For now, using self-signed certificates for testing..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$PROJECT_ROOT/deployment/ssl/key.pem" \
        -out "$PROJECT_ROOT/deployment/ssl/cert.pem" \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Stop existing containers if running
echo -e "${YELLOW}Stopping existing containers...${NC}"
cd "$PROJECT_ROOT"
docker-compose -f docker-compose.prod.yml down

# Pull latest images
echo -e "${YELLOW}Pulling latest images...${NC}"
docker-compose -f docker-compose.prod.yml pull

# Build and start containers
echo -e "${YELLOW}Building and starting containers...${NC}"
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Run database migrations if needed
echo -e "${YELLOW}Running database migrations...${NC}"
docker-compose -f docker-compose.prod.yml exec -T backend \
    python -c "from app.db import init_db; init_db()"

# Check service health
echo -e "${YELLOW}Checking service health...${NC}"
if curl -sf http://localhost/health > /dev/null; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
fi

# Show running containers
echo ""
echo -e "${GREEN}Running containers:${NC}"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "Application is now running at:"
echo "  - HTTP:  http://localhost"
echo "  - HTTPS: https://localhost (self-signed)"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "To stop the application:"
echo "  docker-compose -f docker-compose.prod.yml down"
echo ""
