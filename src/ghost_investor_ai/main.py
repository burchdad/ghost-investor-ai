"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api.routes_leads import router as leads_router
from .api.routes_enrichment import router as enrichment_router
from .api.routes_campaigns import router as campaigns_router
from .api.routes_activities import router as activities_router
from .api.routes_email_accounts import router as email_accounts_router
from .api.routes_batch import router as batch_router
from .database import Base, engine

# Create tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    print("Ghost Investor AI starting up...")
    yield
    # Shutdown
    print("Ghost Investor AI shutting down...")


app = FastAPI(
    title="Ghost Investor AI",
    description="AI-powered lead enrichment and investor outreach orchestration",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(leads_router)
app.include_router(enrichment_router)
app.include_router(campaigns_router)
app.include_router(activities_router)
app.include_router(email_accounts_router)
app.include_router(batch_router)


@app.get("/health")
async def health_check():
    """Health check endpoint for orchestrator."""
    return {
        "status": "healthy",
        "service": "ghost-investor-ai",
        "version": "0.1.0",
    }


@app.get("/")
async def root():
    """Root endpoint with API documentation."""
    return {
        "service": "Ghost Investor AI",
        "description": "AI-powered lead enrichment and investor outreach orchestration",
        "docs": "/docs",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
