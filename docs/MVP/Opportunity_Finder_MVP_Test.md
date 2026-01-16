# OPPORTUNITY FINDER - MVP Test Build

**Purpose:** Minimum build for Mark to test if the system actually finds and scores opportunities accurately.

**Date:** 11 January 2026

---

## What This MVP Tests

> "Can the system find real opportunities from Reddit/IH/etc and score them in a way that helps me decide what to build?"

This is NOT the full product. This is a functional test of the core hypothesis.

---

## MVP Scope Summary

| Include | Exclude (Full Product Only) |
|---------|----------------------------|
| Data collection from 6 sources | Stripe payments |
| Scoring algorithm | Subscription tiers |
| Basic auth (single user) | Admin panel |
| Dashboard with opportunities | Email alerts |
| Search & filters | Landing page builder |
| Detail modal | CSV/PDF exports |
| Dark mode UI | Multi-tenant |
| Local deployment | VPS deployment |

---

## 1. BACKEND (Python/Flask)

### 1.1 Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | Flask 3.0+ |
| Database | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.0+ |
| Auth | Flask-JWT-Extended (simple) |
| Reddit | PRAW 7.7+ |
| Scraping | BeautifulSoup4 4.12+ |
| HTTP | Requests 2.31+ |

### 1.2 Database Schema (Simplified)

**users** (single user for testing)
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**opportunities**
```sql
CREATE TABLE opportunities (
  id SERIAL PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  problem TEXT,
  score INTEGER NOT NULL,
  mentions INTEGER DEFAULT 0,
  revenue VARCHAR(100),
  revenue_amount INTEGER,
  competitors INTEGER DEFAULT 0,
  competition_level VARCHAR(50),
  build_complexity VARCHAR(50),
  sources JSONB,
  source_urls JSONB,
  example TEXT,
  competitor_urls JSONB,
  validated BOOLEAN DEFAULT FALSE,
  recommendation TEXT,
  market_size TEXT,
  status VARCHAR(50) DEFAULT 'new',
  user_notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_opportunities_score ON opportunities(score DESC);
CREATE INDEX idx_opportunities_status ON opportunities(status);
```

**pain_points** (raw collected data)
```sql
CREATE TABLE pain_points (
  id SERIAL PRIMARY KEY,
  source VARCHAR(100) NOT NULL,
  text TEXT NOT NULL,
  url TEXT,
  mentions INTEGER DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 1.3 API Endpoints

**Auth (Simple)**
```
POST /api/auth/login
  Body: { email, password }
  Returns: { access_token }
```

**Opportunities**
```
GET /api/opportunities
  Query: min_score, sort, search, status
  Returns: Array of opportunities

GET /api/opportunities/:id
  Returns: Single opportunity with full details

PATCH /api/opportunities/:id
  Body: { status, user_notes }
  Returns: Updated opportunity
```

**Scan**
```
POST /api/scan
  Triggers data collection from all sources
  Returns: { job_id, status: "started" }

GET /api/scan/:job_id
  Returns: { status: "running" | "complete", opportunities_found }
```

**Stats**
```
GET /api/stats
  Returns: { total, validated, high_score_count, avg_score }
```

### 1.4 Data Collectors

Build modular collectors in `/backend/collectors/`:

**reddit.py** - REQUIRED
- Use PRAW library
- Subreddits: r/Entrepreneur, r/smallbusiness, r/SaaS, r/startups, r/indiehackers
- Keywords: "looking for a tool", "need software for", "wish there was", "tired of manually"
- Rate limit: 60 req/min with backoff

**indie_hackers.py** - REQUIRED
- BeautifulSoup scraper
- Collect: product names, MRR figures, pain points from discussions

**producthunt.py** - REQUIRED
- GraphQL API
- Collect: daily launches, comments (pain points), upvote counts

**hackernews.py** - REQUIRED
- Algolia API (free)
- Query: "Ask HN: What tool", "Ask HN: How do you"

**google_search.py** - REQUIRED
- SerpAPI
- Search: "[problem] software", "[problem] tool"
- Used for competitor discovery

**microns.py** - REQUIRED
- Scrape Microns.io / Acquire.com
- Collect: MRR data from businesses for sale

### 1.5 Scoring Algorithm

```python
def calculate_score(opportunity):
    score = 0

    # Demand Frequency (25%)
    if opportunity.mentions >= 50:
        score += 25
    elif opportunity.mentions >= 30:
        score += 15
    elif opportunity.mentions >= 20:
        score += 10

    # Revenue Proof (35%)
    if opportunity.revenue_amount >= 10000:
        score += 35
    elif opportunity.revenue_amount >= 5000:
        score += 25
    elif opportunity.revenue_amount >= 2000:
        score += 15
    elif opportunity.revenue_amount >= 1000:
        score += 10

    # Competition (20%)
    if opportunity.competitors <= 2:
        score += 20
    elif opportunity.competitors <= 5:
        score += 15
    elif opportunity.competitors <= 10:
        score += 10
    else:
        score += 5

    # Build Complexity (20%)
    if opportunity.build_complexity == 'Low':
        score += 20
    elif opportunity.build_complexity == 'Medium':
        score += 15
    else:
        score += 10

    return score
