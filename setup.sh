#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up Reading Agent environment...${NC}"

# Check if config.yaml exists
if [ -f "config.yaml" ]; then
    echo -e "${RED}Warning: config.yaml already exists. Please backup and remove it first.${NC}"
    exit 1
fi

# Create config.yaml from example
if [ -f "config.yaml.example" ]; then
    cp config.yaml.example config.yaml
    echo -e "${GREEN}Created config.yaml from example${NC}"
else
    echo -e "${RED}Error: config.yaml.example not found${NC}"
    exit 1
fi

# Create .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}Created .env from example${NC}"
        echo -e "${YELLOW}Please edit .env with your actual values${NC}"
    else
        echo -e "${RED}Error: .env.example not found${NC}"
        exit 1
    fi
fi

# Create necessary directories
mkdir -p data logs backups

# Set proper permissions
chmod 700 data logs backups
chmod 600 .env config.yaml

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit .env with your actual values"
echo "2. Edit config.yaml with your desired configuration"
echo "3. Run 'pip install -r requirements.txt' to install dependencies" 