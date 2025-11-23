"""
Lead Scoring Agent - LangGraph Workflow
Stateful workflow for lead scoring process
"""

from typing import TypedDict, Annotated, Optional, Tuple, Any
from datetime import datetime
import operator

from langgraph.graph import StateGraph, END
from pydantic import ValidationError

from app.schemas import LeadScoreRequest, LeadScoreResponse, RiskCategory
from app.database import db
from app.model import ModelTrainer
from app.config import settings


# ===========================================================================
# MODEL CACHE
# ===========================================================================

# Global cache for model to avoid reloading on every request
_model_cache: Optional[Tuple[Any, Any, dict]] = None

def get_cached_model() -> Optional[Tuple[Any, Any, dict]]:
    """Get cached model or load from database"""
    global _model_cache
    
    if _model_cache is None:
        _model_cache = ModelTrainer.load_from_database()
    
    return _model_cache

def clear_model_cache():
    """Clear model cache (e.g., after retraining)"""
    global _model_cache
    _model_cache = None


# ===========================================================================
# STATE DEFINITION
# ===========================================================================

class LeadScoringState(TypedDict):
    """State for lead scoring workflow"""
    
    # Input
    request: Optional[LeadScoreRequest]
    
    # Processing
    validation_errors: Annotated[list, operator.add]
    preprocessed_data: Optional[dict]
    conversion_score: Optional[float]
    risk_category: Optional[str]
    
    # Persistence
    stored: bool
    feedback_count: int
    should_retrain: bool
    
    # Output
    response: Optional[LeadScoreResponse]
    error: Optional[str]
    
    # Metadata
    model_version: str
    timestamp: str


# ===========================================================================
# WORKFLOW NODES
# ===========================================================================

def validate_node(state: LeadScoringState) -> LeadScoringState:
    """
    Node 1: VALIDATE
    Validate input schema
    """
    try:
        request = state['request']
        if request is None:
            state['error'] = "No request provided"
            return state
        
        # Validation already done by Pydantic, just confirm
        state['validation_errors'] = []
        
    except Exception as e:
        state['error'] = f"Validation failed: {str(e)}"
        state['validation_errors'] = [str(e)]
    
    return state


def preprocess_node(state: LeadScoringState) -> LeadScoringState:
    """
    Node 2: PREPROCESS
    Feature engineering and transformation
    """
    try:
        request = state['request']
        
        # Prepare lead data for model
        preprocessed = {
            'age': request.age,
            'location': request.location,
            'industry': request.industry,
            'email_opens': request.email_opens,
            'website_visits': request.website_visits,
            'content_downloads': request.content_downloads,
            'days_since_contact': request.days_since_contact,
            'lead_source': request.lead_source.value
        }
        
        state['preprocessed_data'] = preprocessed
        
    except Exception as e:
        state['error'] = f"Preprocessing failed: {str(e)}"
    
    return state


def score_node(state: LeadScoringState) -> LeadScoringState:
    """
    Node 3: SCORE
    ML model inference
    """
    try:
        # Load active model (uses cache)
        model_data = get_cached_model()
        
        if model_data is None:
            state['error'] = "No trained model available"
            return state
        
        model, feature_engineer, metadata = model_data
        
        # Prepare lead data
        lead_dict = state['preprocessed_data']
        
        # Get prediction
        X = feature_engineer.prepare_lead_data(lead_dict)
        X_transformed = feature_engineer.transform(X)
        conversion_score = float(model.predict_proba(X_transformed)[:, 1][0])
        
        # Determine risk category
        if conversion_score >= 0.7:
            risk_category = RiskCategory.HIGH
        elif conversion_score >= 0.4:
            risk_category = RiskCategory.MEDIUM
        else:
            risk_category = RiskCategory.LOW
        
        state['conversion_score'] = conversion_score
        state['risk_category'] = risk_category.value
        state['model_version'] = metadata['version']
        
    except Exception as e:
        state['error'] = f"Scoring failed: {str(e)}"
    
    return state


def store_node(state: LeadScoringState) -> LeadScoringState:
    """
    Node 4: STORE
    Persist to SQLite
    """
    try:
        request = state['request']
        
        # Prepare lead score data
        lead_data = {
            'lead_id': request.lead_id,
            'age': request.age,
            'location': request.location,
            'industry': request.industry,
            'email_opens': request.email_opens,
            'website_visits': request.website_visits,
            'content_downloads': request.content_downloads,
            'days_since_contact': request.days_since_contact,
            'lead_source': request.lead_source.value,
            'conversion_score': state['conversion_score'],
            'risk_category': state['risk_category'],
            'actual_outcome': request.actual_outcome,
            'model_version': state['model_version'],
            'timestamp': state['timestamp']
        }
        
        # Store in database
        db.insert_lead_score(lead_data)
        
        # Update system metrics
        total_scores = db.get_total_scores()
        db.update_system_metric('total_scores', str(total_scores))
        
        if request.actual_outcome is not None:
            feedback_count = db.get_feedback_count()
            db.update_system_metric('feedback_count', str(feedback_count))
            state['feedback_count'] = feedback_count
        
        state['stored'] = True
        
    except Exception as e:
        state['error'] = f"Storage failed: {str(e)}"
        state['stored'] = False
    
    return state


