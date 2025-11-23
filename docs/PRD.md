# Product Requirements Document (PRD)

## Lead Scoring Agent - Minimalist Version

**Version:** 1.0  
**Date:** November 22, 2025  
**Project Team:** Saad Khan, Shuja Uddin, Javeria Irfan  
**Supervisor:** Dr. Behjat Zuhaira

---

## 1. Executive Summary

A minimalist autonomous AI agent that evaluates incoming leads and predicts their conversion likelihood using machine learning. The agent learns and adapts over time by collecting feedback on actual conversion outcomes and periodically retraining its model to improve accuracy.

**Core Value:** Automate lead prioritization by providing conversion probability scores (0-1 scale), enabling sales teams to focus on high-potential opportunities.

---

## 2. Product Vision

An intelligent, self-improving agent that transforms raw lead data into actionable conversion scores, continuously learning from outcomes to enhance prediction accuracy without manual intervention.

---

## 3. Technical Architecture

### 3.1 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.10+ | Core development |
| **Agent Framework** | LangGraph | Workflow orchestration |
| **ML Library** | scikit-learn | Model training/inference |
| **Data Processing** | pandas, numpy | Feature engineering |
| **Long-term Memory** | SQLite | Persistent storage |
| **API Framework** | FastAPI | REST endpoints |
| **Validation** | Pydantic | Input/output schemas |

### 3.2 System Components

**API Layer:**
- 3 REST endpoints for external interaction
- Input validation and error handling
- Response formatting

**Agent Workflow (LangGraph):**
- Orchestrates the scoring pipeline
- Manages state transitions
- Handles learning triggers

**ML Pipeline:**
- Feature preprocessing
- Model inference
- Periodic retraining

**Memory Layer (SQLite):**
- Lead data storage
- Score history
- Feedback collection
- Model versioning

---

## 4. Functional Requirements

### 4.1 API Endpoints

#### **Endpoint 1: POST /score**
**Purpose:** Score leads and optionally provide feedback for learning

**Accepts:**
- Lead identification (unique ID)
- Demographic data (age, location, industry)
- Engagement metrics (email opens, website visits, downloads, recency)
- Lead source (webinar, referral, cold call, etc.)
- Optional: actual conversion outcome (true/false) for learning

**Returns:**
- Lead ID
- Conversion probability score (0.0 to 1.0)
- Risk category (high/medium/low)
- Timestamp
- Model version used

**Behavior:**
- Validates input data
- Processes through agent workflow
- Stores lead and score in SQLite
- If conversion outcome provided, stores as feedback
- Triggers automatic retraining when feedback threshold reached (50+ samples)

---

#### **Endpoint 2: GET /health**
**Purpose:** System health monitoring

**Returns:**
- Overall system status
- Database connectivity
- Model availability
- Uptime information

---

#### **Endpoint 3: GET /info**
**Purpose:** Model performance and system metrics

**Returns:**
- Current model version
- Model accuracy metrics (AUC score)
- Total leads scored
- Feedback samples collected
- Last training timestamp
- Features used in scoring

---

### 4.2 LangGraph Agent Workflow

**Workflow States:**

1. **VALIDATE** - Input schema validation
2. **PREPROCESS** - Feature engineering and transformation
3. **SCORE** - ML model inference
4. **STORE** - Persist to SQLite
5. **LEARN** - Process feedback and trigger retraining if needed
6. **RESPOND** - Format and return API response

**State Transitions:**
- Linear flow: VALIDATE → PREPROCESS → SCORE → STORE → LEARN → RESPOND
- Learning node checks feedback threshold and initiates background retraining
- Error states handled with appropriate logging and user feedback

---

## 5. Data Architecture

### 5.1 SQLite Database Schema

**Table 1: lead_scores**
- Primary storage for all leads and their scores
- Fields: lead_id (unique), demographic data, engagement metrics, source, score, rank, actual_outcome (nullable), model_version, timestamp
- Indexes on lead_id and timestamp for query performance

**Table 2: models**
- Model version management
- Fields: version (primary key), serialized model blob, accuracy metrics, training timestamp, active flag
- Only one model marked as active at a time

**Table 3: system_metrics**
- Aggregate statistics for /info endpoint
- Fields: total_scores, feedback_count, last_updated
- Updated periodically for quick retrieval

---

## 6. Machine Learning Pipeline

### 6.1 Features

**Numeric Features:**
- Age
- Email opens count
- Website visits count
- Content downloads count
- Days since last contact

**Categorical Features (One-Hot Encoded):**
- Geographic location
- Industry sector
- Lead source

**Derived Features:**
- Engagement intensity score
- Recency weight
- Interaction frequency

### 6.2 Model Approach

**Initial Model:** Logistic Regression
- Fast inference (< 50ms)
- Interpretable coefficients
- Sufficient accuracy for MVP (target: AUC ≥ 0.75)
- Low computational requirements

**Model Storage:**
- Serialized using pickle
- Stored as BLOB in SQLite models table
- Versioned with timestamp and metrics

### 6.3 Training Process

