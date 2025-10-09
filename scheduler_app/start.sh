#!/bin/bash
# Flask Schedule Webapp - Linux/Mac Start Script
# Quick start script for running the application

echo "========================================"
echo "Flask Schedule Webapp - Starting..."
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo -e "${RED}ERROR: Virtual environment not found!${NC}"
    echo "Please run ./setup.sh first to set up the application."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}WARNING: .env file not found!${NC}"
    echo "Using default development configuration..."
    echo ""
fi

# Set Flask environment variables
export FLASK_APP=scheduler_app.app:create_app
export FLASK_ENV=development

# Start the application
echo "Starting Flask application..."
echo ""
echo -e "${GREEN}The application will be available at:${NC}"
echo "  http://127.0.0.1:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m flask run --host=0.0.0.0 --port=5000
