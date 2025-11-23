# Lead Scoring Agent - Integration Reference for Supervisor

**Agent Name:** Lead Scoring Agent  
**Version:** 1.0  
**Status:** Production Ready (Phases 1-3 Complete)  
**Maintained By:** Saad Khan, Shuja Uddin, Javeria Irfan  
**Last Updated:** November 22, 2025

---

## Executive Summary

The Lead Scoring Agent is an autonomous AI agent that predicts lead conversion probability using machine learning. It features adaptive learning through automatic model retraining based on real-world feedback.

**Key Capabilities:**
- Real-time lead scoring (0.0 - 1.0 probability)
- Risk categorization (high/medium/low)
- Automatic model retraining at 50+ feedback samples
- Self-improving accuracy (current AUC: 0.9986)
- Non-blocking background learning

---

## API Endpoints

### Base URL
```
http://localhost:8000
```

### 1. POST /score - Score a Lead

**Purpose:** Predict conversion probability for a lead and optionally provide feedback.

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

**Request Fields:**

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| `lead_id` | string | Yes | Unique lead identifier | Any string |
| `age` | integer | Yes | Lead's age | 18-100 |
| `location` | string | Yes | Geographic location | Any string |
| `industry` | string | Yes | Industry sector | Any string |
| `email_opens` | integer | Yes | Number of email opens | 0-100 |
| `website_visits` | integer | Yes | Number of website visits | 0-100 |
| `content_downloads` | integer | Yes | Number of content downloads | 0-50 |
| `days_since_contact` | integer | Yes | Days since last contact | 0-365 |
| `lead_source` | string | Yes | Lead acquisition source | "Webinar", "Cold Call", "Referral", "Advertisement", "Organic", "Trade Show", "Email Campaign" |
| `actual_outcome` | boolean/null | No | Actual conversion outcome (for feedback) | true, false, null |

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

**Response Fields:**

| Field | Type | Description | Values |
|-------|------|-------------|--------|
| `lead_id` | string | Echo of input lead ID | Same as input |
| `conversion_score` | float | Conversion probability | 0.0 - 1.0 |
| `risk_category` | string | Priority level | "high" (≥0.7), "medium" (0.4-0.7), "low" (<0.4) |
| `timestamp` | string | Scoring timestamp | ISO 8601 format |
| `model_version` | string | Model version used | e.g., "1.0", "1.1" |

**Performance:**
- Response Time: 2.3s average (P99)
- Timeout: Set client timeout to 5s minimum
- Rate Limit: None currently

---

### 2. GET /health - Health Check

**Purpose:** Verify agent availability and model status.

**Request:**
```bash
GET /health
```

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

**Status Codes:**
- `200 OK`: System healthy and operational
- `503 Service Unavailable`: System degraded (DB or model unavailable)

**Use Case:** Health checks for load balancers, monitoring systems.

---

### 3. GET /info - System Information

**Purpose:** Retrieve model metrics, feedback status, and retraining information.

**Request:**
```bash
GET /info
```

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

**Key Metrics:**
- `auc_score`: Model accuracy (target: ≥0.75)
- `feedback_count`: Leads with actual outcomes
- `ready_for_retraining`: Whether agent can retrain now

---

### 4. POST /retrain - Manual Retraining

**Purpose:** Manually trigger model retraining (if sufficient feedback available).

**Request:**
```bash
POST /retrain
```

**Response (Success):**
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

**Response (No Improvement):**
```json
{
  "status": "no_improvement",
  "feedback_count": 52,
  "current_version": "1.0",
  "current_auc": 0.9986,
  "message": "New model did not meet improvement threshold (0.02)"
}
```

**Response (Insufficient Feedback - 400 Error):**
```json
{
  "error": "InsufficientFeedback",
  "message": "Need 38 more feedback samples",
  "details": ["Current: 12, Required: 50"],
  "timestamp": "2025-11-22T17:34:08.159547"
}
```

