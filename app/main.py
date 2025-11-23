"""
Lead Scoring Agent - FastAPI Application
REST API with 3 endpoints: /score, /health, /info
"""

import time
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import db
from app.schemas import (
    LeadScoreRequest,
    LeadScoreResponse,
    HealthResponse,
    InfoResponse,
    ErrorResponse,
    RiskCategory,
    ModelMetrics
)
from app.data_generator import SyntheticDataGenerator
from app.workflow import agent as scoring_agent
from app.model import ModelTrainer
from app.retraining import retraining_manager

# Track application start time for uptime calculation
START_TIME = time.time()

# Cached model instance for performance
_cached_model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - startup and shutdown events"""
    # Startup
    print("🚀 Starting Lead Scoring Agent...")
    
    # Ensure directories exist
    settings.ensure_directories()
    
    # Initialize database schema
    print("📊 Initializing database schema...")
    db.initialize_schema()
    
    print("✓ Database schema initialized")
    print(f"✓ Database path: {settings.database_path}")
    print(f"✓ API running on {settings.api_host}:{settings.api_port}")
    
    yield
    
    # Shutdown
    print("👋 Shutting down Lead Scoring Agent...")


# Initialize FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_risk_category(score: float) -> RiskCategory:
    """
    Categorize lead based on conversion score
    High: score >= 0.7
    Medium: 0.4 <= score < 0.7
    Low: score < 0.4
    """
    if score >= 0.7:
        return RiskCategory.HIGH
    elif score >= 0.4:
        return RiskCategory.MEDIUM
    else:
        return RiskCategory.LOW


def format_error_response(error_type: str, message: str, details: list = None) -> Dict[str, Any]:
    """Format standardized error response"""
    return {
        "error": error_type,
        "message": message,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# ENDPOINT 1: POST /score
# ============================================================================

@app.post(
    "/score",
    response_model=LeadScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Score a lead",
    description="Score a lead's conversion probability and optionally provide feedback for learning",
    responses={
        200: {"description": "Lead scored successfully"},
        400: {"model": ErrorResponse, "description": "Invalid input data"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def score_lead(request: LeadScoreRequest) -> LeadScoreResponse:
    """
    Score a lead and return conversion probability
    
    Phase 2: Uses ML model with LangGraph workflow
    """
    try:
        # Execute LangGraph workflow (6 states: VALIDATE → PREPROCESS → SCORE → STORE → LEARN → RESPOND)
        response = scoring_agent.score_lead(request)
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response(
                "InternalServerError",
                f"Failed to score lead: {str(e)}"
            )
        )


# ============================================================================
# ENDPOINT 2: GET /health
# ============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check system health and availability",
    responses={
        200: {"description": "System is healthy"},
        503: {"model": ErrorResponse, "description": "Service unavailable"}
    }
)
async def health_check() -> HealthResponse:
    """
    Perform system health check
    
    Verifies:
    - Database connectivity
    - Model availability (Phase 2)
    - System uptime
    """
    try:
        # Check database connectivity
        database_connected = False
        try:
            _ = db.get_total_scores()
            database_connected = True
        except Exception:
            pass
        
        # Check model availability
        model_data = ModelTrainer.load_from_database()
        model_available = model_data is not None
        
        # Calculate uptime
        uptime_seconds = time.time() - START_TIME
        
        # Determine overall status
        if database_connected and model_available:
            overall_status = "healthy"
            status_code = status.HTTP_200_OK
        else:
            overall_status = "degraded"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
        response = HealthResponse(
            status=overall_status,
            database_connected=database_connected,
            model_available=model_available,
            uptime_seconds=round(uptime_seconds, 2),
            timestamp=datetime.utcnow().isoformat()
        )
        
        if status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            return JSONResponse(
                status_code=status_code,
                content=response.model_dump()
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response(
                "InternalServerError",
                f"Health check failed: {str(e)}"
            )
        )


# ============================================================================
# ENDPOINT 3: GET /info
# ============================================================================

@app.get(
    "/info",
    response_model=InfoResponse,
    status_code=status.HTTP_200_OK,
    summary="System information",
    description="Get model performance metrics and system statistics",
    responses={
        200: {"description": "System information retrieved successfully"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def system_info() -> InfoResponse:
    """
    Retrieve system information and metrics
    
    Returns:
    - Model version and metrics
    - Total leads scored
    - Feedback samples collected
    - Last training timestamp
    - Features used
    """
    try:
        # Get system metrics from database
        metrics = db.get_system_metrics()
        
        # Get model info (placeholder for Phase 1)
        model_info = db.get_model_info()
        
        if model_info:
            model_version = model_info["version"]
            model_metrics = ModelMetrics(
                auc_score=model_info.get("auc_score"),
                precision_top20=model_info.get("precision_top20"),
                recall_top20=model_info.get("recall_top20")
            )
            last_training = model_info.get("training_timestamp", "never")
        else:
            # Phase 1 placeholder values
            model_version = settings.model_version
            model_metrics = ModelMetrics(
                auc_score=None,
                precision_top20=None,
                recall_top20=None
            )
            last_training = metrics.get("last_training", "never")
        
        # Get current statistics
        total_scores = int(metrics.get("total_scores", 0))
        feedback_count = int(metrics.get("feedback_count", 0))
        
        # Get features used
        features_used = SyntheticDataGenerator.get_feature_names()
        
        # Get retraining status (Phase 3)
        retraining_status = retraining_manager.get_status()
        
        # Add retraining info to system_status
        system_status_details = {
            "operational": "operational",
            "retraining_status": retraining_status
        }
        
        return InfoResponse(
            model_version=model_version,
            model_metrics=model_metrics,
            total_leads_scored=total_scores,
            feedback_samples_collected=feedback_count,
            last_training_timestamp=last_training,
            features_used=features_used,
            system_status="operational",
            retraining_status=retraining_status  # Phase 3: Add retraining info
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response(
                "InternalServerError",
                f"Failed to retrieve system info: {str(e)}"
            )
        )


# ============================================================================
# ENDPOINT 4: POST /retrain (Phase 3)
# ============================================================================

@app.post(
    "/retrain",
    status_code=status.HTTP_200_OK,
    summary="Manual model retraining",
    description="Manually trigger model retraining if sufficient feedback is available",
    responses={
        200: {"description": "Retraining initiated or status returned"},
        400: {"model": ErrorResponse, "description": "Insufficient feedback"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def manual_retrain() -> Dict[str, Any]:
    """
    Manually trigger model retraining
    
    Phase 3: Adaptive Learning
    - Checks if sufficient feedback (50+ samples)
    - Retrains model if threshold met
    - Deploys new model if accuracy improves by 2%+
    """
    try:
        result = retraining_manager.check_and_retrain()
        
        if result['status'] == 'insufficient_feedback':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=format_error_response(
                    "InsufficientFeedback",
                    result['message'],
                    details=[f"Current: {result['feedback_count']}, Required: {result['threshold']}"]
                )
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=format_error_response(
                "InternalServerError",
                f"Retraining failed: {str(e)}"
            )
        )


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get(
    "/",
    summary="Root endpoint",
    description="Welcome message and API information"
)
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "endpoints": {
            "score": "/score",
            "health": "/health",
            "info": "/info",
            "retrain": "/retrain",
            "docs": "/docs"
        },
        "status": "operational"
    }


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with standardized format"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {
            "error": "HTTPException",
            "message": str(exc.detail),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            "InternalServerError",
            f"An unexpected error occurred: {str(exc)}"
        )
    )
