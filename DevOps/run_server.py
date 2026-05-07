#!/usr/bin/env python
"""Simple Flask test server launcher"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
