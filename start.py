#!/usr/bin/env python3
"""
Simple startup script for the Lead Management System.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main function to start the Django development server."""
    print("=" * 50)
    print("Lead Management System")
    print("=" * 50)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Virtual environment not detected!")
        print("Please activate your virtual environment first:")
        print("  Windows: .\\venv\\Scripts\\Activate.ps1")
        print("  Linux/Mac: source venv/bin/activate")
        print()
    
    # Check if requirements are installed
    try:
        import django
        print(f"✅ Django {django.get_version()} is installed")
    except ImportError:
        print("❌ Django not found. Please install requirements:")
        print("  pip install -r requirements.txt")
        return
    
    # Run migrations
    print("\n🔄 Running database migrations...")
    try:
        subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
        print("✅ Migrations completed")
    except subprocess.CalledProcessError:
        print("❌ Migration failed")
        return
    
    # Start the server
    print("\n🚀 Starting Django development server...")
    print("Server will be available at: http://127.0.0.1:8000")
    print("Admin login: http://127.0.0.1:8000/admin")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        subprocess.run([sys.executable, "manage.py", "runserver"])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    main() 