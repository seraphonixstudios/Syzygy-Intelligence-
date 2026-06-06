#!/bin/bash
# Production deployment configuration helper
# Usage: source scripts/setup-prod-env.sh

set -e

echo "Syzygy Intelligence - Production Setup"
echo "======================================"
echo ""

# Generate secure secret key
if [ -z "$SYZYGY_SECRET_KEY" ]; then
    echo "Generating SYZYGY_SECRET_KEY..."
    SECRET=$(openssl rand -hex 32)
    echo "SYZYGY_SECRET_KEY=$SECRET" >> .env.production
    echo "✓ Secret key generated and saved to .env.production"
else
    echo "✓ SYZYGY_SECRET_KEY already set"
fi

# Prompt for CORS origins
echo ""
echo "Enter CORS origins (comma-separated, e.g., https://example.com,https://app.example.com)"
read -p "SYZYGY_CORS_ORIGINS: " cors_origins
if [ -n "$cors_origins" ]; then
    echo "SYZYGY_CORS_ORIGINS=$cors_origins" >> .env.production
    echo "✓ CORS origins configured"
fi

# Prompt for environment
echo ""
read -p "Environment (development/production) [production]: " env_choice
env_choice=${env_choice:-production}
echo "SYZYGY_ENV=$env_choice" >> .env.production
echo "✓ Environment set to $env_choice"

# Database configuration
echo ""
read -p "Database host [postgres]: " db_host
db_host=${db_host:-postgres}
read -p "Database port [5432]: " db_port
db_port=${db_port:-5432}
read -s -p "Database password: " db_pass
echo ""
echo "SYZYGY_DB_HOST_DOCKER=$db_host" >> .env.production
echo "SYZYGY_DB_PORT=$db_port" >> .env.production
echo "SYZYGY_DB_PASSWORD=$db_pass" >> .env.production
echo "✓ Database configured"

echo ""
echo "Setup complete! Review and edit .env.production before deploying."
echo ""
