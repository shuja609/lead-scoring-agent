# Lead Scoring Agent

**Version:** 1.0  
**Status:** Phase 3 Complete ✅

An autonomous AI agent that evaluates incoming leads and predicts their conversion likelihood using machine learning. Features adaptive learning with automatic model retraining based on feedback.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. **Clone or navigate to the repository**
```bash
cd lead-scoring-agent
```

2. **Create a virtual environment**
```bash
python -m venv venv
```

3. **Activate the virtual environment**

Windows (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1
```

Windows (Command Prompt):
```cmd
venv\Scripts\activate.bat
```

Linux/Mac:
```bash
source venv/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

5. **Run setup script**
```bash
python setup.py
```

This will:
- Create necessary directories
- Initialize SQLite database
- Generate 1000 synthetic training leads
- Verify system setup

6. **Start the API server**
```bash
python run.py
```

The API will be available at: `http://localhost:8000`

---

## 📚 API Documentation

Once the server is running, access interactive API documentation at:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🔌 API Endpoints

### 1. POST /score
Score a lead's conversion probability

**Request:**
```json
{
  "lead_id": "LEAD-12345",
  "age": 35,
  "location": "New York",
  "industry": "Technology",
  "email_opens": 15,
  "website_visits": 10,
  "content_downloads": 5,
  "days_since_contact": 7,
  "lead_source": "Webinar",
  "actual_outcome": null
}
```

**Response:**
```json
{
  "lead_id": "LEAD-12345",
  "conversion_score": 0.78,
  "risk_category": "high",
  "timestamp": "2025-11-22T10:30:00.000000",
  "model_version": "1.0"
}
```

### 2. GET /health
Check system health

**Response:**
```json
{
  "status": "healthy",
  "database_connected": true,
  "model_available": true,
  "uptime_seconds": 3600.5,
  "timestamp": "2025-11-22T10:30:00.000000"
}
```

### 3. GET /info
Get system information and metrics

**Response:**
```json
{
  "model_version": "1.0",
  "model_metrics": {
    "auc_score": 0.9986,
    "precision_top20": 1.0,
    "recall_top20": 0.5
  },
  "total_leads_scored": 76,
  "feedback_samples_collected": 52,
  "last_training_timestamp": "2025-11-22T17:00:15.122919",
  "features_used": [
    "age", "location", "industry", "email_opens",
    "website_visits", "content_downloads", 
    "days_since_contact", "lead_source"
  ],
  "system_status": "operational",
  "retraining_status": {
    "is_retraining": false,
    "feedback_count": 52,
    "retraining_threshold": 50,
    "ready_for_retraining": true,
    "last_check_time": "2025-11-22T17:34:08.159547",
    "last_retrain_time": "2025-11-22T17:34:08.159547"
  }
}
```

### 4. POST /retrain
Manually trigger model retraining (Phase 3)

**Response:**
```json
{
  "status": "success",
  "old_version": "1.0",
  "new_version": "1.1",
  "old_auc": 0.9986,
  "new_auc": 0.9992,
  "improvement": 0.0006,
  "feedback_count": 52,
  "timestamp": "2025-11-22T17:34:08.159547",
  "message": "Model upgraded from 1.0 to 1.1"
}
```

---

## 📊 Project Structure

```
lead-scoring-agent/
├── app/
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration management
│   ├── database.py           # SQLite database layer
│   ├── data_generator.py     # Synthetic data generation
│   ├── features.py           # Feature engineering pipeline (Phase 2)
│   ├── main.py               # FastAPI application
│   ├── model.py              # ML model training (Phase 2)
│   ├── retraining.py         # Automatic retraining system (Phase 3)
│   ├── schemas.py            # Pydantic models
│   └── workflow.py           # LangGraph agent workflow (Phase 2)
├── data/                     # Database and data files
│   ├── lead_scoring.db       # SQLite database (auto-generated)
│   └── synthetic_leads.csv   # Training data (auto-generated)
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore rules
├── PRD.md                    # Product Requirements Document
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── run.py                    # Application entry point
├── setup.py                  # Setup script
├── test_phase1.py            # Phase 1 test suite
├── test_phase2.py            # Phase 2 test suite
└── test_phase3.py            # Phase 3 test suite
```

---

## 🎯 All Phases Complete

### ✅ Phase 1: Foundation (Complete)

1. **Python Environment Setup**
   - Virtual environment configuration
   - Dependency management with requirements.txt
   - Configuration management with pydantic-settings

2. **SQLite Database Implementation**
   - `lead_scores` table for lead data and scores
   - `models` table for model versioning
   - `system_metrics` table for statistics
   - Indexes for query optimization

3. **FastAPI Skeleton**
   - ✓ POST /score endpoint
   - ✓ GET /health endpoint
   - ✓ GET /info endpoint

4. **Synthetic Data Generation**
   - 1000 realistic lead records
   - 40% converted, 60% not converted
   - Faker library for realistic data

5. **Input Validation**
   - Comprehensive Pydantic schemas
   - Field validation and constraints

### ✅ Phase 2: ML Model Integration (Complete)

1. **Feature Engineering Pipeline**
   - 37 features (5 numeric + 3 categorical + 3 derived)
   - StandardScaler for numeric features
   - OneHotEncoder for categorical features
   - Derived features: engagement_intensity, recency_weight, interaction_frequency

2. **ML Model Training**
   - Logistic Regression model
   - AUC Score: 0.9986 (exceeds 0.75 target)
   - Precision @ Top 20%: 1.0
   - Recall @ Top 20%: 0.5
   - Model persistence to database

3. **LangGraph Workflow**
   - 6-state workflow: VALIDATE → PREPROCESS → SCORE → STORE → LEARN → RESPOND
   - State management and error handling
   - Model caching for performance

4. **Performance**
   - Response time: 2.3s (under 3s target)
   - Real ML inference integrated

### ✅ Phase 3: Adaptive Learning (Complete)

1. **Automatic Retraining System**
   - Background retraining manager
   - Non-blocking async execution
   - Triggers at 50+ feedback samples

2. **Model Comparison & Deployment**
   - Trains new model with feedback data
   - Compares AUC scores with 2% improvement threshold
   - Automatic version incrementing (1.0 → 1.1)
   - Deploys only if model improves

3. **Enhanced Monitoring**
   - Retraining status in /info endpoint
   - Feedback count tracking
   - Last retraining timestamp
   - Ready-for-retraining indicator

4. **Manual Retraining Endpoint**
   - POST /retrain for on-demand retraining
   - Returns detailed status and results
   - Validates feedback threshold

### 🎯 All Acceptance Criteria Met

**Phase 1:**
- [x] Database tables created successfully
- [x] All endpoints return 200 status
- [x] Synthetic data validates against schema
- [x] Data persisted to SQLite

**Phase 2:**
- [x] Feature engineering pipeline working
- [x] Logistic Regression model trained
- [x] AUC Score ≥ 0.75 (achieved 0.9986)
- [x] LangGraph workflow implemented
- [x] Response time < 3 seconds

**Phase 3:**
- [x] Feedback correctly stored with lead scores
- [x] Retraining triggers at 50+ samples
- [x] New model deployed if accuracy improves
- [x] Metrics accurately reflect system state

---

## ⚙️ Configuration

Create a `.env` file (or use `.env.example`) to customize settings:

```env
# Environment Configuration
ENV=development
DEBUG=True

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Database Configuration
DATABASE_PATH=./data/lead_scoring.db

# Model Configuration
MODEL_VERSION=1.0
RETRAINING_THRESHOLD=50
ACCURACY_IMPROVEMENT_THRESHOLD=0.02
```

---

## 🧪 Testing

### Automated Test Suites

Run comprehensive test suites for each phase:

**Phase 1 Tests:**
```bash
python test_phase1.py
```

**Phase 2 Tests:**
```bash
python test_phase2.py
```

**Phase 3 Tests:**
```bash
python test_phase3.py
```

### Manual API Testing

Test endpoints using curl or the Swagger UI:

**Test /health:**
```bash
curl http://localhost:8000/health
```

**Test /info:**
```bash
curl http://localhost:8000/info
```

**Test /score:**
```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": "TEST-001",
    "age": 35,
    "location": "New York",
    "industry": "Technology",
    "email_opens": 15,
    "website_visits": 10,
    "content_downloads": 5,
    "days_since_contact": 7,
    "lead_source": "Webinar",
    "actual_outcome": true
  }'
```

**Test /retrain (Phase 3):**
```bash
curl -X POST http://localhost:8000/retrain
```

---

## 🎓 Key Features

### Intelligent Lead Scoring
- **ML-Powered Predictions:** Logistic Regression model with 0.9986 AUC
- **37 Engineered Features:** Numeric, categorical, and derived features
- **Risk Categorization:** Automatic high/medium/low classification

### Adaptive Learning
- **Automatic Retraining:** Triggers at 50+ feedback samples
- **Smart Deployment:** Only deploys if model improves by 2%+
- **Version Management:** Automatic version tracking (1.0, 1.1, etc.)
- **Background Processing:** Non-blocking retraining execution

### Production Ready
- **FastAPI Framework:** High-performance async API
- **SQLite Persistence:** Reliable data storage with versioning
- **LangGraph Workflow:** 6-state orchestration pipeline
- **Comprehensive Testing:** Phase 1, 2, and 3 test suites
- **API Documentation:** Auto-generated Swagger UI

---

## 📝 License

Academic project for learning purposes.

---

## 👥 Team

- **Saad Khan**
- **Shuja Uddin**
- **Javeria Irfan**
- **Supervisor:** Dr. Behjat Zuhaira

---

## 📊 Performance Metrics

- **Model AUC Score:** 0.9986 (Target: ≥ 0.75)
- **Precision @ Top 20%:** 1.0
- **Recall @ Top 20%:** 0.5
- **API Response Time:** 2.3s average (Target: < 3s)
- **Leads Scored:** 76+
- **Feedback Samples:** 52+
- **Training Samples:** 1000

---

## 🔄 Development Workflow

1. **Phase 1:** Foundation and API skeleton ✅
2. **Phase 2:** ML model integration and LangGraph workflow ✅
3. **Phase 3:** Adaptive learning and automatic retraining ✅
4. **Phase 4:** Integration & polish (upcoming)

---

## 🚂 Deployment on Railway

### Quick Deploy

1. **Push to GitHub**
```bash
git add .
git commit -m "Add Railway deployment config"
git push origin main
```

2. **Deploy on Railway**
   - Go to [Railway](https://railway.app/)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your `lead-scoring-agent` repository
   - Railway will automatically detect the configuration

3. **Environment Variables** (Optional)
   - Set in Railway dashboard if you need to override defaults:
   - `ENV=production`
   - `DEBUG=False`
   - `LOG_LEVEL=INFO`

### Configuration Files

The project includes:
- **`Procfile`** - Process file for web dyno
- **`railway.json`** - Railway-specific configuration
- **`nixpacks.toml`** - Nixpacks build configuration

### Post-Deployment

After deployment, Railway will provide a URL like:
```
https://your-app.railway.app
```

Access your API documentation at:
```
https://your-app.railway.app/docs
```

---

**All Phases Status:** ✅ Complete (Phases 1-3)  
**Current Version:** 1.0  
**Last Updated:** November 23, 2025



---