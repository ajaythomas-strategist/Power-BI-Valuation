"""
FastAPI Application Entry Point for Power BI Answer Evaluator.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.services.cleanup_service import CleanupService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("powerbi_evaluator")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Power BI Answer Evaluator backend service...")
    yield
    # Shutdown: ensure cleanup of temp folders
    logger.info("Shutting down and cleaning temporary evaluation directories...")
    CleanupService.cleanup_all()


app = FastAPI(
    title="Power BI Answer Evaluator API",
    description="Automated Power BI Project Assessment Platform Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for local dev and Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Power BI Answer Evaluator API",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
