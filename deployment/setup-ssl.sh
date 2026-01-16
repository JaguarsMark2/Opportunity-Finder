#!/bin/bash

# SSL Certificate Setup Script using Let's Encrypt (Certbot)
# Usage: sudo ./deployment/setup-ssl.sh your-domain.com

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root (sudo)${NC}"
    exit 1
fi

# Check domain argument
if [ -z "$1" ]; then
    echo -e "${RED}Error: Domain name required${NC}"
    echo "Usage: sudo ./deployment/setup-ssl.sh your-domain.com"
    exit 1
fi

DOMAIN=$1
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSL_DIR="$PROJECT_ROOT/deployment/ssl"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}SSL Certificate Setup${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "Domain: $DOMAIN"
echo ""

# Create SSL directory
mkdir -p "$SSL_DIR"

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}Certbot not found. Installing...${NC}"

    # Detect OS
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        apt-get update
        apt-get install -y certbot
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS
        yum install -y certbot
    else
        echo -e "${RED}Error: Unable to detect OS. Please install certbot manually.${NC}"
        exit 1
    fi
fi

# Check if nginx is running (needed for domain validation)
if ! pgrep nginx > /dev/null; then
    echo -e "${YELLOW}Nginx is not running. Starting temporary nginx for validation...${NC}"

    # Create temporary nginx config
    cat > /tmp/nginx-temp.conf << EOF
events {}
http {
    server {
        listen 80;
        server_name $DOMAIN;

        location /.well-known/acme-challenge/ {
            root /tmp/certbot-webroot;
        }
    }
}
EOF

    mkdir -p /tmp/certbot-webroot
    nginx -c /tmp/nginx-temp.conf &
    NGINX_PID=$!
    sleep 2
fi

# Get certificate
echo -e "${YELLOW}Requesting SSL certificate from Let's Encrypt...${NC}"
certbot certonly --webroot -w /tmp/certbot-webroot -d "$DOMAIN" --email "admin@$DOMAIN" --agree-tos --non-interactive

# Copy certificates to project
echo -e "${YELLOW}Copying certificates to project...${NC}"
cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/cert.pem"
cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/key.pem"
chmod 644 "$SSL_DIR/cert.pem"
chmod 600 "$SSL_DIR/key.pem"

# Set up auto-renewal
echo -e "${YELLOW}Setting up auto-renewal cron job...${NC}"
(crontab -l 2>/dev/null; echo "0 0 * * * certbot renew --quiet --post-hook 'cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $SSL_DIR/cert.pem && cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $SSL_DIR/key.pem && docker restart opportunity-finder-nginx'") | crontab -

# Cleanup
if [ -n "$NGINX_PID" ]; then
    kill $NGINX_PID 2>/dev/null || true
    rm -f /tmp/nginx-temp.conf
fi

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}SSL Certificate Setup Complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "Certificate installed for: $DOMAIN"
echo "Certificate location: $SSL_DIR/"
echo ""
echo "Auto-renewal is configured via cron."
echo ""
echo "You can now deploy the application with:"
echo "  ./deployment/deploy.sh"
echo ""
