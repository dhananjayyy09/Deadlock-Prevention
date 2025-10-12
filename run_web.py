#!/usr/bin/env python3
"""
Simple launcher script for the web version of Deadlock Detection Tool
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    from web_app_simple import app
    print("🚀 Starting Deadlock Detection Tool Web Server...")
    print("📊 Open your browser and go to: http://localhost:5000")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