**Initial Training:**
- Uses synthetic dataset (1000+ samples)
- 80/20 train-test split
- Cross-validation for robustness
- Baseline model deployed as v1.0

**Adaptive Retraining:**
- Triggered automatically when 50+ new feedback samples collected
- Incorporates all historical data with actual outcomes
- Evaluates new model against current baseline
- Deploys only if accuracy improvement ≥ 2%
- Updates model_version and metrics

**Performance Metrics:**
- Primary: AUC (Area Under ROC Curve)
- Secondary: Precision @ top 20%, Recall @ top 20%
- Target: AUC ≥ 0.75, improving over time

---

## 7. Data Requirements

### 7.1 Training Data Generation

**Synthetic Data Approach:**
- Generate 1000+ realistic lead records using Faker library
- Balanced conversion outcomes (40% converted, 60% not converted)
- Realistic distributions for age, engagement metrics
- Diverse industry and location representation

**Data Attributes:**
- Demographics: Age (22-65), Location (major cities), Industry (10+ sectors)
- Engagement: Email opens (0-30), Website visits (0-20), Downloads (0-10)
- Recency: Days since contact (1-90)
- Source: Webinar, Cold Call, Referral, Advertisement, Organic
- Outcome: Converted (boolean) - used for training only

### 7.2 Free Data Resources

**Faker (Python Library):**
- Generate realistic names, locations, industries
- Create randomized but plausible engagement metrics
- No external API needed

**Mockaroo (Optional):**
- Free web service for synthetic datasets
- 1000 rows per day free tier
- Can export CSV with custom schema
- URL: https://www.mockaroo.com

---

## 8. Non-Functional Requirements

### 8.1 Performance
- **API Latency:** < 2 seconds per score request (P99)
- **Throughput:** Support 100+ leads per minute
- **Training Time:** < 5 minutes for 10,000 samples

### 8.2 Reliability
- **Uptime:** 99% availability target
- **Data Persistence:** Zero data loss for scores and feedback
- **Error Handling:** Graceful degradation with clear error messages

### 8.3 Accuracy
- **Baseline:** AUC ≥ 0.75 on test set
- **Improvement:** 5%+ accuracy gain after retraining with real feedback
- **Consistency:** Score variance < 0.05 for identical inputs

### 8.4 Scalability
- **Database:** Support 100,000+ lead records
- **Concurrent Requests:** Handle 10+ simultaneous API calls
- **Model Size:** Keep model under 10MB for fast loading

### 8.5 Usability
- **API Documentation:** OpenAPI/Swagger auto-generated
- **Error Messages:** Clear, actionable error responses
- **Setup Time:** < 15 minutes from clone to running server

---

## 9. Integration Requirements

### 9.1 Supervisor Agent Integration

**Registration Information:**
- Agent Name: "Lead Scoring Agent"
- Agent ID: "lead-scorer-001"
- Capabilities: lead scoring, conversion prediction, adaptive learning
- Endpoint Base URL: Provided at deployment

**Communication Protocol:**
- RESTful JSON API
- Standard HTTP status codes
- Authentication: API key (if required by supervisor)

**Input Schema:**
- Well-defined JSON structure
- Required fields clearly documented
- Optional fields with defaults

**Output Schema:**
- Consistent response format
- Standard error structure
- Versioned API contract

---

## 10. Development Phases

### Phase 1: Foundation (Weeks 1-2)
**Deliverables:**
- Python environment setup
- SQLite database schema implementation
- FastAPI skeleton with 3 endpoints (basic responses)
- Synthetic data generation (1000 samples)

**Acceptance Criteria:**
- Database tables created successfully
- All 3 endpoints return 200 status
- Synthetic data validates against schema

---

### Phase 2: Core Scoring (Weeks 3-4)
**Deliverables:**
- Feature engineering pipeline
- Initial Logistic Regression model training
- LangGraph workflow implementation
- Full /score endpoint functionality

**Acceptance Criteria:**
- Model achieves AUC ≥ 0.75 on test set
- /score endpoint returns valid predictions
- Lead data persisted to SQLite
- Response time < 2 seconds

---

### Phase 3: Adaptive Learning (Weeks 5-6)
**Deliverables:**
- Feedback storage mechanism
- Automatic retraining logic
- Model versioning system
- /info endpoint with live metrics

**Acceptance Criteria:**
- Feedback correctly stored with lead scores
- Retraining triggers at 50+ samples
- New model deployed if accuracy improves
- Metrics accurately reflect system state

---

### Phase 4: Integration & Polish (Weeks 7-8)
**Deliverables:**
- Comprehensive API documentation
- Unit and integration tests
- Supervisor agent integration
- Final presentation materials

**Acceptance Criteria:**
- All tests passing
- Integration successful with supervisor agent
- Documentation complete
- Performance targets met

---

## 11. Testing Strategy

### 11.1 Unit Testing
- Feature preprocessing functions
- Model prediction accuracy
- Database CRUD operations
- Input validation logic

### 11.2 Integration Testing
- End-to-end scoring workflow
- Feedback → Retraining → Deployment cycle
- API endpoint responses
- Database persistence

