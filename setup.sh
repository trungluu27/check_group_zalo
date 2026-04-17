#!/bin/bash

# Setup script for Zalo Group Membership Checker
# This script sets up the project environment on macOS

echo "🚀 Setting up Zalo Group Membership Checker..."
echo ""

# Check if Python 3.9+ is installed
echo "📦 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Found Python $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv
if [ $? -eq 0 ]; then
    echo "✅ Virtual environment created"
else
    echo "❌ Failed to create virtual environment"
    exit 1
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip
echo ""

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo ""

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium
if [ $? -eq 0 ]; then
    echo "✅ Playwright browsers installed"
else
    echo "❌ Failed to install Playwright browsers"
    exit 1
fi
echo ""

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p output
mkdir -p logs
mkdir -p resources
echo "✅ Directories created"
echo ""

# Create sample Excel file
echo "📊 Creating sample Excel file..."
python3 resources/create_sample_excel.py
if [ $? -eq 0 ]; then
    echo "✅ Sample Excel file created"
else
    echo "⚠️  Could not create sample Excel file (optional)"
fi
echo ""

echo "✨ Setup complete!"
echo ""
echo "To run the application:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run the application: python src/main.py"
echo ""
echo "Or simply run: ./run.sh"
echo ""