def learn_node(state: LeadScoringState) -> LeadScoringState:
    """
    Node 5: LEARN
    Process feedback and trigger retraining if needed
    """
    try:
        # Check if we have enough feedback for retraining
        feedback_count = state.get('feedback_count', 0)
        threshold = settings.retraining_threshold
        
        if feedback_count >= threshold:
            state['should_retrain'] = True
            
            # Trigger background retraining (non-blocking)
            from app.retraining import retraining_manager
            retraining_manager.trigger_background_retraining()
        else:
            state['should_retrain'] = False
        
    except Exception as e:
        state['error'] = f"Learning node failed: {str(e)}"
    
    return state


def respond_node(state: LeadScoringState) -> LeadScoringState:
    """
    Node 6: RESPOND
    Format and return API response
    """
    try:
        if state.get('error'):
            # Error occurred, handled by API layer
            return state
        
        request = state['request']
        
        # Create response
        response = LeadScoreResponse(
            lead_id=request.lead_id,
            conversion_score=round(state['conversion_score'], 4),
            risk_category=RiskCategory(state['risk_category']),
            timestamp=state['timestamp'],
            model_version=state['model_version']
        )
        
        state['response'] = response
        
    except Exception as e:
        state['error'] = f"Response formatting failed: {str(e)}"
    
    return state


# ===========================================================================
# WORKFLOW CONSTRUCTION
# ===========================================================================

def create_workflow() -> StateGraph:
    """
    Create LangGraph workflow for lead scoring
    
    Flow: VALIDATE → PREPROCESS → SCORE → STORE → LEARN → RESPOND
    """
    workflow = StateGraph(LeadScoringState)
    
    # Add nodes
    workflow.add_node("validate", validate_node)
    workflow.add_node("preprocess", preprocess_node)
    workflow.add_node("score", score_node)
    workflow.add_node("store", store_node)
    workflow.add_node("learn", learn_node)
    workflow.add_node("respond", respond_node)
    
    # Define edges (linear flow)
    workflow.add_edge("validate", "preprocess")
    workflow.add_edge("preprocess", "score")
    workflow.add_edge("score", "store")
    workflow.add_edge("store", "learn")
    workflow.add_edge("learn", "respond")
    workflow.add_edge("respond", END)
    
    # Set entry point
    workflow.set_entry_point("validate")
    
    return workflow


# ===========================================================================
# WORKFLOW EXECUTION
# ===========================================================================

class LeadScoringAgent:
    """Agent for executing lead scoring workflow"""
    
    def __init__(self):
        self.workflow = create_workflow()
        self.app = self.workflow.compile()
    
    def score_lead(self, request: LeadScoreRequest) -> LeadScoreResponse:
        """
        Execute lead scoring workflow
        
        Args:
            request: LeadScoreRequest object
        
        Returns:
            LeadScoreResponse object
        
        Raises:
            Exception: If workflow fails
        """
        # Initialize state
        initial_state = {
            'request': request,
            'validation_errors': [],
            'preprocessed_data': None,
            'conversion_score': None,
            'risk_category': None,
            'stored': False,
            'feedback_count': 0,
            'should_retrain': False,
            'response': None,
            'error': None,
            'model_version': settings.model_version,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Execute workflow
        final_state = self.app.invoke(initial_state)
        
        # Check for errors
        if final_state.get('error'):
            raise Exception(final_state['error'])
        
        # Return response
        return final_state['response']


# Global agent instance
agent = LeadScoringAgent()


def main():
    """Test LangGraph workflow"""
    from app.schemas import LeadSource
    
    print("=" * 60)
    print("Testing LangGraph Workflow")
    print("=" * 60)
    
    # Create test request
    test_request = LeadScoreRequest(
        lead_id="WORKFLOW-TEST-001",
        age=35,
        location="New York",
        industry="Technology",
        email_opens=20,
        website_visits=15,
        content_downloads=7,
        days_since_contact=5,
        lead_source=LeadSource.WEBINAR,
        actual_outcome=None
    )
    
    print(f"\n📊 Test Lead: {test_request.lead_id}")
    
    # Execute workflow
    agent = LeadScoringAgent()
    response = agent.score_lead(test_request)
    
    print(f"\n✅ Workflow completed successfully!")
    print(f"\n   Lead ID: {response.lead_id}")
    print(f"   Score: {response.conversion_score:.4f}")
    print(f"   Risk: {response.risk_category}")
    print(f"   Model Version: {response.model_version}")
    print(f"   Timestamp: {response.timestamp}")
    
    # Test with feedback
    print(f"\n" + "=" * 60)
    print("Testing with Feedback")
    print("=" * 60)
    
    feedback_request = LeadScoreRequest(
        lead_id="WORKFLOW-TEST-002",
        age=42,
        location="San Francisco",
        industry="Finance",
        email_opens=25,
        website_visits=18,
        content_downloads=9,
        days_since_contact=2,
        lead_source=LeadSource.REFERRAL,
        actual_outcome=True  # Feedback: converted
    )
    
    response = agent.score_lead(feedback_request)
    
    print(f"\n✅ Workflow with feedback completed!")
    print(f"   Score: {response.conversion_score:.4f}")
    print(f"   Feedback recorded: Yes")
    
    print(f"\n" + "=" * 60)
    print("LangGraph Workflow Test: PASSED ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()
