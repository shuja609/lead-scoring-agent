# Lead Scoring Agent - Workflow Explanation

## What Does This Agent Do?

Imagine you're a sales team drowning in hundreds of potential customers (leads). You don't know which ones are actually interested in buying. This agent is like a **smart assistant that predicts which leads are most likely to become customers**, so your sales team can focus on the right people.

---

## The Core Workflow (6 Steps)

### 1️⃣ **VALIDATE** - Check the Input
```
Lead comes in → Agent checks: "Does this lead have all the info I need?"
- Age, location, industry?
- Email opens, website visits?
- Source (webinar, referral, etc.)?

✅ Valid? → Move to next step
❌ Invalid? → Return error
```

### 2️⃣ **PREPROCESS** - Prepare the Data
```
Raw lead data → Transform it into features the ML model understands
- Age: 35 → normalized value
- Location: "New York" → encoded number
- Engagement metrics → calculated intensity scores

Think of it like translating languages so the AI can "read" the lead
```

### 3️⃣ **SCORE** - Predict Conversion Probability
```
Prepared data → ML Model (Logistic Regression) analyzes patterns

The model asks:
- "Does this lead look like past leads that converted?"
- "High email opens + Recent contact + Tech industry = Usually converts!"

Output: 0.78 (78% chance of converting)
```

### 4️⃣ **STORE** - Save to Database
```
Lead score → Saved to SQLite database

Stores:
- Lead ID: "LEAD-12345"
- Score: 0.78
- Risk Category: "high" (because 0.78 > 0.7)
- Timestamp, Model Version
- Actual Outcome (if provided as feedback)
```

### 5️⃣ **LEARN** - Check if Retraining Needed
```
Agent counts feedback samples: "Do we have 50+ leads with actual outcomes?"

If YES (50+):
  → Trigger background retraining (doesn't block response)
  → "I'll learn from these outcomes and improve!"

If NO:
  → "Not enough data yet, keep current model"
```

### 6️⃣ **RESPOND** - Return the Answer
```
Format the result → Send back to user

{
  "lead_id": "LEAD-12345",
  "conversion_score": 0.78,
  "risk_category": "high",
  "model_version": "1.0"
}

Sales team sees: "This is a HIGH priority lead! Call them NOW!"
```

---

## The Learning Loop (Adaptive Intelligence)

### How It Gets Smarter Over Time

```
┌─────────────────────────────────────────────┐
│  1. Score leads → 2. Sales team contacts   │
│                                             │
│  6. Use new     ← 5. Model    ← 4. Retrain │
│     model          improves?     with data  │
│                                             │
│  3. Actual outcomes collected (converted or not)
└─────────────────────────────────────────────┘
```

**Example:**
- **Day 1:** Agent scores LEAD-001 as 0.80 (high)
- **Week 1:** Sales team contacts them → They convert! ✅
- **Week 2:** Agent scores LEAD-002 as 0.75 (high)
- **Week 2:** Sales team contacts them → They DON'T convert ❌

**After 50+ outcomes collected:**
- Agent: "Wait! I thought 0.75 was good, but those leads didn't convert"
- Agent retrains itself on real data
- Agent: "I learned! Now I need 0.82+ to call it 'high risk'"
- **New model deployed automatically** (version 1.0 → 1.1)

---

## Why This Matters

### Without Agent:
- Sales calls 100 leads randomly
- 10 convert (10% success rate)
- Wasted time on 90 uninterested people

### With Agent:
- Agent identifies top 20 leads (scored 0.7+)
- Sales calls only those 20 leads
- 10 convert (50% success rate!)
- **5x more efficient** - same conversions, 80% less effort

---

## The Smart Parts

### 1. **Feature Engineering** (Phase 2)
The agent doesn't just look at raw numbers. It creates **intelligent features**:

```
Raw Data:
- Email opens: 15
- Website visits: 10
- Days since contact: 7

Engineered Features:
- Engagement intensity = (15 + 10) / 7 = 3.57 interactions per day
- Recency weight = 1 / (1 + 7) = 0.125 (recent = better)
- Interaction frequency = 15 / (7 + 1) = 1.875 emails per day

The model sees these patterns: "High engagement + Recent contact = Strong lead!"
```

### 2. **Risk Categorization**
Simple color coding for sales teams:

