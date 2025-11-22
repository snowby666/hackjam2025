#!/bin/bash

# Screenshot Sherlock Setup Script

echo "📱 Setting up Screenshot Sherlock..."

# Backend setup
echo "🔧 Setting up backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo "Installing Tookie-OSINT dependencies..."
pip install -r tookie-osint/requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env with your API keys and MongoDB URL"
fi

cd ..

# Extension setup
echo "🔌 Extension is ready to load in Chrome"
echo ""
echo "To load extension:"
echo "1. Open Chrome and go to chrome://extensions/"
echo "2. Enable 'Developer mode'"
echo "3. Click 'Load unpacked'"
echo "4. Select the 'extension' directory"
echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your credentials"
echo "2. Start backend: cd backend && source venv/bin/activate && python main.py"
echo "   Or use: daphne -b 127.0.0.1 -p 8000 main:app"
echo "3. Load extension in Chrome"
echo "4. Start analyzing conversations!"

