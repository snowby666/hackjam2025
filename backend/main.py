import sys
import asyncio

# Configure Windows asyncio loop policy
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
from daphne.cli import CommandLineInterface
import logging

from config import settings
from api import auth, screenshot, analysis, wingman, conversations, osint
from database import init_database

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}. Server will start but database operations will fail until MONGODB_URL is configured.")
    
    yield
    
    # Shutdown (if needed)
    # await close_database()


app = FastAPI(
    title="Screenshot Sherlock API",
    description="AI-powered text conversation analysis wingman",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(screenshot.router, prefix="/api/screenshot", tags=["Screenshot"])
app.include_router(analysis.router, prefix="/api/analyze", tags=["Analysis"])
app.include_router(wingman.router, prefix="/api/wingman", tags=["Wingman"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["Conversations"])
app.include_router(osint.router, prefix="/api/osint", tags=["OSINT"])


@app.get("/")
async def root():
    return {"message": "Screenshot Sherlock API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    CommandLineInterface().run(["main:app", "--bind", "127.0.0.1", "--port", "8000", "--application-close-timeout", "300"])