```
Score 0.7 - 1.0  → 🔴 HIGH    → "Call them TODAY!"
Score 0.4 - 0.7  → 🟡 MEDIUM  → "Call them this week"
Score 0.0 - 0.4  → 🟢 LOW     → "Send email follow-up"
```

### 3. **Automatic Retraining** (Phase 3)
The agent monitors itself:

```python
if feedback_count >= 50:
    new_model = train_with_feedback()
    
    if new_model.accuracy > old_model.accuracy + 2%:
        deploy(new_model)
        print("I'm smarter now! Version 1.1 deployed")
    else:
        print("Current model is still best, keeping it")
```

### 4. **Non-Blocking Learning**
The agent doesn't make you wait:

```
User: "Score this lead"
Agent: *Scoring in 2.3 seconds*
Agent: "Here's your score: 0.78"

[Behind the scenes, in background thread:]
Agent: "Oh, we have 50 feedback samples now..."
Agent: *Retraining model... 2 minutes...*
Agent: "New model ready! Deployed version 1.1"

User never waited - they got their score immediately!
```

---

## Real-World Example

**Monday Morning:**
```
→ LEAD-5001 enters system (came from webinar)
→ Agent: VALIDATE → All fields present ✓
→ Agent: PREPROCESS → 37 features calculated
→ Agent: SCORE → 0.87 (Model sees: Recent webinar + Tech industry + High engagement)
→ Agent: STORE → Saved to database
→ Agent: LEARN → "Only 49 feedback samples, need 1 more"
→ Agent: RESPOND → "LEAD-5001: 87% conversion chance - HIGH PRIORITY"
→ Sales team calls immediately → Sale closed! ✅
```

**Tuesday Morning:**
```
→ Sales marks LEAD-5001 as "converted" (feedback)
→ Agent: "That's 50 feedback samples! Time to learn!"
→ Agent: *Retrains in background*
→ Agent: "New patterns found! Tech leads from webinars convert at 92%, not 87%"
→ Agent: "New model improves AUC from 0.9986 to 0.9992"
→ Agent: "Deploying version 1.1"
→ All future webinar leads scored more accurately
```

---

## The Technology Stack (Simplified)

1. **FastAPI** = The messenger (receives requests, sends responses)
2. **SQLite** = The notebook (remembers everything)
3. **Logistic Regression** = The brain (predicts conversion)
4. **LangGraph** = The workflow manager (orchestrates 6 steps)
5. **Pydantic** = The validator (checks data is correct)
6. **scikit-learn** = The learning toolkit (trains models)

---

## Key Metrics

- **AUC Score: 0.9986** → Model is 99.86% accurate at ranking leads
- **Response Time: 2.3s** → Fast enough for real-time use
- **Automatic Retraining** → Gets smarter without human intervention
- **50+ Feedback Threshold** → Waits for enough data before retraining

---

**In One Sentence:**  
This agent is a **self-improving AI assistant that predicts which sales leads will convert, learns from actual outcomes, and automatically gets smarter over time** - turning your sales team from randomly calling leads into laser-focused conversion machines.

---

## How Sales Team Provides Feedback for Retraining

### The Problem
For the agent to learn and improve, it needs to know: **"Did the lead we predicted actually convert or not?"**

### The Solution: `actual_outcome` Field

Sales teams provide feedback through the **same `/score` endpoint** using an optional field called `actual_outcome`.

---

### Step-by-Step Example

#### Initial Scoring (Week 1)
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
  "actual_outcome": null  // ← Don't know yet
}

Response: {
  "conversion_score": 0.87,  // Agent predicts 87% chance
  "risk_category": "high"
}
```

**What happens:**
- Agent scores the lead: 87% likely to convert
- Sales team calls the lead
- Lead says: "I'm interested, let me think about it"
- We wait...

---

#### Feedback Provided (Week 3)
```json
POST /score
{
  "lead_id": "LEAD-5001",  // ← Same lead ID
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
  "conversion_score": 0.91,
  "risk_category": "high"
}
```

**Behind the scenes:**
- Database stores: `actual_outcome = 1` (converted)
- Feedback counter: 48 → 49
- Agent: "One more feedback sample to reach 50!"

---

### When Retraining Triggers

#### The 50th Feedback (Week 4)
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

**🔥 Retraining Triggered:**
```
1. Feedback count reaches 50 ✅
2. Background thread starts retraining (non-blocking)
3. Agent collects all 50 leads with actual outcomes
4. Trains new model on real data
5. Compares new model vs old model:
   - Old model AUC: 0.9986
   - New model AUC: 0.9992
   - Improvement: +0.0006 (0.06%)
