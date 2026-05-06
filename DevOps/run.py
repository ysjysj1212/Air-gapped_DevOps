#!/usr/bin/env python
"""Entry point for Flask app"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
