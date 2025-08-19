from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from models.database import db_manager
from api.endpoints import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Bangladesh News Scraper API",
    description="A comprehensive news scraper for Bangladeshi news portals with geolocation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize database connection and create indexes"""
    await db_manager.connect()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection"""
    await db_manager.disconnect()

@app.get("/")
async def root():
    return {
        "message": "Bangladesh News Scraper API",
        "version": "1.0.0",
        "docs": "/docs",
        "api_base": "/api/v1"
    }

@app.get("/health")
async def health_check():
    try:
        stats = await db_manager.get_database_stats()
        return {
            "status": "healthy",
            "database": "connected",
            "stats": {
                "unique_news_count": stats["unique_news_count"],
                "raw_news_count": stats["raw_news_count"],
                "geolocated_news_count": stats["geolocated_news_count"]
            }
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