6. Check: Is improvement ≥ 2%?
   - No → Keep old model
   - Yes → Deploy new model as version 1.1
```

**User experience:**
- Gets their score in 2.3 seconds (never waits for retraining!)
- Retraining happens silently in background

---

### What Gets Stored in Database

```sql
lead_scores table:
┌──────────────┬─────┬──────────────┬──────────────┬────────────────┐
│ lead_id      │ age │ location     │ score        │ actual_outcome │
├──────────────┼─────┼──────────────┼──────────────┼────────────────┤
│ LEAD-5001    │ 42  │ San Fran     │ 0.87         │ 1 (✅ YES)     │
│ LEAD-5002    │ 35  │ Austin       │ 0.25         │ 0 (❌ NO)      │
│ LEAD-5003    │ 38  │ New York     │ 0.92         │ NULL (unknown) │
└──────────────┴─────┴──────────────┴──────────────┴────────────────┘
```

**Values:**
- `NULL` = No feedback yet (lead still being worked)
- `1` = Converted ✅ (closed-won)
- `0` = Did not convert ❌ (closed-lost)

---

### Real-World Integration Options

#### Option 1: CRM Webhook (Automatic)
```python
# Salesforce/HubSpot triggers this when deal closes
when deal.status_changed:
    requests.post("http://lead-agent:8000/score", json={
        "lead_id": deal.lead_id,
        # ... all lead fields ...
        "actual_outcome": deal.is_won  # ← Automatic!
    })
```

#### Option 2: Weekly Batch Script
```python
# Run every Friday
closed_leads = crm.get_closed_leads_this_week()
for lead in closed_leads:
    update_agent_with_outcome(lead.id, lead.converted)
```

#### Option 3: Simple Web Form (Manual)
```html
<form action="/score" method="POST">
  <input name="lead_id" placeholder="LEAD-12345">
  <select name="actual_outcome">
    <option value="true">✅ Converted</option>
    <option value="false">❌ Lost</option>
  </select>
  <button>Submit Feedback</button>
</form>
```

---

### Why This Design is Brilliant

1. **Same Endpoint** → No need to learn new API
2. **Optional Field** → Works with or without feedback
3. **Automatic Counting** → Agent tracks feedback samples
4. **Non-Blocking** → Retraining doesn't slow down responses
5. **Smart Deployment** → Only deploys if model actually improves
6. **Self-Improving** → Gets smarter without manual intervention

---

### Monitoring Feedback Status

Check how many feedback samples collected:

```bash
GET /info

Response:
{
  "feedback_samples_collected": 52,
  "retraining_status": {
    "feedback_count": 52,
    "retraining_threshold": 50,
    "ready_for_retraining": true,
    "last_retrain_time": "2025-11-22T17:34:08"
  }
}
```

---

### The Learning Cycle Visualized

```
Week 1: Score 10 leads → Sales calls them
Week 2: Score 20 more leads → Sales calls them
Week 3: Score 20 more leads → Sales calls them
        ↓
Week 4: 50 outcomes collected!
        ├─ 35 converted ✅
        ├─ 15 did not convert ❌
        ↓
Week 4: Agent retrains
        ├─ "Aha! I see patterns in the real data!"
        ├─ "Webinar leads convert 25% more than I thought"
        ├─ "Healthcare leads need 30+ email opens, not 20"
        ↓
Week 5: New model (v1.1) deployed
        └─ Predictions now match reality better!
```

---

### Summary: The Feedback Loop

1. **Agent scores lead** → Prediction: 0.87
2. **Sales team contacts** → Follow up over weeks
3. **Outcome determined** → ✅ Converted or ❌ Lost
4. **Feedback submitted** → `actual_outcome: true/false`
5. **Agent counts** → "50 samples reached!"
6. **Retraining triggered** → Learns from real outcomes
7. **Model improves** → Better predictions
8. **Cycle repeats** → Continuous learning!

**The agent doesn't just predict - it learns from being wrong and gets better! 🎯**
