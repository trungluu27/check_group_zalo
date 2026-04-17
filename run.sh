#!/bin/bash

# Run script for Zalo Group Membership Checker

echo "🚀 Starting Zalo Group Membership Checker..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Run the application
python src/main.py
