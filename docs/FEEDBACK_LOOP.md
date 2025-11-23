# Feedback Loop - How Sales Team Provides Conversion Data

## The Question

**"For retraining, we need to know whether the predicted lead converted or not. How does the sales team provide this data?"**

---

## Answer: The `actual_outcome` Field

The agent accepts feedback through the **same scoring endpoint** using the optional `actual_outcome` field.

---

## Method 1: Include `actual_outcome` When Scoring (Recommended)

When the sales team follows up with a lead and knows the outcome, they submit it along with the next scoring request:

```bash
# Initial scoring (no outcome yet)
POST /score
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
  "actual_outcome": null  # <-- Don't know yet
}

# Later, after follow-up (2 weeks later)
POST /score
{
  "lead_id": "LEAD-12345",  # <-- Same lead ID
  "age": 35,
  "location": "New York",
  "industry": "Technology",
  "email_opens": 20,  # More engagement
  "website_visits": 15,
  "content_downloads": 7,
  "days_since_contact": 21,
  "lead_source": "Webinar",
  "actual_outcome": true  # <-- ✅ They converted! Feedback provided
}
```

---

## What Happens Behind the Scenes

When `actual_outcome` is provided (true/false), the agent:

1. ✅ **Stores it in the database** (SQLite `lead_scores` table)
2. ✅ **Increments the feedback counter**
3. ✅ **Checks if we have 50+ feedback samples**
4. ✅ **Triggers retraining if threshold met**

### Code Implementation

In `app/workflow.py` - STORE node:

```python
def store_node(state: LeadScoringState) -> LeadScoringState:
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
            'actual_outcome': request.actual_outcome,  # ← KEY LINE
            'model_version': state['model_version'],
            'timestamp': state['timestamp']
        }
        
        # Store in database (UPSERT logic)
        db.insert_lead_score(lead_data)
        
        # If feedback provided, update metrics
        if request.actual_outcome is not None:
            feedback_count = db.get_feedback_count()
            db.update_system_metric('feedback_count', str(feedback_count))
            state['feedback_count'] = feedback_count
        
        state['stored'] = True
```

---

## Database Storage

The `lead_scores` table has an `actual_outcome` column:

```sql
CREATE TABLE lead_scores (
    lead_id TEXT UNIQUE NOT NULL,
    age INTEGER,
    location TEXT,
    industry TEXT,
    email_opens INTEGER,
    website_visits INTEGER,
    content_downloads INTEGER,
    days_since_contact INTEGER,
    lead_source TEXT,
    conversion_score REAL NOT NULL,
    risk_category TEXT NOT NULL,
    actual_outcome INTEGER,  -- ← NULL (unknown), 1 (converted), 0 (lost)
    model_version TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
```

**Values:**
- `NULL` = No feedback yet (lead not closed)
- `1` = Converted ✅
- `0` = Did not convert ❌

---

## Real-World Integration Scenarios

### Scenario A: **CRM Integration** (Most Common)

Sales team uses Salesforce/HubSpot:

```python
# In your CRM system (pseudo-code)
when lead_status_changes_to("Converted") or lead_status_changes_to("Lost"):
    lead_data = get_lead_data(lead_id)
    
    # Call the agent with outcome
    response = requests.post("http://lead-scoring-agent:8000/score", json={
        "lead_id": lead_id,
        "age": lead_data.age,
        "location": lead_data.location,
        "industry": lead_data.industry,
        "email_opens": lead_data.email_opens,
        "website_visits": lead_data.website_visits,
        "content_downloads": lead_data.content_downloads,
        "days_since_contact": lead_data.days_since_contact,
        "lead_source": lead_data.source,
        "actual_outcome": lead_data.converted  # ← Automatic feedback!
    })
```

### Scenario B: **Batch Update Script** (Weekly)

Run a script every Friday to update outcomes:

```python
# weekly_feedback_update.py
import requests
from your_crm import get_closed_leads_this_week

closed_leads = get_closed_leads_this_week()

for lead in closed_leads:
    requests.post("http://localhost:8000/score", json={
        "lead_id": lead.id,
        "age": lead.age,
        "location": lead.location,
        "industry": lead.industry,
        "email_opens": lead.email_opens,
        "website_visits": lead.website_visits,
        "content_downloads": lead.content_downloads,
        "days_since_contact": lead.days_since_contact,
        "lead_source": lead.source,
        "actual_outcome": lead.converted  # ← Feedback from CRM
    })

print(f"Updated {len(closed_leads)} leads with outcomes")
```

### Scenario C: **Manual Dashboard** (Small Teams)

Create a simple web form for sales team:

```html
<!-- feedback_form.html -->
<form action="/score" method="POST">
    <h2>Update Lead Outcome</h2>
    
    <label>Lead ID:</label>
    <input name="lead_id" placeholder="LEAD-12345" required>
    
    <label>Age:</label>
    <input name="age" type="number" required>
    
    <label>Location:</label>
    <input name="location" required>
    
    <label>Industry:</label>
    <input name="industry" required>
    
    <label>Email Opens:</label>
    <input name="email_opens" type="number" required>
    
    <label>Website Visits:</label>
    <input name="website_visits" type="number" required>
    
    <label>Content Downloads:</label>
    <input name="content_downloads" type="number" required>
    
    <label>Days Since Contact:</label>
    <input name="days_since_contact" type="number" required>
    
    <label>Lead Source:</label>
    <select name="lead_source" required>
        <option>Webinar</option>
        <option>Referral</option>
        <option>Cold Call</option>
        <option>Email Campaign</option>
        <option>Organic</option>
        <option>Trade Show</option>
        <option>Advertisement</option>
    </select>
    
    <label>Did they convert?</label>
    <select name="actual_outcome" required>
        <option value="">-- Select --</option>
        <option value="true">Yes - Converted ✅</option>
        <option value="false">No - Lost ❌</option>
    </select>
    
    <button type="submit">Submit Feedback</button>
</form>
```

