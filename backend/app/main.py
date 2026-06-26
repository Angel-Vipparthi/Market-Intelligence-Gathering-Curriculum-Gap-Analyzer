from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, clean up on shutdown."""
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    logger.info("Initializing Gap Analyzer backend...")

    # Initialize Supabase client
    supabase = get_supabase_client()
    logger.info("Supabase client initialized")

    # Initialize Langfuse if credentials are provided
    if settings.langfuse_public_key and settings.langfuse_secret_key:
        try:
            from langfuse import Langfuse

            langfuse = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )
            app.state.langfuse = langfuse
            logger.info("Langfuse client initialized")
        except ImportError:
            logger.warning("Langfuse package not installed, skipping initialization")
        except Exception as e:
            logger.warning(f"Failed to initialize Langfuse: {e}")

    app.state.supabase = supabase

    yield

    # Cleanup
    if hasattr(app.state, "langfuse") and app.state.langfuse:
        try:
            app.state.langfuse.flush()
        except Exception:
            pass
    logger.info("Gap Analyzer backend shut down")


app = FastAPI(
    title="Gap Analyzer",
    description="AI-powered curriculum gap analysis service",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api.router import api_router  # noqa: E402

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {"service": "gap-analyzer", "version": "0.1.0"}
