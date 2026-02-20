import asyncio
from sqlalchemy import  text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import create_engine

# --- CONFIGURATION ---
# Replace these with your actual credentials
DB_USER = "postgres"
DB_PASS = "Bit_2024"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "pypdfsearcherdb"

# URLs
sync_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
async_url = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def test_sync_connection():
    """Tests the connection Alembic uses (psycopg2)"""
    print(f"--- Testing Sync Connection (Alembic Style) ---")
    try:
        engine = create_engine(sync_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✅ Success! Database responded with: {result.scalar()}")
    except Exception as e:
        print(f"❌ Sync Connection Failed!")
        print(f"Error: {e}")


async def test_async_connection():
    """Tests the connection FastAPI uses (asyncpg)"""
    print(f"\n--- Testing Async Connection (FastAPI Style) ---")
    try:
        engine = create_async_engine(async_url)
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"✅ Success! Database responded with: {result.scalar()}")
        await engine.dispose()
    except Exception as e:
        print(f"❌ Async Connection Failed!")
        print(f"Error: {e}")


if __name__ == "__main__":
    # Test Sync first (Alembic)
    test_sync_connection()

    # Test Async second (FastAPI)
    asyncio.run(test_async_connection())