```

**Validation Rules (CRITICAL):**
An opportunity CANNOT score above 40 unless ALL of these are true:
- At least 1 competitor is charging money
- Evidence of £1,000+ MRR in niche exists
- Minimum 20 mentions across sources
- Problem is B2B (businesses will pay)

**Recommendations:**
| Score | Recommendation |
|-------|----------------|
| 80-100 | "Build immediately" |
| 60-79 | "Validate with landing page first" |
| 40-59 | "High risk - need unique angle" |
| 0-39 | "Reject - insufficient validation" |

---

## 2. FRONTEND (React)

### 2.1 Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | React 18+ |
| Build | Vite 5+ |
| Styling | Tailwind CSS |
| HTTP | Axios or fetch |

### 2.2 Pages

**Login Page**
- Email + password form
- Store JWT in localStorage (fine for testing)

**Dashboard** (main page)
- 4 stat cards: Total, Validated, High Score (80+), Avg Score
- Search bar (filter as you type)
- Sort dropdown: Score, Revenue, Mentions
- Filter: Min score slider, Status dropdown
- "Run Scan" button

**Opportunity Cards Grid**
- Score badge (color-coded: green 80+, blue 60-79, amber 40-59, red <40)
- Title
- Problem statement (truncated)
- Revenue, Mentions, Competition
- Recommendation text
- Click to open detail modal

**Detail Modal**
- Full opportunity data
- Source links (clickable)
- Competitor examples with URLs
- Market size
- Status dropdown: New, Researching, Building, Rejected
- Notes textarea (saves on blur)

### 2.3 UI Design

> Use the prototype at `/docs/HTML/opportunity-finder.html`

**Dark Mode Only (for MVP):**
- Background: Linear gradient navy (#0f172a) to slate (#1e293b)
- Cards: Semi-transparent dark, border rgba(148, 163, 184, 0.1)
- Text: White headings, #e2e8f0 body
- Score badges: Green 80+, Blue 60-79, Amber 40-59, Red <40

---

## 3. PROJECT STRUCTURE

```
opportunity-finder/
├── backend/
│   ├── app.py              # Flask app + routes
│   ├── models.py           # SQLAlchemy models
│   ├── scoring.py          # Scoring algorithm
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── reddit.py
│   │   ├── indie_hackers.py
│   │   ├── producthunt.py
│   │   ├── hackernews.py
│   │   ├── google_search.py
│   │   └── microns.py
│   ├── config.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── OpportunityCard.jsx
│   │   │   ├── OpportunityModal.jsx
│   │   │   ├── StatsCards.jsx
│   │   │   └── Filters.jsx
│   │   ├── api/
│   │   │   └── client.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── .env.example
└── README.md
```

---

## 4. ENVIRONMENT VARIABLES

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/opportunity_finder

# Auth
JWT_SECRET_KEY=<generate-random-string>

# Reddit
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx

# ProductHunt
PRODUCTHUNT_TOKEN=xxx

# SerpAPI (Google Search)
SERPAPI_KEY=xxx
```

---

## 5. REQUIRED API ACCOUNTS

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| Reddit API | Pain point discovery | Free (60 req/min) |
| ProductHunt API | Product launches | Free |
| SerpAPI | Google search | 100 searches/month free |

**Setup URLs:**
- Reddit: https://www.reddit.com/prefs/apps
- ProductHunt: https://api.producthunt.com/v2/docs
- SerpAPI: https://serpapi.com

---

## 6. ACCEPTANCE CRITERIA

### Must Work

- [ ] Can login with email/password
- [ ] "Run Scan" collects data from all 6 sources
- [ ] Opportunities display in dashboard sorted by score
- [ ] Score calculation matches algorithm (manual verify 5 opportunities)
- [ ] Validation rules enforced (nothing scores 40+ without revenue proof)
- [ ] Search filters opportunities in real-time
- [ ] Can filter by min score
- [ ] Can sort by score/revenue/mentions
- [ ] Detail modal shows all data with clickable source URLs
- [ ] Can change status (New/Researching/Building/Rejected)
- [ ] Can add notes to opportunity
- [ ] Stats cards show correct counts

### Success Test

After running a scan:
1. System finds 10+ opportunities
2. At least 3 opportunities score 60+
3. Source URLs are valid and clickable
4. Competitor examples are real products
5. Revenue figures are backed by evidence

---

## 7. HOW TO RUN

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
flask run
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Database:**
```bash
createdb opportunity_finder
flask db upgrade  # or run schema SQL manually
```

**First Run:**
1. Create user in database (or add /api/auth/register endpoint)
2. Login via frontend
3. Click "Run Scan"
4. Wait for scan to complete
5. Review opportunities

---

## 8. WHAT'S NOT INCLUDED (Full Product Later)

| Feature | Why Excluded |
|---------|--------------|
| Stripe payments | Not selling yet |
| Subscription tiers | Single user testing |
| Admin panel | No other users |
| Email alerts | Can check manually |
| Landing page builder | Not testing this |
| CSV/PDF export | Can view in UI |
| Multi-tenant | Single user |
| Production deployment | Running locally |
| Rate limiting | Single user |
| Background job queue | Can run scans synchronously for testing |

---

## 9. AFTER TESTING

Once you confirm the core works:
1. Return to full PRD (v1.7)
2. Add payment integration
3. Add subscription tiers
4. Deploy to VPS
5. Add remaining features

---

**— END OF MVP TEST DOC —**
