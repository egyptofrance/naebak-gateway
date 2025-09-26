#!/usr/bin/env python3
"""
Simple startup script for Naebak Gateway Service
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main gateway application
if __name__ == '__main__':
    from gateway import app
    
    # Set default configuration if not provided
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_RUN_PORT', 8007))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting Naebak Gateway on {host}:{port}")
    
    try:
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        print(f"Failed to start gateway: {e}")
        sys.exit(1)
