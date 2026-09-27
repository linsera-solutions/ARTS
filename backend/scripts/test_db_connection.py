"""
Standalone verification script for ARTS Supabase / PostgreSQL database connection.
Run this after populating your credentials in backend/.env:
    python scripts/test_db_connection.py
"""

import sys
from pathlib import Path

# Add backend root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.db.connection import verify_database_connection


def main():
    print("=" * 60)
    print("ARTS MVP - Database Connection Verification")
    print("=" * 60)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"PostgreSQL Configured (DATABASE_URL): {'YES' if settings.DATABASE_URL else 'NO'}")
    print(f"Supabase Configured (SUPABASE_URL): {'YES' if settings.SUPABASE_URL else 'NO'}")
    print("-" * 60)

    result = verify_database_connection()

    print(f"PostgreSQL Connection: {'SUCCESS' if result.get('postgres_connected') else 'NOT CONNECTED'}")
    if result.get("postgres_error"):
        print(f"  Reason: {result['postgres_error']}")

    print(f"Supabase SDK Client: {'READY' if result.get('supabase_client_ready') else 'NOT READY'}")
    if result.get("supabase_error"):
        print(f"  Reason: {result['supabase_error']}")

    print("-" * 60)
    print(f"Status Summary: {result.get('message')}")
    print("=" * 60)

    if not result.get("postgres_connected") and not result.get("supabase_client_ready"):
        print("\nNext Step:")
        print("To connect your database, copy backend/.env.example to backend/.env")
        print("and fill in your Supabase project credentials.")
        sys.exit(0)


if __name__ == "__main__":
    main()
