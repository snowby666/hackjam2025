"""
Startup script to initialize database on server start
"""
import asyncio
from database import init_database


async def startup():
    """Initialize database connection"""
    try:
        await init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise


import uvicorn
import sys
import asyncio

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    asyncio.run(startup())

