# Reset App Database
# This script clears the app database and re-syncs from main database
# Use this to clean up test data or start fresh

import os
import sqlite3


def reset_app_database():
    """Reset app database and resync from main database."""
    app_db = "data/app_data.db"
    
    if os.path.exists(app_db):
        print(f"Removing existing app database: {app_db}")
        os.remove(app_db)
        print("Done!")
    else:
        print("App database doesn't exist, nothing to reset.")
    
    print("\nTo resync from main database, run:")
    print("  python demo_database_sync.py")
    print("\nOr initialize ProfileRepository in your code.")


if __name__ == "__main__":
    confirm = input("This will delete all app data. Continue? (y/N): ")
    if confirm.lower() == 'y':
        reset_app_database()
    else:
        print("Cancelled.")
