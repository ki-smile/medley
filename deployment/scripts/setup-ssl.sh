#!/bin/bash

# MEDLEY SSL Setup Script for Let's Encrypt
# Author: Farhad Abtahi - SMAILE at Karolinska Institutet

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}MEDLEY SSL Certificate Setup${NC}"
echo "================================"

# Check if domain is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Domain name required${NC}"
    echo "Usage: ./setup-ssl.sh your-domain.com your-email@example.com"
    exit 1
fi

if [ -z "$2" ]; then
    echo -e "${RED}Error: Email address required${NC}"
    echo "Usage: ./setup-ssl.sh your-domain.com your-email@example.com"
    exit 1
fi

DOMAIN=$1
EMAIL=$2

echo -e "${YELLOW}Setting up SSL for domain: ${DOMAIN}${NC}"
echo -e "${YELLOW}Contact email: ${EMAIL}${NC}"

# Export environment variables
export DOMAIN_NAME=${DOMAIN}

# Create required directories
echo -e "${GREEN}Creating certificate directories...${NC}"
mkdir -p certbot/www certbot/conf

# Check if certificates already exist
if [ -d "certbot/conf/live/${DOMAIN}" ]; then
    echo -e "${YELLOW}Certificates already exist for ${DOMAIN}${NC}"
    read -p "Do you want to renew them? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping certificate generation"
        exit 0
    fi
fi

# Start nginx with HTTP only for initial certificate generation
echo -e "${GREEN}Starting nginx for certificate validation...${NC}"
docker-compose up -d nginx

# Wait for nginx to be ready
sleep 5

# Generate certificates
echo -e "${GREEN}Requesting SSL certificates from Let's Encrypt...${NC}"
docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email ${EMAIL} \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d ${DOMAIN} \
    -d www.${DOMAIN}

# Generate Diffie-Hellman parameters if not exists
if [ ! -f "certbot/conf/ssl-dhparams.pem" ]; then
    echo -e "${GREEN}Generating Diffie-Hellman parameters...${NC}"
    openssl dhparam -out certbot/conf/ssl-dhparams.pem 2048
fi

# Restart nginx with SSL configuration
echo -e "${GREEN}Restarting nginx with SSL configuration...${NC}"
docker-compose restart nginx

echo -e "${GREEN}✓ SSL setup complete!${NC}"
echo ""
echo "Your MEDLEY instance is now available at:"
echo -e "${GREEN}https://${DOMAIN}${NC}"
echo ""
echo "Certificate will auto-renew every 60 days."
echo ""
echo "To manually renew certificates, run:"
echo "docker-compose run --rm certbot renew"