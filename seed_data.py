#!/usr/bin/env python
"""
Simple script to seed the database with demo data.
Run this script to populate your Lead Management System with realistic data.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.core.management import call_command
from django.db import IntegrityError

def main():
    """Main function to run the data seeding command."""
    print("🌱 Seeding Lead Management System with demo data...")
    print("=" * 50)
    
    try:
        # Run the setup_demo_data command
        # You can modify these parameters:
        # --clear: Clear existing data before seeding
        # --leads: Number of leads to create (default: 100)
        
        call_command('setup_demo_data', '--leads', '150')
        
        print("\n✅ Data seeding completed successfully!")
        print("\n📋 Login Credentials (username = password):")
        print("=" * 40)
        print("👑 Organizers:")
        print("   • admin/admin")
        print("   • manager/manager") 
        print("   • director/director")
        print("\n👥 Agents:")
        print("   • john/john")
        print("   • jane/jane")
        print("   • mike/mike")
        print("   • sarah/sarah")
        print("   • david/david")
        print("   • lisa/lisa")
        print("   • james/james")
        print("   • emma/emma")
        print("   • alex/alex")
        print("   • sophia/sophia")
        print("   • daniel/daniel")
        print("   • olivia/olivia")
        print("   • chris/chris")
        print("   • amanda/amanda")
        print("   • kevin/kevin")
        print("\n🎯 All agents have the same username and password for easy testing!")
        print("\n🚀 Start your server and login to see the demo data!")
        
    except IntegrityError as e:
        print(f"❌ Database integrity error: {e}")
        print("\n💡 This usually means some data already exists.")
        print("   Try running with --clear flag to remove existing data:")
        print("   python manage.py setup_demo_data --clear --leads 150")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Make sure your database is migrated: python manage.py migrate")
        print("   2. Check if you have existing users with conflicting usernames")
        print("   3. Try running with --clear flag to start fresh")
        sys.exit(1)

if __name__ == '__main__':
    main() 