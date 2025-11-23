"""
Lead Scoring Agent - Application Entry Point
Run this script to start the FastAPI server
"""

import uvicorn
from app.config import settings


if __name__ == "__main__":
    print(f"Starting {settings.api_title} v{settings.api_version}")
    print(f"API Documentation: http://{settings.api_host}:{settings.api_port}/docs")
    print()
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
