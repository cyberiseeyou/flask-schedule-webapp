#!/bin/bash
# Flask Schedule Webapp - Linux/Mac Setup Script
# This script sets up the application environment and dependencies

set -e  # Exit on error

echo "========================================"
echo "Flask Schedule Webapp - Setup Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
echo "[1/7] Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed${NC}"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "[2/7] Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created successfully${NC}"
else
    echo ""
    echo "[2/7] Virtual environment already exists, skipping..."
fi

# Activate virtual environment
echo ""
echo "[3/7] Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "[4/7] Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "[5/7] Installing dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}Dependencies installed successfully${NC}"
else
    echo -e "${YELLOW}WARNING: requirements.txt not found, skipping dependency installation${NC}"
fi

# Create necessary directories
echo ""
echo "[6/7] Creating necessary directories..."
mkdir -p scheduler_app/instance
mkdir -p scheduler_app/logs
mkdir -p scheduler_app/uploads
mkdir -p edr_printer
echo -e "${GREEN}Directories created${NC}"

# Setup environment file
echo ""
echo "[7/7] Setting up environment configuration..."
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cat > .env << 'EOF'
# Flask Schedule Webapp Configuration
# Copy this file to .env and update with your actual values

# Flask Configuration
FLASK_APP=scheduler_app.app:create_app
FLASK_ENV=development
SECRET_KEY=change-this-to-a-random-secret-key-in-production

# Database Configuration
DATABASE_URL=sqlite:///instance/scheduler.db

# Crossmark API Configuration
CROSSMARK_API_URL=https://api.crossmark.com
CROSSMARK_USERNAME=your_username_here
CROSSMARK_PASSWORD=your_password_here

# Sync Configuration
SYNC_ENABLED=false
AUTO_SYNC_INTERVAL=3600

# Logging
LOG_LEVEL=INFO
LOG_FILE=scheduler_app/logs/app.log
EOF
    echo -e "${YELLOW}.env file created - Please update with your actual configuration values${NC}"
else
    echo ".env file already exists, skipping..."
fi

# Initialize database
echo ""
echo "========================================"
echo "Database Initialization"
echo "========================================"
echo ""
read -p "Would you like to initialize the database now? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Initializing database..."
    cd scheduler_app
    python3 -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized successfully')"
    cd ..
    echo -e "${GREEN}Database initialized successfully${NC}"
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Update .env file with your actual configuration values"
echo "2. Run 'source venv/bin/activate' to activate the virtual environment"
echo "3. Run 'python -m scheduler_app.app' to start the application"
echo ""
echo "For development:"
echo "  export FLASK_APP=scheduler_app.app:create_app"
echo "  export FLASK_ENV=development"
echo "  flask run"
echo ""
echo "Or use the start script:"
echo "  ./start.sh"
echo ""