---

## Check Current Feedback Count

The agent tracks how many leads have feedback:

```bash
# Check system info
GET /info

Response:
{
  "model_version": "1.0",
  "total_leads_scored": 76,
  "feedback_samples_collected": 52,  # ← 52 leads have outcomes
  "retraining_status": {
    "feedback_count": 52,
    "retraining_threshold": 50,
    "ready_for_retraining": true  # ← Ready to learn!
  }
}
```

---

## Example Flow with Timeline

### Week 1 - Monday (Initial Scoring)

```json
POST /score
{
  "lead_id": "LEAD-5001",
  "age": 42,
  "location": "San Francisco",
  "industry": "Technology",
  "email_opens": 25,
  "website_visits": 18,
  "content_downloads": 8,
  "days_since_contact": 2,
  "lead_source": "Webinar",
  "actual_outcome": null  // ← No feedback yet
}

Response: {
  "lead_id": "LEAD-5001",
  "conversion_score": 0.87,
  "risk_category": "high",
  "timestamp": "2025-11-22T10:00:00",
  "model_version": "1.0"
}
```

**Sales team action:**
- Calls the lead
- Lead says: "I'm interested, let me think about it"
- Waits for decision...

---

### Week 3 - Friday (Feedback Provided)

```json
POST /score
{
  "lead_id": "LEAD-5001",  // ← Same lead ID (UPSERT)
  "age": 42,
  "location": "San Francisco",
  "industry": "Technology",
  "email_opens": 32,  // More engagement
  "website_visits": 25,
  "content_downloads": 12,
  "days_since_contact": 16,
  "lead_source": "Webinar",
  "actual_outcome": true  // ← ✅ They signed the contract!
}

Response: {
  "lead_id": "LEAD-5001",
  "conversion_score": 0.91,
  "risk_category": "high",
  "timestamp": "2025-11-08T15:30:00",
  "model_version": "1.0"
}
```

**Behind the scenes:**
- Database updates: `actual_outcome = 1` for LEAD-5001
- Feedback count: 48 → 49
- Agent: "Almost there! Need 1 more feedback sample"

---

### Next Lead with Feedback (Retraining Triggers)

```json
POST /score
{
  "lead_id": "LEAD-5002",
  "age": 35,
  "location": "Austin",
  "industry": "Healthcare",
  "email_opens": 10,
  "website_visits": 5,
  "content_downloads": 2,
  "days_since_contact": 45,
  "lead_source": "Cold Call",
  "actual_outcome": false  // ← ❌ Did not convert
}
```

**Behind the scenes:**
- Database updates: `actual_outcome = 0` for LEAD-5002
- Feedback count: 49 → 50 ✅
- Agent: "Threshold reached! Triggering retraining..."
- Background thread starts retraining (2-3 minutes)
- New model trained with 50 actual outcomes
- If new model AUC improves by 2%+, deploy version 1.1
- User gets their score immediately (non-blocking)

---

## Why This Design is Smart

1. **Flexible**: Sales team can provide feedback anytime (immediately or weeks later)
2. **No Extra Endpoint**: Uses same `/score` endpoint (simpler API)
3. **Upsert Logic**: Same `lead_id` updates the record (INSERT OR REPLACE)
4. **Non-Intrusive**: If no feedback, just pass `null` - system still works
5. **Automatic**: Once threshold hit, retraining happens automatically
6. **Non-Blocking**: User never waits for retraining (background thread)

---

## Optional: Dedicated Feedback Endpoint

If you want a **simpler way** for sales teams to just update outcomes without resending all lead data, you can add:

```python
# In app/main.py - Add this endpoint

@app.put(
    "/feedback/{lead_id}",
    status_code=status.HTTP_200_OK,
    summary="Update lead outcome",
    description="Update actual conversion outcome for an existing lead"
)
async def update_feedback(
    lead_id: str,
    outcome: bool
) -> Dict[str, Any]:
    """
    Update actual outcome for a lead
    
    Usage:
      PUT /feedback/LEAD-12345?outcome=true
      PUT /feedback/LEAD-12345?outcome=false
    """
    success = db.update_lead_outcome(lead_id, outcome)
    
    if success:
        feedback_count = db.get_feedback_count()
        return {
            "message": "Feedback recorded",
            "lead_id": lead_id,
            "outcome": outcome,
            "total_feedback": feedback_count
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead {lead_id} not found"
        )
```

**Usage:**
```bash
# Lead converted
PUT /feedback/LEAD-12345?outcome=true

# Lead did not convert
PUT /feedback/LEAD-12345?outcome=false
```

**Response:**
```json
{
  "message": "Feedback recorded",
  "lead_id": "LEAD-12345",
  "outcome": true,
  "total_feedback": 51
}
```

This is **much simpler** for manual updates! Sales team doesn't need to resend all lead data.

---

## Summary

The feedback loop works through:

1. **Storage**: `actual_outcome` field in database (NULL/1/0)
2. **Collection**: Via `/score` endpoint or optional `/feedback` endpoint
3. **Tracking**: Feedback count monitored in real-time
4. **Trigger**: Automatic retraining at 50+ samples
5. **Learning**: Model improves based on actual outcomes
6. **Deployment**: New model auto-deployed if it improves by 2%+

**The agent learns from reality, not just predictions!** 🎯