**Notes:**
- Retraining requires 50+ feedback samples
- New model must improve AUC by 2%+ to deploy
- Retraining takes 2-3 minutes (blocking)

---

## Integration Scenarios

### Scenario 1: Real-Time Lead Scoring

**Use Case:** Sales CRM receives new lead, needs immediate scoring.

```python
import requests

def score_new_lead(lead_data):
    """Score a new lead in real-time"""
    response = requests.post(
        "http://lead-scoring-agent:8000/score",
        json={
            "lead_id": lead_data["id"],
            "age": lead_data["age"],
            "location": lead_data["location"],
            "industry": lead_data["industry"],
            "email_opens": lead_data["email_opens"],
            "website_visits": lead_data["website_visits"],
            "content_downloads": lead_data["content_downloads"],
            "days_since_contact": lead_data["days_since_contact"],
            "lead_source": lead_data["source"],
            "actual_outcome": None
        },
        timeout=5.0
    )
    
    if response.status_code == 200:
        result = response.json()
        return {
            "score": result["conversion_score"],
            "priority": result["risk_category"],
            "model_version": result["model_version"]
        }
    else:
        raise Exception(f"Scoring failed: {response.text}")

# Usage
lead = get_new_lead_from_crm()
scoring_result = score_new_lead(lead)

if scoring_result["priority"] == "high":
    assign_to_top_salesperson(lead)
elif scoring_result["priority"] == "medium":
    add_to_nurture_campaign(lead)
else:
    add_to_low_priority_queue(lead)
```

---

### Scenario 2: Batch Scoring

**Use Case:** Process multiple leads at once.

```python
import requests
from concurrent.futures import ThreadPoolExecutor

def score_lead_batch(leads, max_workers=10):
    """Score multiple leads concurrently"""
    def score_single(lead):
        try:
            response = requests.post(
                "http://lead-scoring-agent:8000/score",
                json={
                    "lead_id": lead["id"],
                    "age": lead["age"],
                    "location": lead["location"],
                    "industry": lead["industry"],
                    "email_opens": lead["email_opens"],
                    "website_visits": lead["website_visits"],
                    "content_downloads": lead["content_downloads"],
                    "days_since_contact": lead["days_since_contact"],
                    "lead_source": lead["source"],
                    "actual_outcome": None
                },
                timeout=5.0
            )
            return response.json()
        except Exception as e:
            return {"error": str(e), "lead_id": lead["id"]}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(score_single, leads))
    
    return results

# Usage
leads = get_unscored_leads_from_db(limit=100)
scores = score_lead_batch(leads)

for lead, score in zip(leads, scores):
    if "error" not in score:
        update_crm_with_score(lead["id"], score["conversion_score"])
```

---

### Scenario 3: Feedback Collection (Adaptive Learning)

**Use Case:** CRM system updates lead status → Agent learns from outcome.

```python
import requests

def provide_lead_outcome(lead_id, converted, lead_data):
    """
    Provide feedback when lead outcome is known
    This enables the agent to learn and improve
    """
    response = requests.post(
        "http://lead-scoring-agent:8000/score",
        json={
            "lead_id": lead_id,
            "age": lead_data["age"],
            "location": lead_data["location"],
            "industry": lead_data["industry"],
            "email_opens": lead_data["email_opens"],
            "website_visits": lead_data["website_visits"],
            "content_downloads": lead_data["content_downloads"],
            "days_since_contact": lead_data["days_since_contact"],
            "lead_source": lead_data["source"],
            "actual_outcome": converted  # ← Feedback!
        },
        timeout=5.0
    )
    
    return response.json()

# CRM Webhook: When deal closes
def on_deal_closed(deal):
    lead_id = deal.lead_id
    converted = (deal.status == "won")
    lead_data = get_lead_data(lead_id)
    
    # Provide feedback to agent
    provide_lead_outcome(lead_id, converted, lead_data)
    
    print(f"Feedback provided: Lead {lead_id} {'converted' if converted else 'lost'}")
```

