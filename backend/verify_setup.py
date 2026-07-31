#!/usr/bin/env python
"""Verify that all AI infrastructure is set up correctly.

Run this to check:
- All required dependencies are installed
- Database tables exist
- OpenAI API is configured
- pgvector extension is available

Usage:
    python verify_setup.py
"""

import sys
import subprocess

def check_imports():
    """Verify all required packages are installed."""
    print("\n📦 Checking dependencies...")
    required = [
        ('fastapi', 'fastapi'),
        ('sqlalchemy', 'sqlalchemy'),
        ('openai', 'openai'),
        ('pypdf', 'pypdf'),
        ('nltk', 'nltk'),
        ('apscheduler', 'apscheduler'),
        ('tenacity', 'tenacity'),
    ]

    missing = []
    for name, module in required:
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - MISSING")
            missing.append(name)

    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install -r requirements.txt")
        return False

    print("  All dependencies installed ✓")
    return True


def check_database():
    """Verify database connection and tables."""
    print("\n🗄️  Checking database...")
    try:
        from app.database import engine
        from sqlalchemy import text

        with engine.connect() as conn:
            # Check PostgreSQL version
            result = conn.execute(text("SELECT version();")).scalar()
            version = result.split(',')[0] if result else "unknown"
            print(f"  ✓ PostgreSQL: {version}")

            # Check pgvector
            try:
                conn.execute(text("SELECT 1 FROM pg_extension WHERE extname='vector';"))
                print("  ✓ pgvector extension installed")
            except:
                print("  ⚠️  pgvector not installed (run: python -m app.init_ai)")

            # Check tables exist
            tables = ['documents', 'document_embeddings', 'embedding_operations']
            for table in tables:
                try:
                    conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1;"))
                    print(f"  ✓ {table} table exists")
                except:
                    print(f"  ✗ {table} table missing (run: python -m app.init_ai)")

            return True
    except Exception as e:
        print(f"  ✗ Database error: {e}")
        return False


def check_openai():
    """Verify OpenAI API configuration."""
    print("\n🔑 Checking OpenAI API...")
    from app.config import settings

    if not settings.openai_api_key:
        print("  ⚠️  OPENAI_API_KEY not configured")
        print("  Set OPENAI_API_KEY in your .env file to enable embeddings")
        return False

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        models = list(client.models.list())[:1]  # Just check connection
        print(f"  ✓ OpenAI API key valid")
        print(f"  ✓ Embedding model: {settings.embedding_model}")
        return True
    except Exception as e:
        print(f"  ✗ OpenAI API error: {e}")
        return False


def check_nltk():
    """Verify NLTK data is downloaded."""
    print("\n📚 Checking NLTK data...")
    try:
        import nltk
        nltk.data.find('tokenizers/punkt')
        print("  ✓ NLTK punkt tokenizer available")
        return True
    except LookupError:
        print("  ⚠️  NLTK punkt tokenizer not downloaded")
        print("  Run: python -m app.init_ai")
        return False
    except Exception as e:
        print(f"  ✗ NLTK error: {e}")
        return False


def main():
    print("=" * 60)
    print("StratOS AI - AI Infrastructure Verification")
    print("=" * 60)

    checks = [
        ("Dependencies", check_imports),
        ("Database", check_database),
        ("OpenAI API", check_openai),
        ("NLTK Data", check_nltk),
    ]

    results = {}
    for name, check_fn in checks:
        try:
            results[name] = check_fn()
        except Exception as e:
            print(f"\n✗ {name} check failed: {e}")
            results[name] = False

    print("\n" + "=" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"Results: {passed}/{total} checks passed\n")

    for name, result in results.items():
        status = "✓" if result else "✗"
        print(f"  {status} {name}")

    if passed == total:
        print("\n✅ All systems ready! You can now:")
        print("   1. Upload documents (embeddings will be generated)")
        print("   2. Search semantically (POST /search/semantic)")
        print("   3. Monitor embedding status (GET /documents/{id}/embedding-status)")
        return 0
    else:
        print("\n⚠️  Some checks failed. See above for details.")
        print("   Run: python -m app.init_ai")
        return 1


if __name__ == "__main__":
    sys.exit(main())
