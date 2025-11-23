"""
Lead Scoring Agent - Pydantic Schemas
Input/output validation and data models
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class LeadSource(str, Enum):
    """Valid lead source types"""
    WEBINAR = "Webinar"
    COLD_CALL = "Cold Call"
    REFERRAL = "Referral"
    ADVERTISEMENT = "Advertisement"
    ORGANIC = "Organic"
    TRADE_SHOW = "Trade Show"
    EMAIL_CAMPAIGN = "Email Campaign"


class RiskCategory(str, Enum):
    """Lead risk/priority categories"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class LeadScoreRequest(BaseModel):
    """Request schema for /score endpoint"""
    
    # Lead Identification
    lead_id: str = Field(
        ...,
        description="Unique identifier for the lead",
        min_length=1,
        max_length=100
    )
    
    # Demographics
    age: int = Field(
        ...,
        description="Age of the lead",
        ge=18,
        le=100
    )
    
    location: str = Field(
        ...,
        description="Geographic location of the lead",
        min_length=1,
        max_length=100
    )
    
    industry: str = Field(
        ...,
        description="Industry sector of the lead",
        min_length=1,
        max_length=100
    )
    
    # Engagement Metrics
    email_opens: int = Field(
        ...,
        description="Number of email opens",
        ge=0
    )
    
    website_visits: int = Field(
        ...,
        description="Number of website visits",
        ge=0
    )
    
    content_downloads: int = Field(
        ...,
        description="Number of content downloads",
        ge=0
    )
    
    days_since_contact: int = Field(
        ...,
        description="Days since last contact",
        ge=0
    )
    
    # Lead Source
    lead_source: LeadSource = Field(
        ...,
        description="Source of the lead"
    )
    
    # Optional Feedback
    actual_outcome: Optional[bool] = Field(
        None,
        description="Actual conversion outcome (for learning)"
    )
    
    @field_validator('lead_id')
    @classmethod
    def validate_lead_id(cls, v: str) -> str:
        """Ensure lead_id is not empty after stripping"""
        if not v.strip():
            raise ValueError("lead_id cannot be empty")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "lead_id": "LEAD-12345",
                "age": 35,
                "location": "New York",
                "industry": "Technology",
                "email_opens": 15,
                "website_visits": 10,
                "content_downloads": 5,
                "days_since_contact": 7,
                "lead_source": "Webinar",
                "actual_outcome": None
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class LeadScoreResponse(BaseModel):
    """Response schema for /score endpoint"""
    
    lead_id: str = Field(
        ...,
        description="Unique identifier for the lead"
    )
    
    conversion_score: float = Field(
        ...,
        description="Conversion probability score (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    
    risk_category: RiskCategory = Field(
        ...,
        description="Risk/priority category"
    )
    
    timestamp: str = Field(
        ...,
        description="Scoring timestamp (ISO format)"
    )
    
    model_version: str = Field(
        ...,
        description="Model version used for scoring"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "lead_id": "LEAD-12345",
                "conversion_score": 0.78,
                "risk_category": "high",
                "timestamp": "2025-11-22T10:30:00.000000",
                "model_version": "1.0"
            }
        }


class HealthResponse(BaseModel):
    """Response schema for /health endpoint"""
    
    status: str = Field(
        ...,
        description="Overall system status"
    )
    
    database_connected: bool = Field(
        ...,
        description="Database connectivity status"
    )
    
    model_available: bool = Field(
        ...,
        description="ML model availability status"
    )
    
    uptime_seconds: float = Field(
        ...,
        description="System uptime in seconds"
    )
    
    timestamp: str = Field(
        ...,
        description="Health check timestamp (ISO format)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "database_connected": True,
                "model_available": True,
                "uptime_seconds": 3600.5,
                "timestamp": "2025-11-22T10:30:00.000000"
            }
        }


class ModelMetrics(BaseModel):
    """Model performance metrics"""
    
    auc_score: Optional[float] = Field(
        None,
        description="Area Under ROC Curve",
        ge=0.0,
        le=1.0
    )
    
    precision_top20: Optional[float] = Field(
        None,
        description="Precision at top 20%",
        ge=0.0,
        le=1.0
    )
    
    recall_top20: Optional[float] = Field(
        None,
        description="Recall at top 20%",
        ge=0.0,
        le=1.0
    )


class InfoResponse(BaseModel):
    """Response schema for /info endpoint"""
    
    model_version: str = Field(
        ...,
        description="Current active model version"
    )
    
    model_metrics: ModelMetrics = Field(
        ...,
        description="Model performance metrics"
    )
    
    total_leads_scored: int = Field(
        ...,
        description="Total number of leads scored"
    )
    
    feedback_samples_collected: int = Field(
        ...,
        description="Number of feedback samples collected"
    )
    
    last_training_timestamp: str = Field(
        ...,
        description="Last model training timestamp"
    )
    
    features_used: List[str] = Field(
        ...,
        description="Features used in scoring"
    )
    
    system_status: str = Field(
        ...,
        description="Overall system status"
    )
    
    retraining_status: Optional[Dict[str, Any]] = Field(
        None,
        description="Retraining status information (Phase 3)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_version": "1.0",
                "model_metrics": {
                    "auc_score": 0.78,
                    "precision_top20": 0.85,
                    "recall_top20": 0.72
                },
                "total_leads_scored": 150,
                "feedback_samples_collected": 25,
                "last_training_timestamp": "2025-11-22T08:00:00.000000",
                "features_used": [
                    "age", "location", "industry", "email_opens",
                    "website_visits", "content_downloads", 
                    "days_since_contact", "lead_source"
                ],
                "system_status": "operational",
                "retraining_status": {
                    "is_retraining": False,
                    "feedback_count": 25,
                    "retraining_threshold": 50,
                    "ready_for_retraining": False
                }
            }
        }


# ============================================================================
# ERROR RESPONSE SCHEMAS
# ============================================================================

class ErrorDetail(BaseModel):
    """Detailed error information"""
    
    field: Optional[str] = Field(
        None,
        description="Field that caused the error (if applicable)"
    )
    
    message: str = Field(
        ...,
        description="Error message"
    )


class ErrorResponse(BaseModel):
    """Standard error response schema"""
    
    error: str = Field(
        ...,
        description="Error type or category"
    )
    
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    
    details: Optional[List[ErrorDetail]] = Field(
        None,
        description="Detailed error information"
    )
    
    timestamp: str = Field(
        ...,
        description="Error timestamp (ISO format)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data",
                "details": [
                    {
                        "field": "age",
                        "message": "Age must be between 18 and 100"
                    }
                ],
                "timestamp": "2025-11-22T10:30:00.000000"
            }
        }
