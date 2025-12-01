#!/bin/bash

###############################################################################
# Flask Schedule Webapp - Docker Setup Script (Linux/Mac)
#
# This script sets up the application with Docker Compose
# Usage: ./setup.sh [dev|prod]
###############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         Flask Schedule Webapp - Docker Setup             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Determine environment (default: production)
ENVIRONMENT=${1:-prod}

DOCKER_DIR="deployment/docker"

if [ "$ENVIRONMENT" = "dev" ]; then
    print_info "Setting up DEVELOPMENT environment"
    COMPOSE_FILE="$DOCKER_DIR/docker-compose.dev.yml"
else
    print_info "Setting up PRODUCTION environment"
    COMPOSE_FILE="$DOCKER_DIR/docker-compose.yml"
fi

# Validate docker-compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    print_error "Docker Compose file not found: $COMPOSE_FILE"
    exit 1
fi

# Step 1: Check Docker installation
print_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    print_info "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi
print_success "Docker is installed: $(docker --version)"

# Step 2: Check Docker Compose installation
print_info "Checking Docker Compose installation..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed!"
    print_info "Please install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    print_success "Docker Compose is installed: $(docker-compose --version)"
else
    COMPOSE_CMD="docker compose"
    print_success "Docker Compose is installed: $(docker compose version)"
fi

# Step 3: Create .env file if it doesn't exist
print_info "Configuring environment variables..."
ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        print_success "Created .env file from .env.example"
    else
        print_error ".env.example file not found!"
        exit 1
    fi
else
    print_warning ".env file already exists, skipping..."
fi

# Step 4: Generate secure secrets
print_info "Generating secure secrets..."

# Generate SECRET_KEY
if ! grep -q "^SECRET_KEY=.*[a-f0-9]\{64\}" "$ENV_FILE"; then
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))' 2>/dev/null || openssl rand -hex 32)
    if [ -n "$SECRET_KEY" ]; then
        sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" "$ENV_FILE"
        print_success "Generated SECRET_KEY"
    else
        print_warning "Could not generate SECRET_KEY, please set it manually in $ENV_FILE"
    fi
fi

# Add Docker Compose variables to .env if not already present
print_info "Configuring Docker Compose variables..."

if ! grep -q "^POSTGRES_DB=" "$ENV_FILE"; then
    POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d /=+ | cut -c -32)
    REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d /=+ | cut -c -32)

    cat >> "$ENV_FILE" << EOF

# ===================================================================
# DOCKER COMPOSE VARIABLES (auto-generated)
# ===================================================================
POSTGRES_DB=crossmark_scheduler
POSTGRES_USER=scheduler_app
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_PORT=5432
REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_PORT=6379
APP_PORT=8000
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
EOF
    print_success "Added Docker Compose variables with secure passwords"
else
    print_warning "Docker Compose variables already exist, skipping..."
fi

# Step 5: Update DATABASE_URL in app .env
print_info "Updating database connection string..."
source "$ENV_FILE"
DB_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:${POSTGRES_PORT}/${POSTGRES_DB}"
sed -i.bak "s|^DATABASE_URL=.*|DATABASE_URL=$DB_URL|" "$ENV_FILE"
print_success "Updated DATABASE_URL in $ENV_FILE"

# Clean up backup files created by sed
rm -f "$ENV_FILE.bak" 2>/dev/null || true

# Step 6: Build Docker images
print_info "Building Docker images..."
$COMPOSE_CMD -f "$COMPOSE_FILE" build
print_success "Docker images built successfully"

# Step 7: Start containers
print_info "Starting containers..."
$COMPOSE_CMD -f "$COMPOSE_FILE" up -d
print_success "Containers started successfully"

# Step 8: Wait for database to be ready
print_info "Waiting for database to be ready..."
sleep 5

# Step 9: Run database migrations
print_info "Running database migrations..."
if [ "$ENVIRONMENT" = "dev" ]; then
    $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T app flask db upgrade
else
    $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T app flask db upgrade
fi
print_success "Database migrations completed"

# Step 10: Display status
echo ""
print_success "Setup completed successfully!"
echo ""
print_info "Container Status:"
$COMPOSE_CMD -f "$COMPOSE_FILE" ps

# Step 11: Display access information
echo ""
print_info "Application is running at:"
if [ "$ENVIRONMENT" = "dev" ]; then
    echo -e "  ${GREEN}http://localhost:5000${NC}"
else
    echo -e "  ${GREEN}http://localhost:8000${NC}"
fi

echo ""
print_info "Health Check:"
echo -e "  http://localhost:${APP_PORT:-8000}/health/ping"

echo ""
print_info "Useful Commands:"
echo -e "  View logs:    ${YELLOW}$COMPOSE_CMD -f $COMPOSE_FILE logs -f${NC}"
echo -e "  Stop app:     ${YELLOW}$COMPOSE_CMD -f $COMPOSE_FILE down${NC}"
echo -e "  Restart app:  ${YELLOW}$COMPOSE_CMD -f $COMPOSE_FILE restart${NC}"
echo -e "  Shell access: ${YELLOW}$COMPOSE_CMD -f $COMPOSE_FILE exec app /bin/bash${NC}"

echo ""
print_success "Happy scheduling! 🚀"
