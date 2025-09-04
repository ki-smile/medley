#!/bin/bash

# MEDLEY Deployment Script
# Author: Farhad Abtahi - SMAILE at Karolinska Institutet

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   MEDLEY Deployment Script v1.0        ║${NC}"
echo -e "${BLUE}║   Medical AI Ensemble System           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Check Docker and Docker Compose
echo -e "${YELLOW}Checking prerequisites...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose found${NC}"

# Load environment variables if .env exists
if [ -f "../.env" ]; then
    echo -e "${GREEN}✓ Loading environment variables from .env${NC}"
    export $(cat ../.env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}⚠ No .env file found${NC}"
fi

# Check required environment variables
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo -e "${YELLOW}Warning: OPENROUTER_API_KEY not set${NC}"
    echo "The system will run with limited functionality"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Deployment mode selection
echo ""
echo "Select deployment mode:"
echo "1) Development (HTTP only, localhost)"
echo "2) Production with SSL (HTTPS, requires domain)"
echo "3) Production without SSL (HTTP only)"
read -p "Enter choice [1-3]: " mode

case $mode in
    1)
        echo -e "${GREEN}Starting in development mode...${NC}"
        export DOMAIN_NAME=localhost
        docker-compose up -d web redis
        ;;
    2)
        echo -e "${GREEN}Starting in production mode with SSL...${NC}"
        read -p "Enter your domain name (e.g., medley.example.com): " domain
        read -p "Enter your email for SSL certificates: " email
        
        export DOMAIN_NAME=$domain
        
        # Setup SSL if not already done
        if [ ! -d "certbot/conf/live/${domain}" ]; then
            ./scripts/setup-ssl.sh $domain $email
        fi
        
        docker-compose up -d
        ;;
    3)
        echo -e "${GREEN}Starting in production mode without SSL...${NC}"
        read -p "Enter your domain/IP (e.g., medley.example.com or 192.168.1.100): " domain
        
        export DOMAIN_NAME=$domain
        docker-compose up -d web redis nginx
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Health check
echo -e "${YELLOW}Running health check...${NC}"
if [ "$mode" == "1" ]; then
    health_url="http://localhost:5000/api/health"
else
    health_url="http://localhost/api/health"
fi

if curl -f -s $health_url > /dev/null; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo "Check logs with: docker-compose logs"
fi

# Display status
echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Deployment Complete!                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

docker-compose ps

echo ""
echo "Access MEDLEY at:"
if [ "$mode" == "1" ]; then
    echo -e "${BLUE}http://localhost:5000${NC}"
elif [ "$mode" == "2" ]; then
    echo -e "${BLUE}https://${domain}${NC}"
else
    echo -e "${BLUE}http://${domain}${NC}"
fi

echo ""
echo "Useful commands:"
echo "  View logs:        docker-compose logs -f"
echo "  Stop services:    docker-compose stop"
echo "  Restart services: docker-compose restart"
echo "  Remove all:       docker-compose down -v"