"""
CarScout AI - FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from apps.api.routers import telegram, admin, internal, public
from configs.settings import settings

app = FastAPI(
    title="CarScout AI",
    description="AI-powered car listing aggregator and pricing analyzer",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(telegram.router, prefix="/telegram", tags=["telegram"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(internal.router, prefix="/internal", tags=["internal"])
app.include_router(public.router, prefix="/v1", tags=["public"])

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/readiness")
async def readiness_check():
    """Readiness check endpoint"""
    # TODO: Add database and Redis connectivity checks
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "apps.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