---

### Scenario 4: Supervisor Orchestration

**Use Case:** Supervisor agent coordinates multiple agents.

```python
class SupervisorAgent:
    def __init__(self):
        self.lead_scoring_agent = "http://lead-scoring-agent:8000"
        self.email_agent = "http://email-agent:8000"
        self.calendar_agent = "http://calendar-agent:8000"
    
    def process_new_lead(self, lead):
        """
        Orchestrate multi-agent workflow:
        1. Score lead
        2. Based on score, trigger appropriate actions
        """
        # Step 1: Score the lead
        score_response = requests.post(
            f"{self.lead_scoring_agent}/score",
            json={
                "lead_id": lead["id"],
                "age": lead["age"],
                "location": lead["location"],
                "industry": lead["industry"],
                "email_opens": lead["email_opens"],
                "website_visits": lead["website_visits"],
                "content_downloads": lead["content_downloads"],
                "days_since_contact": lead["days_since_contact"],
                "lead_source": lead["source"],
                "actual_outcome": None
            },
            timeout=5.0
        ).json()
        
        score = score_response["conversion_score"]
        priority = score_response["risk_category"]
        
        # Step 2: Orchestrate based on score
        if priority == "high":
            # High priority: Schedule immediate call
            self.calendar_agent_schedule_call(lead, urgent=True)
            self.email_agent_send_personalized_email(lead, template="high_priority")
            self.assign_to_top_salesperson(lead)
        
        elif priority == "medium":
            # Medium priority: Add to nurture sequence
            self.email_agent_add_to_sequence(lead, sequence="nurture_7day")
            self.assign_to_available_salesperson(lead)
        
        else:
            # Low priority: Automated follow-up
            self.email_agent_send_template(lead, template="general_info")
            self.add_to_low_priority_queue(lead)
        
        return {
            "lead_id": lead["id"],
            "score": score,
            "priority": priority,
            "actions_taken": self.get_actions_log()
        }
    
    def check_agents_health(self):
        """Health check for all agents"""
        agents = {
            "lead_scoring": self.lead_scoring_agent,
            "email": self.email_agent,
            "calendar": self.calendar_agent
        }
        
        status = {}
        for name, url in agents.items():
            try:
                response = requests.get(f"{url}/health", timeout=2.0)
                status[name] = "healthy" if response.status_code == 200 else "degraded"
            except:
                status[name] = "unavailable"
        
        return status
```

---

## Data Models

### Input Schema (LeadScoreRequest)

```python
from pydantic import BaseModel, Field
from typing import Optional

class LeadScoreRequest(BaseModel):
    lead_id: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=18, le=100)
    location: str = Field(..., min_length=1, max_length=100)
    industry: str = Field(..., min_length=1, max_length=100)
    email_opens: int = Field(..., ge=0, le=100)
    website_visits: int = Field(..., ge=0, le=100)
    content_downloads: int = Field(..., ge=0, le=50)
    days_since_contact: int = Field(..., ge=0, le=365)
    lead_source: str  # Enum: see valid values above
    actual_outcome: Optional[bool] = None
```

### Output Schema (LeadScoreResponse)

