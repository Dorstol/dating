#!/bin/bash
# First-time SSL certificate setup
# Usage: ./scripts/init-ssl.sh

set -euo pipefail

DOMAIN="dorstol.duckdns.org"
COMPOSE_FILE="docker-compose.prod.yml"

echo "=== Step 1: Temporary nginx config (HTTP only) ==="
cat > /tmp/nginx-temp.conf << 'NGINX'
server {
    listen 80;
    server_name dorstol.duckdns.org;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
NGINX

# Backup original config and use temp
cp nginx/nginx.conf nginx/nginx.conf.bak
cp /tmp/nginx-temp.conf nginx/nginx.conf

echo "=== Step 2: Restart nginx with temp config ==="
docker compose -f "$COMPOSE_FILE" up -d nginx

echo "=== Step 3: Get SSL certificate ==="
docker compose -f "$COMPOSE_FILE" run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email admin@$DOMAIN \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN"

echo "=== Step 4: Restore full nginx config ==="
cp nginx/nginx.conf.bak nginx/nginx.conf
rm nginx/nginx.conf.bak

echo "=== Step 5: Restart nginx with SSL ==="
docker compose -f "$COMPOSE_FILE" restart nginx

echo "=== Done! HTTPS should be available at https://$DOMAIN ==="
