from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import users, listings, purchases, blockchain, public, audit

settings = get_settings()

# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "### 🌿 Green Energy Marketplace — Peer-to-Peer Renewable Energy Trading\n\n"
        "A platform where **sellers** list surplus renewable energy (Solar, Wind, Hydro, Biomass...) "
        "and **buyers** purchase energy credits directly — settled via Ethereum smart contracts.\n\n"
        "**AI Agent** powered by AWS Bedrock + RAG analyzes market data from `/api/v1/public/*` "
        "endpoints to provide price predictions, demand forecasts and trading recommendations."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ─── CORS ────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Global exception handler ────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )

# ─── Routers ─────────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"

app.include_router(users.router, prefix=API_PREFIX)
app.include_router(listings.router, prefix=API_PREFIX)
app.include_router(purchases.router, prefix=API_PREFIX)
app.include_router(blockchain.router, prefix=API_PREFIX)
app.include_router(audit.router, prefix=API_PREFIX)
app.include_router(public.router, prefix=API_PREFIX)

# ─── Root endpoint ───────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
def root():
    """Welcome endpoint - shows API information"""
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "api_prefix": API_PREFIX,
    }


# ─── Health check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health():
    """Check if the API and database are working"""
    from app.database import engine
    from sqlalchemy import text

    response = {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
    }

    # Test database connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            response["database"] = "connected"
    except Exception as e:
        response["status"] = "error"
        response["database"] = "disconnected"

    return response
