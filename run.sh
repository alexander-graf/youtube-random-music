#!/bin/bash
# Navigate to project directory and start the app in the virtual environment
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
