from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