### 11.3 Performance Testing
- Latency benchmarks
- Concurrent request handling
- Memory usage profiling
- Database query optimization

### 11.4 Acceptance Testing
- Functional requirements verification
- Integration with supervisor agent
- User documentation walkthrough
- Instructor demonstration

---

## 12. Deployment

### 12.1 Local Development
**Requirements:**
- Python 3.10+
- Virtual environment
- SQLite3 (included with Python)
- 2GB RAM minimum

**Setup Steps:**
1. Clone repository
2. Create and activate virtual environment
3. Install dependencies from requirements.txt
4. Initialize database with schema
5. Generate synthetic training data
6. Train initial model
7. Start FastAPI server

**Verification:**
- Health endpoint returns healthy status
- Info endpoint shows model metrics
- Score endpoint processes sample lead

### 12.2 Production Deployment (Optional)
**Platforms:**
- **Render.com** - Free tier available
- **Railway.app** - Free tier with limitations
- **Fly.io** - Free tier suitable for small apps

**Considerations:**
- SQLite file persistence
- Environment variables for configuration
- API rate limiting
- Logging and monitoring

---

## 13. Documentation Requirements

### 13.1 Technical Documentation
- System architecture diagram
- Database schema with relationships
- LangGraph workflow visualization
- API endpoint specifications (OpenAPI)
- Feature engineering details
- Model training methodology

### 13.2 User Documentation
- Installation guide
- API usage examples
- Input/output schemas
- Error handling guide
- FAQ section

### 13.3 Project Management Documentation
- Work Breakdown Structure (WBS)
- Gantt chart with milestones
- Scope management plan
- Verification and validation report
- Project closure documentation

---

## 14. Success Criteria

### 14.1 Functional Success
✅ All 3 API endpoints operational  
✅ Lead scoring with AUC ≥ 0.75  
✅ Automatic retraining functional  
✅ SQLite persistence working  
✅ Integration with supervisor agent successful

### 14.2 Performance Success
✅ API response time < 2 seconds  
✅ Support 100+ leads per minute  
✅ Zero critical bugs in production  
✅ 99% uptime during evaluation period

### 14.3 Learning Success
✅ Model improves after feedback (5%+ accuracy gain)  
✅ Retraining completes successfully  
✅ New model deployed automatically  
✅ Version tracking functional

### 14.4 Project Success
✅ All deliverables submitted on time  
✅ Documentation complete and clear  
✅ Successful final presentation  
✅ Instructor approval and sign-off

---

## 15. Risk Management

### 15.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|---------|------------|
| Poor model accuracy | Medium | High | Start with proven algorithm (Logistic Regression), use quality synthetic data |
| Integration delays | Medium | Medium | Mock supervisor endpoints for parallel development |
| Database performance | Low | Medium | Index optimization, query profiling |
| API latency issues | Low | Medium | Implement response caching, optimize preprocessing |

### 15.2 Project Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|---------|------------|
| Timeline slippage | Medium | High | Weekly progress reviews, buffer time in schedule |
| Scope creep | Medium | Medium | Strict change control, documented baseline |
| Team coordination | Low | Medium | Daily standups, clear role assignments |
| Tool/platform issues | Low | Low | Backup hosting options, local development priority |

---

## 16. Dependencies

### 16.1 Core Dependencies
- **fastapi** - API framework
- **uvicorn** - ASGI server
- **pydantic** - Data validation
- **langgraph** - Agent workflow
- **langchain** - LangGraph dependency
- **scikit-learn** - Machine learning
- **pandas** - Data processing
- **numpy** - Numerical operations
- **faker** - Synthetic data generation

### 16.2 Development Dependencies
- **pytest** - Testing framework
- **httpx** - API testing
- **python-dotenv** - Environment configuration

---

## 17. Constraints

### 17.1 Technical Constraints
- Must use SQLite (no external database)
- Must use Python ecosystem
- Must integrate via REST API
- No paid external APIs

### 17.2 Project Constraints
- 8-week development timeline
- Academic project scope (no commercialization)
- Limited computational resources (free tier tools)
- Dependent on other teams for integration

### 17.3 Functional Constraints
- Exactly 3 API endpoints (no more, no less)
- Synthetic data only (no real customer data)
- Single-threaded training (no distributed computing)
- Automatic retraining only (no manual model upload)

---


## 19. Glossary

**AUC (Area Under Curve):** Metric measuring model's ability to distinguish between classes (0-1 scale, higher is better)

**Conversion:** The desired outcome action (e.g., purchase, sign-up) taken by a lead

**Feature Engineering:** Process of transforming raw data into model-ready inputs

**Lead:** Potential customer contact with associated behavioral and demographic data

**LangGraph:** Framework for building stateful, multi-step AI agent workflows

**One-Hot Encoding:** Converting categorical variables into binary vectors

**Retraining:** Process of updating model with new data to improve accuracy

**SQLite:** Lightweight, file-based relational database

---



**End of PRD**

This minimalist PRD provides complete specifications for building a working lead scoring agent that learns and adapts, using only Python, LangGraph, SQLite, and free resources, with exactly 3 API endpoints as required.