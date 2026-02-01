import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from .core.config import settings
from .core.database import init_db

from .api import portfolio, companies, marketplace, credits, ai, swaps, market, simulator


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.APP_NAME,
    description="API for GFA Loan Sandbox - Inclusive AI Loan Reallocation Engine",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(marketplace.router, prefix="/api/marketplace", tags=["Marketplace"])
app.include_router(credits.router, prefix="/api/credits", tags=["Credits"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(swaps.router, prefix="/api/swaps", tags=["Swaps"])
app.include_router(market.router, prefix="/api/market", tags=["Market Intelligence"])
app.include_router(simulator.router, prefix="/api/simulator", tags=["Transaction Simulator"])


@app.get("/api")
async def api_root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Serve static frontend files (for Railway deployment)
# In Docker: /app/app/main.py -> dirname twice -> /app -> /app/static
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        # Serve static assets (JS, CSS, images)
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # Serve index.html for root
    @app.get("/")
    async def serve_index():
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"detail": "Frontend not built"}

    # Catch-all route for SPA - must be last
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # Don't intercept API routes
        if full_path.startswith("api/"):
            return {"detail": "Not found"}

        # Serve index.html for all other routes (SPA routing)
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"detail": "Frontend not built"}
else:
    # No static files - serve API info at root
    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": "1.0.0",
            "status": "operational",
            "note": "Frontend not available - API only mode"
        }