```python
class LeadScoreResponse(BaseModel):
    lead_id: str
    conversion_score: float  # 0.0 - 1.0
    risk_category: str  # "high", "medium", "low"
    timestamp: str  # ISO 8601
    model_version: str
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Response |
|------|---------|----------|
| 200 | Success | Normal response |
| 400 | Bad Request | Invalid input data |
| 404 | Not Found | Endpoint doesn't exist |
| 500 | Internal Server Error | Agent error |
| 503 | Service Unavailable | Agent degraded |

### Error Response Format

```json
{
  "error": "ValidationError",
  "message": "Invalid lead_source value",
  "details": [
    "Input should be 'Webinar', 'Cold Call', 'Referral', 'Advertisement', 'Organic', 'Trade Show' or 'Email Campaign'"
  ],
  "timestamp": "2025-11-22T10:30:00.000000"
}
```

### Retry Logic (Recommended)

```python
import time
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_resilient_session():
    """Create HTTP session with automatic retries"""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        method_whitelist=["GET", "POST"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Usage
session = create_resilient_session()
response = session.post(
    "http://lead-scoring-agent:8000/score",
    json=lead_data,
    timeout=5.0
)
```

---

## Deployment Information

### Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_PATH=./data/lead_scoring.db

# Model Configuration
MODEL_VERSION=1.0
RETRAINING_THRESHOLD=50
ACCURACY_IMPROVEMENT_THRESHOLD=0.02
TARGET_AUC=0.75

# Environment
ENV=production
DEBUG=False
```

### Docker Deployment (Recommended)

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY run.py .

EXPOSE 8000

CMD ["python", "run.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  lead-scoring-agent:
    build: ./lead-scoring-agent
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - DATABASE_PATH=/app/data/lead_scoring.db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    restart: unless-stopped
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lead-scoring-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: lead-scoring-agent
  template:
    metadata:
      labels:
        app: lead-scoring-agent
    spec:
      containers:
      - name: agent
        image: lead-scoring-agent:1.0
        ports:
        - containerPort: 8000
        env:
        - name: API_PORT
          value: "8000"
        - name: DATABASE_PATH
          value: "/data/lead_scoring.db"
        volumeMounts:
        - name: data
          mountPath: /data
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: lead-scoring-data
---
apiVersion: v1
kind: Service
metadata:
  name: lead-scoring-agent
spec:
  selector:
    app: lead-scoring-agent
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
```

---

## Performance Characteristics

### Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Response Time (P50) | 2.1s | Median response time |
| Response Time (P99) | 2.3s | 99th percentile |
| Throughput | 100+ req/min | Tested capacity |
| Model AUC | 0.9986 | Current accuracy |
| Memory Usage | ~500 MB | Average |
| CPU Usage | 15-25% | During scoring |

### Scalability

- **Horizontal Scaling**: Stateless API, can run multiple instances
- **Database**: SQLite suitable for <100K leads, migrate to PostgreSQL for larger scale
- **Caching**: Model cached in memory for performance
- **Concurrency**: Handles 10+ simultaneous requests

---

## Monitoring & Observability

### Key Metrics to Monitor

1. **Health Endpoint**: Poll `/health` every 30s
2. **Response Time**: Track P50, P95, P99
3. **Error Rate**: Monitor 4xx and 5xx responses
4. **Feedback Count**: Track via `/info` endpoint
5. **Model Version**: Alert on version changes
6. **Retraining Status**: Monitor `retraining_status.is_retraining`

### Sample Monitoring Script

```python
import requests
import time

def monitor_agent():
    """Continuous monitoring of lead scoring agent"""
    while True:
        try:
            # Health check
            health = requests.get("http://lead-scoring-agent:8000/health", timeout=2.0)
            print(f"Health: {health.json()['status']}")
            
            # System info
            info = requests.get("http://lead-scoring-agent:8000/info", timeout=2.0)
            data = info.json()
            
            print(f"Model Version: {data['model_version']}")
            print(f"AUC Score: {data['model_metrics']['auc_score']}")
            print(f"Feedback Count: {data['feedback_samples_collected']}")
            print(f"Retraining Ready: {data['retraining_status']['ready_for_retraining']}")
            
            # Alert if model degraded
            if data['model_metrics']['auc_score'] < 0.75:
                send_alert("Model AUC below threshold!")
            
        except Exception as e:
            print(f"Monitoring error: {e}")
            send_alert(f"Lead Scoring Agent unreachable: {e}")
        
        time.sleep(30)
```

---

## Security Considerations

### Current Implementation

- No authentication required (internal network assumed)
- No rate limiting
- No data encryption at rest
- SQLite file-based database

### Recommendations for Production

1. **Add Authentication**:
   ```python
   # Add API key authentication
   from fastapi import Header, HTTPException
   
   async def verify_api_key(x_api_key: str = Header(...)):
       if x_api_key != os.getenv("API_KEY"):
           raise HTTPException(401, "Invalid API key")
   ```

2. **Enable HTTPS**: Use reverse proxy (nginx) with SSL/TLS

3. **Rate Limiting**: Implement per-client rate limits

4. **Database Encryption**: Encrypt SQLite database or migrate to secure DB

5. **Input Sanitization**: Already implemented via Pydantic validation

---

## Maintenance & Support

### Regular Tasks

1. **Weekly**: Check feedback count, trigger manual retraining if needed
2. **Monthly**: Review model metrics, verify AUC > 0.75
3. **Quarterly**: Backup database, review system logs

### Database Backup

```bash
# Backup SQLite database
cp ./data/lead_scoring.db ./backups/lead_scoring_$(date +%Y%m%d).db

# Restore from backup
cp ./backups/lead_scoring_20251122.db ./data/lead_scoring.db
```

### Troubleshooting

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| Slow responses | Check CPU/memory | Scale horizontally |
| Model not retraining | Check feedback count | Verify ≥50 samples |
| Low accuracy | Check AUC in /info | Collect more diverse feedback |
| Database errors | Check disk space | Clean up old records |

---

## Testing

### Unit Tests
```bash
python test_phase1.py  # Foundation tests
python test_phase2.py  # ML model tests
python test_phase3.py  # Retraining tests
```

### Integration Tests

```python
def test_supervisor_integration():
    """Test integration with supervisor"""
    # 1. Score a lead
    response = requests.post("http://lead-scoring-agent:8000/score", json={
        "lead_id": "TEST-001",
        # ... all required fields ...
    })
    assert response.status_code == 200
    
    # 2. Verify response format
    data = response.json()
    assert "conversion_score" in data
    assert 0.0 <= data["conversion_score"] <= 1.0
    
    # 3. Verify health
    health = requests.get("http://lead-scoring-agent:8000/health")
    assert health.json()["status"] == "healthy"
```

---

## FAQ

**Q: How long does retraining take?**  
A: 2-3 minutes for 50-100 feedback samples. Process runs in background.

**Q: Can I score the same lead multiple times?**  
A: Yes. Database uses UPSERT (INSERT OR REPLACE) on lead_id.

**Q: What happens if model doesn't improve during retraining?**  
A: Old model is retained. New model only deployed if AUC improves by 2%+.

**Q: How do I know if retraining is ready?**  
A: Check `/info` endpoint: `retraining_status.ready_for_retraining === true`

**Q: Can I deploy multiple instances?**  
A: Yes, but each needs its own SQLite database file or use shared PostgreSQL.

**Q: What's the maximum throughput?**  
A: Tested at 100+ requests/minute. Scale horizontally for more.

---

## Contact & Support

**Team:** Saad Khan, Shuja Uddin, Javeria Irfan  
**Supervisor:** Dr. Behjat Zuhaira  
**Documentation:** See README.md, WORKFLOW_EXPLANATION.md, FEEDBACK_LOOP.md  
**API Docs:** http://localhost:8000/docs (Swagger UI)  
**Repository:** [Your GitHub URL]

---

## Changelog

### Version 1.0 (November 22, 2025)
- ✅ Phase 1: Foundation (Database, API, Synthetic Data)
- ✅ Phase 2: ML Model Integration (Feature Engineering, LangGraph, Logistic Regression)
- ✅ Phase 3: Adaptive Learning (Automatic Retraining, Feedback Loop)
- ✅ AUC Score: 0.9986
- ✅ All acceptance criteria met

---

**Document Version:** 1.0  
**Classification:** Internal Use  
**Status:** Production Ready
