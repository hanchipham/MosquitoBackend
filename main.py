from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from app.api.endpoints import router
from app.database import init_db
from app.config import settings
from app.auth import verify_docs_api_key
import os

# Initialize FastAPI app with docs disabled (will be protected manually)
app = FastAPI(
    title="IoT Larva Detection System",
    description="Backend API for ESP32-CAM Mosquito Larva Detection",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api", tags=["main"])


@app.on_event("startup")
async def startup_event():
    """Initialize database dan storage directories on startup"""
    # Create database tables
    init_db()
    
    # Ensure storage directories exist
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)
    os.makedirs(settings.IMAGE_ORIGINAL_PATH, exist_ok=True)
    os.makedirs(settings.IMAGE_PREPROCESSED_PATH, exist_ok=True)
    
    print("✓ Database initialized")
    print("✓ Storage directories created")
    print(f"✓ Server starting on {settings.API_HOST}:{settings.API_PORT}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "IoT Larva Detection System API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs?key=YOUR_API_KEY"
    }


# Protected documentation endpoints
@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint(api_key: str = Depends(verify_docs_api_key)):
    """Protected OpenAPI schema endpoint"""
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )


@app.get("/docs", include_in_schema=False)
async def get_documentation(api_key: str = Depends(verify_docs_api_key)):
    """Protected Swagger UI documentation"""
    return get_swagger_ui_html(
        openapi_url="/openapi.json?key=" + api_key,
        title=f"{app.title} - Swagger UI"
    )


@app.get("/redoc", include_in_schema=False)
async def get_redoc_documentation(api_key: str = Depends(verify_docs_api_key)):
    """Protected ReDoc documentation"""
    return get_redoc_html(
        openapi_url="/openapi.json?key=" + api_key,
        title=f"{app.title} - ReDoc"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
