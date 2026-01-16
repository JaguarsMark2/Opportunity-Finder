# OPPORTUNITY FINDER

## Product Requirements Document

**Version 2.0 - Phase 1: Single-User MVP**

**14 January 2026**

| Field | Value |
|-------|-------|
| Status | APPROVED FOR DEVELOPMENT |
| Owner | Mark |
| Target Delivery | As soon as possible via AI |
| Phase | Phase 1: Single-user MVP for product owner. Phase 2: Multi-user SaaS production model. |

---

## EXECUTIVE SUMMARY

### Product Vision

Opportunity Finder is a systematic validation platform for micro-SaaS entrepreneurs delivered as a subscription SaaS product with **admin-configurable pricing**. It eliminates guesswork by collecting real market demand signals from multiple sources, validating them against existing solutions and revenue data, and producing scored opportunities with clear build/no-build recommendations. Built from day one as a multi-tenant, payment-enabled platform with mobile-ready architecture. Pricing is set by the admin through the Admin Panel and can be changed at any time without code deployment.

### Problem Statement

Indie developers and entrepreneurs waste months building products nobody wants because:

- They guess at problems rather than finding validated demand
- Manual research across multiple platforms is time-consuming and inconsistent
- No systematic way to validate if people will actually pay
- Opportunity assessment is subjective and emotionally driven

### Solution

Automated system that monitors Reddit, Indie Hackers, ProductHunt, HackerNews, and other sources for pain points, validates them against existing paid solutions, scores opportunities 0-100 based on demand/revenue/competition/complexity, and provides clear recommendations.

### Success Metrics

| Priority | Metric |
|----------|--------|
| Primary | System accurately scores opportunities based on defined criteria |
| Secondary | Product owner identifies 1+ buildable opportunity per week |
| Tertiary | System collects and validates data from all 6 sources reliably |

> **Note:** "Validation success with landing page test" metric will be defined during Phase 2 (production model) planning. For Phase 1, success is defined as accurate scoring, reliable data collection, and functional system.

---

## 1. PHASE SCOPE DEFINITION

### Phase 1: Single-User MVP (Current Document)
- **Purpose:** Validate product concept with product owner (Mark) as sole user
- **Scope:** Full system for single user, all features functional
- **Delivery:** Complete working system running on local/VPS
- **Data Model:** Global scan runs, tier-based visibility (single tier for product owner)
- **Post-Phase 1:** Decision to proceed to Phase 2 based on system effectiveness

### Phase 2: Multi-User SaaS (Future)
- **Purpose:** Offer as subscription service to external users
- **Scope:** Add multi-user onboarding, trial flows, full production support
- **Delivery:** Separate production planning phase
- **Decision:** Triggered by successful Phase 1 validation

**This PRD documents Phase 1 requirements. Phase 2 will require separate planning based on Phase 1 outcomes.**

---

## 2. PRODUCT OVERVIEW

### 2.1 Target User

**Primary:**
- Solo indie developers with React/Python skills building first SaaS
- Former employees with 3-6 month runway seeking validated opportunities
- Willing to pay the configured subscription price for systematic validation vs months of guessing
- Need to identify £1k+ MRR opportunities quickly before runway expires

### 2.2 Use Cases

| Use Case | Description |
|----------|-------------|
| Weekly Opportunity Discovery | User runs weekly scan, reviews top 10 opportunities, identifies 1-3 to investigate further |
| Idea Validation | User has idea, searches system to see if demand exists and validates score |
| Market Research | User explores specific niche (e.g., 'freelancer tools') to find gaps |

### 2.3 Core Value Proposition

> "Stop guessing. Build what people are actively looking for and willing to pay for."

---

## 3. TECHNICAL ARCHITECTURE

### 3.1 System Components

**Backend (Python/Flask)**
- **Authentication:** JWT-based auth with secure session management
- **Payment Processing:** Stripe integration for subscriptions (price configured by admin via Admin Panel)
- **Data Collectors:** Modular scrapers for each source
- **Validation Engine:** Checks for existing solutions and revenue
- **Scoring Engine:** Calculates 0-100 score based on weighted criteria
- **REST API:** Exposes endpoints for frontend (with auth middleware)
- **Database:** PostgreSQL with multi-tenant architecture
- **Caching:** Redis for session storage, API response caching, and rate limiting
- **Background Jobs:** Celery with Redis broker for async scan jobs, email sending, PDF generation

**Frontend (React)**
- **Authentication:** Login/signup/password reset
- **Subscription Management:** Stripe checkout integration, billing portal
- **Dashboard:** Overview stats and top opportunities
- **Opportunity Cards:** Filterable, sortable grid view
- **Detail Modal:** Full opportunity breakdown with sources
- **Search & Filters:** Real-time filtering by score, keyword, time range
- **Theme Toggle:** Dark mode (default) with light mode option

**UI Design Specification**

> **CRITICAL:** Use approved prototype design at `docs/PRD/opportunity-finder.html`

**Dark Mode (Default):**
- Background: Linear gradient from navy (#0f172a) to slate (#1e293b)
- Cards: Semi-transparent dark with subtle borders (rgba(148, 163, 184, 0.1))
- Text: White (#fff) for headings, light slate (#e2e8f0) for body
- Score badges: Color-coded (green 80+, blue 60-79, amber 40-59, red <40)

**Light Mode (Optional Toggle):**
- Background: White to light gray gradient
- Cards: White with subtle shadows
- Text: Dark gray for body, black for headings

### 3.2 Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Backend | Python + Flask | 3.11+ / 3.0+ |
| Frontend | React + Vite + TypeScript | 18+ / 5+ |
| Database | PostgreSQL | 15+ |
| ORM | SQLAlchemy | 2.0+ |
| Authentication | Flask-JWT-Extended | 4.6+ |
| Payments | Stripe Python SDK | 8.0+ |
| Email | SendGrid / Mailgun | Latest |
| PDF Generation | ReportLab | 4.0+ |
| Reddit | PRAW | 7.7+ |
| Web Scraping | BeautifulSoup4 | 4.12+ |
| API Calls | Requests | 2.31+ |
| Search | SerpAPI | Latest |
| CORS | Flask-CORS | 4.0+ |
| Password Hashing | bcrypt | 4.1+ |
| Caching | Redis | 7.0+ |
| Background Jobs | Celery | 5.3+ |
| Rate Limiting | Flask-Limiter | 3.5+ |

### 3.3 Deployment Architecture

| Environment | Configuration |
|-------------|---------------|
| Development | Local (localhost:3000 frontend, localhost:5000 backend) |
| Production | VPS deployment (DigitalOcean/Hetzner) |
| Frontend | Nginx serving React build |
| Backend | Gunicorn + Flask behind Nginx reverse proxy |
| Redis | Local instance for caching, sessions, job queue |
| Mobile Ready | API-first design allows future React Native/Flutter app using same backend |

#### File Storage

| File Type | Storage Location | Notes |
|-----------|------------------|-------|
| PDF exports | `/var/app/exports/` (local) | Auto-delete after 24 hours |
| CSV exports | `/var/app/exports/` (local) | Auto-delete after 24 hours |
| Landing pages | Database (HTML stored in table) | Served dynamically |

**Scale Path:** When storage exceeds 10GB, migrate to S3-compatible storage (Backblaze B2, AWS S3).

#### CDN (Future Scale)

Not required for MVP. When traffic exceeds 10,000 daily users:
- Cloudflare free tier for static assets (JS, CSS, images)
- Cache API responses at edge for public data
- Keep dynamic/authenticated endpoints on origin

### 3.4 Quality Architecture Requirements

#### Security Architecture

1. **JWT Implementation**: Short-lived access tokens (15min) + refresh tokens with Redis revocation capability
2. **Webhook Security**: Stripe signature verification on every request + idempotency table
3. **Data Isolation**: Row-level security at database level, not just application level
4. **Rate Limiting**: Per-user limits, not global (prevents DoS from single abusive user)

#### Performance Architecture

1. **Caching Strategy**: Redis cache opportunities by user_id + filter combination, invalidate on new scan
2. **Query Optimization**: Composite index `(user_id, score DESC)` for hot path queries
3. **Pagination**: Cursor-based using `id`, not offset (critical for scale)
4. **Collector Optimization**: Pre-calculate scores during collection, not on read

#### Operations Architecture

1. **Structured Logging**: JSON format with `timestamp, level, user_id (or 'anonymous'), request_id, event_type`
2. **Error Categorization**: User errors (400s) at INFO level, system errors (500s) at ERROR with full context
3. **Job Visibility**: Scan jobs track progress percentage, opportunities found, source-by-source completion
4. **Health Endpoints**: `/health` for load balancer, `/health/detailed` for admin with DB/Redis/collector status

#### Data Architecture

1. **Transaction Boundaries**: Scoring calculation atomic - calculate, validate, insert in single transaction
2. **Index Strategy**:
   - `(user_id, score DESC)` - main query
   - `(user_id, status)` - filtering
   - `(created_at DESC)` - time filtering
   - GIN tsvector for search
3. **Audit Integrity**: `old_values`/`new_values` JSONB captures full record snapshot, not partial
4. **Webhook Idempotency**: `webhook_events` table primary key on `event_id`, check before insert

### 3.5 Architectural Decisions

The following architectural decisions have been made for Phase 1:

| Category | Decision | Rationale |
|----------|----------|-----------|
| **Project Structure** | Manual Flask + React Vite | Flask provides flexibility for multi-tenant architecture; no single template handles both appropriately |
| **Authentication** | Redis-based refresh tokens | PRD requires Redis revocation capability; supports immediate account suspension for God-mode admin |
| **Data Collection** | Keyword matching + Manual review (Phase 1) | Simple to implement initially; NLP/ML clustering can be added in Phase 2 |
| **Scoring Algorithm** | Admin-configurable weights in database | Essential for testing different scoring approaches without code deployment |
| **API Design** | Cursor-based pagination | Required for scale; industry standard for large datasets |
| **Background Jobs** | Celery + Redis broker | Industry standard for Flask; Redis already required for caching |
| **Admin Panel** | Full God-mode with audit trail | Required for user impersonation, emergency overrides, and production incident handling |
| **Deployment** | Direct VPS (DigitalOcean/Hetzner) | Phase 1 single-user MVP - containers add complexity; Docker can be Phase 2 consideration |

---

## 4. DATA SOURCES

> All data sources must be implemented. No optional sources in MVP.
> **Scan Architecture:** Global scan runs on schedule set by admin. All users share same opportunity pool. User's subscription tier determines which opportunities they can view (not unique per-user data).
> **Scan Schedule:** Admin configures scan frequency via Admin Panel. Default: Daily scans, potentially running twice daily. Scan progress displayed to users but not user-triggered (system-decided execution).

### 4.1 Reddit

| Field | Value |
|-------|-------|
| Purpose | Primary pain point discovery |
| Implementation | PRAW (Python Reddit API Wrapper) |
| Rate Limits | 60 requests/minute. Implement exponential backoff. |

**Subreddits:**
- r/Entrepreneur
- r/smallbusiness
- r/freelance
- r/SaaS
- r/startups
- r/indiehackers
- r/productivity

**Search Keywords:**
- "looking for a tool"
- "need software for"
- "wish there was"
- "hate that I have to"
- "tired of manually"
- "paying too much for"

### 4.2 Indie Hackers

| Field | Value |
|-------|-------|
| Purpose | Revenue validation + pain points |
| Implementation | BeautifulSoup4 web scraping |
| Update Frequency | Weekly scan of new products |

**Data to Collect:**
- Product names and descriptions
- MRR/ARR figures
- Founder interviews (pain points)
- Discussion threads

### 4.3 ProductHunt

| Field | Value |
|-------|-------|
| Purpose | New product launches + user feedback |
| Implementation | GraphQL API (free tier) |

**Data to Collect:**
- Daily top launches
- Comment threads (pain points)
- Upvote counts (demand signal)

### 4.4 HackerNews

| Field | Value |
|-------|-------|
| Purpose | Technical pain points from 'Ask HN' threads |
| Implementation | Algolia HN Search API (free) |

**Query Patterns:**
- "Ask HN: What tool"
- "Ask HN: How do you"
- "Show HN" (for validation)

### 4.5 Google Search

| Field | Value |
|-------|-------|
| Purpose | Competitor discovery + revenue validation |
| Implementation | SerpAPI (100 free searches/month) |
| Search Pattern | "[problem] software", "[problem] tool", "[problem] SaaS" |
| Use | Validate existing solutions, count competitors |

### 4.6 Microns.io / Acquire.com

| Field | Value |
|-------|-------|
| Purpose | Real MRR data from businesses for sale |
| Implementation | Web scraping (public listings) |
| Data | Product name, MRR, problem solved |

### 4.7 Community Signals (Additional Data Source)

| Field | Value |
|-------|-------|
| Purpose | Multi-platform engagement tracking to measure demand volume |
| Implementation | Aggregate engagement metrics across Reddit, YouTube, Facebook, and other communities |
| Data | Engagement counts, discussion volume, trending indicators |
| Use | Validate demand by showing how widely a problem is discussed across platforms |

> **Note:** This aggregates existing public engagement data. No Facebook Ads or Amazon Books integration in Phase 1.

---

## 5. SCORING ALGORITHM & DATA PROCESSING

### 5.1 Data Processing Pipeline

> **CORE FUNCTIONALITY:** This is how the system converts raw pain points into scored opportunities.

**Pipeline Steps:**

1. **Data Collection** (Section 4 - Data Sources)
   - Collect raw pain points from Reddit, IH, PH, HN, Google, Microns
   - Each raw entry: text, source URL, timestamp, platform

2. **Pain Point Clustering** (Algorithm TBD)
   - Group similar pain points into "opportunities"
   - Cluster by semantic similarity (problem keywords, phrasing)
   - Merge duplicate mentions across sources
   - **Phase 1 Implementation:** Simple keyword-based clustering
   - **Phase 2 Enhancement:** NLP/ML clustering when validated by user feedback

3. **Opportunity Generation**
   - For each cluster, create 1 opportunity record
   - Aggregate: total mentions, source list, source URLs
   - Track: first seen date, last seen date, mentions trend

4. **Data Enrichment**
   - Search competitors for opportunity via Google
   - Extract: competitor count, competitor URLs, example MRR data
   - Determine: build complexity (manual classification initially, keyword analysis enhancement later)

5. **Scoring Calculation** (Section 5.2)
   - Apply weight formula: demand + revenue + competition + complexity
   - Store final score (0-100)

6. **Validation Check** (Section 5.4)
   - Check against validation rules (paid solution, £1k+ MRR, 20+ mentions, B2B)
   - Set "validated" boolean flag

7. **Recommendation Assignment** (Section 5.5)
   - Based on score + validation status
   - Store recommendation text

**Data Flow:**
```
Raw Pain Points → Clustering → Opportunity Record → Enrichment → Scoring → Validation → Recommendation → Display to User
```

**Phase 1 Clustering Approach (Simple):**
- Group by exact keyword matches
- Group by similar phrasing (e.g., "need X tool", "looking for X software")
- Manual review of clusters that don't auto-group cleanly

**Phase 2 Enhancement (Optional):**
- NLP-based semantic similarity
- ML clustering algorithm
- User feedback loop to improve clustering accuracy

### 5.2 Scoring Weights (Admin-Configurable)

> **Purpose:** Beyond basic scoring (mentions, revenue, competition, complexity), additional criteria provide deeper insight into opportunity quality. These criteria are derived from industry best practices and ideabrowser.com analysis framework.

**Evaluation Criteria Overview:**

| Criterion | Type | Description | Implementation |
|-----------|------|-------------|-----------------|
| **Demand Frequency** | Quantitative | Count of mentions across all sources | Collected from data sources |
| **Revenue Proof** | Quantitative | Existing MRR in niche from competitors | Extracted from IH/Microns/Acquire listings |
| **Competition** | Quantitative | Number of competing solutions | Google search + manual verification |
| **Build Complexity** | Qualitative | Simple/Moderate/Complex difficulty | Manual classification (admin-configurable tags/keywords) |
| **Timing / Market Trend** | Qualitative | 1-10 scale: Is market growing now? Right time to enter? | Derived from trend data + historical analysis + growth rate calculations |
| **Feasibility Score** | Qualitative | 1-10 scale: how executable is this? | Based on tech stack, resources, complexity, keyword triggers |
| **Problem Severity** | Qualitative | 1-10 scale: how painful is this problem? | User feedback intensity + mention frequency + emotional hook analysis |
| **Revenue Potential** | Quantitative | Estimated ARR range for market (e.g., "$10M-$100M") | Market size data + competitor revenue extrapolation + growth projections |
| **Market Gap Analysis** | Qualitative | What are existing solutions missing? | Competitor feature gap analysis + unmet customer needs |
| **Keyword Volume Metrics** | Quantitative | Search term demand | Volume metrics (e.g., "2.9K", "4.4K searches"), growth rate (e.g., "+303% YoY"), competition level (LOW/MEDIUM/HIGH) |

**Base Scoring Weights:**

| Factor | Default Weight | Admin-Adjustable? |
|--------|---------------|-------------------|
| Demand Frequency | 25% | Yes |
| Revenue Proof | 35% | Yes |
| Competition | 20% | Yes |
| Build Complexity | 20% | Yes |

> **Admin Panel:** All weights adjustable via Admin Panel under "Scoring Criteria" section. Changes affect future scoring, can be recalculated for existing opportunities.

### 5.3 Qualitative Scores (Manual + Admin-Configurable)

Three qualitative criteria that are not directly data-collected but assessed:

| Criterion | Scale | Assessment Method | Admin Config |
|-----------|-------|-------------------|---------------|
| **Feasibility** | 1-10 | Founder + manual review | Keyword triggers + manual override |
| **Problem Severity** | 1-10 | User engagement intensity + keyword analysis | Keyword triggers + manual override |
| **Timing/Urgency** | 1-10 | Market trend analysis (growth rate) | Automated + manual override |

> **Implementation Notes:**
> - Keywords can be configured in Admin Panel to auto-classify opportunities (e.g., "dashboard" → Feasibility 8, "AI" → Feasibility 4)
> - Admin can manually override any qualitative score for specific opportunities
> - Qualitative scores are factored into recommendation but not base 0-100 score

### 5.4 Validation Rules

> **CRITICAL:** Validation rules determine whether opportunity is MARKED AS VALIDATED. Scoring (0-100) happens independently.

**Validation Criteria (all must be true for "validated" status):**

- **Existing Paid Solution:** At least 1 competitor charging money
- **Revenue Proof:** Evidence of £1,000+ MRR in niche
- **Frequency:** Minimum 20 mentions across sources
- **B2B Problem:** Businesses will pay, not just consumers

> **Important:** Opportunity can score highly (60-100) without being validated. Validation is a separate flag. Recommendation logic combines score + validation status.

### 5.5 Recommendation Logic

| Score | Validated? | Recommendation |
|-------|-------------|----------------|
| 80-100 | Must be validated | "Build immediately" - All signals green, revenue proof confirmed |
| 60-79 | Must be validated | "Strong candidate - validate with landing page before building" |
| 40-59 | May not be validated | "High risk - need unique angle, proceed with caution" |
| 20-39 | Unlikely validated | "Reject - insufficient validation, do not build" |
| 0-19 | Not validated | "Reject - minimal data, do not build" |

> **Note:** Recommendations are based on both score AND validation status. High scores without validation still require landing page testing.

### 5.6 Evaluation Methodology

> **CRITICAL:** Evaluation methodology must be agreed and documented.

**Methodology Areas:**

| Area | Approach |
|--------|-------------------|
| **Revenue Extraction** | Algorithm parsing of Indie Hackers listings + Regex from text + Manual annotation from founder interviews |
| **Build Complexity Classification** | Keyword analysis (keywords like "dashboard", "API", "machine learning") + Manual tags by admins |
| **B2B vs B2C Detection** | Keyword heuristics (B2B terms) + Source-specific patterns (Reddit vs IH) + Manual review |
| **Validation Threshold Calibration** | Admin-configurable via Admin Panel: revenue threshold, competitor count, mention frequency |

---

## 6. FEATURE SPECIFICATIONS

### 6.1 Backend API Endpoints

#### API Versioning

All API endpoints are prefixed with `/api/v1/`. This allows future breaking changes via `/api/v2/` without disrupting existing clients.

```
Base URL: https://opportunityfinder.app/api/v1/
Example:  GET /api/v1/opportunities
```

**Version Deprecation Policy:**
- New versions announced 3 months before old version sunset
- Old versions supported for 6 months after new version release
- Breaking changes only in major version bumps

#### Pagination Standard

All list endpoints support cursor-based pagination for consistent performance at scale:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | int | 50 | Items per page (max: 100) |
| cursor | string | null | Opaque cursor for next page |

**Response Format:**
```json
{
  "data": [...],
  "pagination": {
    "has_more": true,
    "next_cursor": "eyJpZCI6MTAwfQ==",
    "total_count": 500
  }
}
```

#### Authentication Endpoints

**POST /api/v1/auth/register**
- Purpose: Create new user account
- Body: email, password
- Action: Sends verification email to user

**GET /api/v1/auth/verify-email/:token**
- Purpose: Verify email address via link in email
- Action: Sets user.email_verified=true, redirects to login

**POST /api/v1/auth/login**
- Purpose: Authenticate and get JWT token
- Returns: access_token, refresh_token (only if email verified)

**POST /api/v1/auth/forgot-password**
- Purpose: Request password reset
- Body: email
- Action: Sends password reset email with token (expires in 1 hour)

**POST /api/v1/auth/reset-password**
- Purpose: Reset password with token
- Body: token, new_password

**POST /api/v1/auth/refresh**
- Purpose: Refresh access token using refresh token
- Returns: new access_token

#### Payment Endpoints

**POST /api/v1/payments/create-checkout**
- Purpose: Create Stripe checkout session for subscription based on selected tier price
- Returns: checkout_url
- Note: Tier price is fetched from subscription_tiers table, which is admin-controlled via Admin Panel

**POST /api/v1/payments/webhook**
- Purpose: Handle Stripe webhook events (payment success, subscription cancelled)
- Updates: user.subscription_status in database

#### Opportunity Endpoints

**GET /api/v1/opportunities**
- Purpose: Retrieve user's opportunities with filtering
- Auth: Requires valid JWT token. Returns only current user's opportunities.
- Query Parameters:
  - min_score (int, default: 0)
  - sort (string: 'score', 'revenue', 'mentions', default: 'score')
  - search (string: keyword search)
  - time_range (string: '3days', '1week', '1month', 'all', default: 'all')
  - status (string: 'new', 'researching', 'building', 'rejected', default: all)
  - limit (int, default: 50, max: 100)
  - cursor (string: pagination cursor)

**Search Implementation:**
- Uses PostgreSQL full-text search with `tsvector` on `title` and `problem` columns
- Search is case-insensitive and supports partial word matching
- Results ranked by relevance score combined with opportunity score
- Debounce on frontend: 300ms delay before triggering API call
- Minimum 2 characters required to trigger search

**GET /api/v1/opportunities/:id**
- Purpose: Get single opportunity with full details including source links

**PATCH /api/v1/opportunities/:id**
- Purpose: Update opportunity status and user notes
- Body:
  - status (optional): 'new', 'researching', 'building', 'rejected'
  - user_notes (optional): Research notes text

#### Scan Endpoints

**POST /api/v1/scan**
- Purpose: Trigger new opportunity scan
- Response: Job ID for tracking scan progress

**GET /api/v1/scan/:job_id**
- Purpose: Check scan progress (pending/running/complete)

#### User Endpoints

**GET /api/v1/stats**
- Purpose: Summary statistics (total, validated, high score, avg score)

**GET /api/v1/user/profile**
- Purpose: Get current user's profile (email, subscription tier, created date)

**PATCH /api/v1/user/profile**
- Purpose: Update user profile
- Body: email (optional), current_password, new_password (optional)

**GET /api/v1/user/export-data**
- Purpose: GDPR data export - download all user data
- Access: Pro and Premium tiers only
- Returns: JSON file with all opportunities, notes, searches, exports

#### Email & Landing Page Endpoints

**POST /api/v1/email/configure-alerts**
- Purpose: Configure email alert settings
- Body: alert_threshold (int), weekly_digest (bool)

**POST /api/v1/landing-page/generate**
- Purpose: Generate validation landing page for opportunity
- Body: opportunity_id, custom_headline (optional), custom_cta (optional)
- Returns: landing_page_url, slug

#### Export Endpoints

**GET /api/v1/export/csv**
- Purpose: Export filtered opportunities to CSV
- Query Parameters: Same as GET /api/v1/opportunities

**GET /api/v1/export/pdf**
- Purpose: Generate PDF report of top opportunities
- Query Parameters: top_n (int, default: 10)

#### Health Endpoints

**GET /health**
- Purpose: Simple health check for load balancer
- Returns: `{"status": "healthy"}`

**GET /health/detailed**
- Purpose: Detailed health check for admin
- Returns: Database status, Redis status, collector status, last scan time

### 6.2 Admin API Endpoints

> Authentication: Requires JWT with role='admin'
> Access Control: All endpoints return 403 Forbidden if user is not admin

**GET /api/v1/admin/tiers** - List all subscription tiers

**POST /api/v1/admin/tiers** - Create new subscription tier
- Body: name, price_monthly, max_sources, scan_frequency, export_limit_monthly, landing_pages_allowed, email_alerts_allowed

**PATCH /api/v1/admin/tiers/:id** - Update existing tier (price, features, enabled status)

**GET /api/v1/admin/sources** - List all data sources with stats

**POST /api/v1/admin/sources** - Add new data source
- Body: name, type, config (JSON with API keys, keywords, etc.), rate_limit_per_minute

**PATCH /api/v1/admin/sources/:id** - Update source config or enable/disable

**POST /api/v1/admin/sources/:id/test** - Test source connection and return sample data

**GET /api/v1/admin/users** - List all users with subscription details
- Query Parameters: search (email), status (active/cancelled), page, limit

**PATCH /api/v1/admin/users/:id** - Update user (cancel subscription, change role to admin)

**GET /api/v1/admin/analytics** - System analytics (users, MRR, opportunities, engagement)

**PATCH /api/v1/admin/settings** - Update system settings
- Body: currency (GBP/USD), scoring_weights (JSON), default_scan_frequency, validation_rules (JSON)
- Note: Changing currency triggers Stripe Price creation and tier price updates

**GET /api/v1/admin/trial-settings** - Get current free trial configuration

**PATCH /api/v1/admin/trial-settings** - Configure free trial settings
- Body: enabled (bool), duration_days (int), trial_tier_id (UUID), max_sources (int), max_exports (int), landing_pages_allowed (bool), email_alerts_allowed (bool), min_opportunity_rank (int), require_card (bool), convert_to_tier_id (UUID)

**GET /api/v1/admin/audit-logs** - View admin action audit trail
- Query Parameters: action_type, admin_id, start_date, end_date, limit, cursor
- Returns: Paginated list of admin actions with timestamps and details

#### Audit Logging

All admin actions are automatically logged for compliance and debugging:

| Action Type | Logged Data |
|-------------|-------------|
| tier_created | tier_id, name, price, admin_id, timestamp |
| tier_updated | tier_id, changed_fields, old_values, new_values, admin_id |
| user_updated | user_id, changed_fields, admin_id, timestamp |
| source_updated | source_id, changed_fields, admin_id, timestamp |
| settings_changed | setting_key, old_value, new_value, admin_id |

Audit logs retained for 1 year minimum.

### 6.3 Frontend Features

#### Authentication & Profile
- Registration form with email verification
- Login form
- "Forgot password" link → Email reset link
- Password reset page (token-based)
- User profile page:
  - Change email
  - Change password
  - View subscription details
  - Update payment method (Stripe portal)
  - Export data button (Pro/Premium only)

#### Dashboard View
- 4 stat cards: Total, Validated, High Score, Average
- Search bar with real-time filtering
- Sort dropdown (score/revenue/mentions)
- Filter toggle with min score slider

#### Opportunity Cards
- Score badge (color-coded by range)
- Title and problem statement
- Revenue, mentions, competition, complexity
- Recommendation text

#### Detail Modal
- Full opportunity breakdown
- Source links (clickable)
- Market size estimate
- Existing competitor examples with direct links
- Action buttons (Mark as Researching/Building/Rejected)

#### Time-Based Filtering
- **Default View:** "Top Opportunities" - All time opportunities sorted by score (highest first)
- **Purpose of Time Filters:** When you need more context or saw something that's no longer on main page
- **Filter options:** Last 3 days, Last week, Last month, All time
- "Last 3 days" shows recent discoveries if something dropped off top page
- Time filters complement score sorting, don't replace it

#### Historical Archive
- All opportunities permanently stored (never deleted)
- Track mentions over time (trending up/down indicators)
- See when opportunity was first discovered
- Research notes and status tracking per opportunity

#### Email Alerts
- Automatic email when opportunity scores 80+ found
- Weekly digest of top 5 opportunities
- Configurable alert threshold in settings

#### Landing Page Builder
Quick validation tool: Generate a "Coming Soon - Join Waitlist" page for any opportunity to test demand before building.
- One-click landing page generation from opportunity data
- Customizable headline, description, and CTA
- Email capture form with Mailchimp/ConvertKit integration
- Hosted on subdomain (validate.opportunityfinder.app/[slug])

#### Export Functionality
- Export filtered opportunities to CSV
- Generate PDF report with top opportunities
- Share link for specific opportunity

### 6.4 Frontend Page Structure

#### Dashboard/List Page

**URL Pattern:** `/dashboard` or `/browse`

**Layout Components:**
- Navigation header (logo, menu items)
- Filter bar (sort, filters, search)
- Opportunity grid/list of cards
- Pagination controls

**Card Structure:**
- Opportunity image/hero (optional)
- Title (clickable, links to detail modal)
- Badges/scores (Opportunity, Problem, Feasibility, Why Now)
- Brief description (2-3 sentences)
- Key metrics row (Volume, Growth, Competition level)
- Action buttons: View Report, Save, Building

**Data Displayed per Opportunity:**

| Metric | Example |
|---------|---------|
| Opportunity Score | 7/10 with color indicator |
| Problem Severity | High Pain to Low Pain 1-10 |
| Feasibility | Manageable to Very Hard 1-10 |
| Why Now | Perfect Timing to Poor Timing 1-10 |
| Volume | Search volume (e.g., "2.9K", "4.4K") |
| Growth | YoY percentage (e.g., "+303%") |
| Competition | LOW/MEDIUM/HIGH |

**Interactions:**
- Hover card shows expanded preview
- Click opportunity → detail modal
- Filter sidebar updates list in real-time
- Sort dropdown changes order

#### Opportunity Detail Modal/Page

**Layout Components:**
- Back to list link
- Large title with opportunity title
- Opportunity Score badge (large, prominent)

**Page Sections:**

**Header Section:**
- Four-score breakdown row:
  - Opportunity: X/10
  - Problem: X/10
  - Feasibility: X/10
  - Why Now: X/10
- Action buttons: Save, Building, Researching, Rejected

**Validation Evidence Section:**
- "Proof & Signals" heading
- List of proof sources with indicators:
  - Community: Reddit X/10, Facebook X/10, YouTube X/10
  - Market Data: Revenue proof, competitor examples, market size
  - Competitors section (competitor cards or list)
- "What's Missing?" analysis (market gap section)

**Content Sections:**
- "The Problem" section - emotional hook opening paragraph
- "The Solution" section - what the product does
- "Target Market" section - who pays and why
- "Pricing Model" section - pricing tiers and revenue potential

**Layout Pattern:**
- Full-width content container (max-width: 800-1200px)
- Left column (70%): All content sections
- Right column (30%): Proof & Signals + action buttons (sticky)

#### Public Landing Page

**URL Pattern:** `/` (root)

**Layout Components:**
- Hero section with value proposition
- Features list (3-4 key benefits)
- Social proof (user count, success stories)
- Email capture form (email field, submit button)
- CTA button: "Get Started"

**Hero Section:**
- Main headline: Product value proposition
- Subheadline: "Powered by Data, Not Guessing"
- Email capture form
- CTA button (prominent)

**Features Section:**
- 3-4 benefit cards (each with icon, title, bullet points)

**Social Proof Section:**
- Success stories with testimonials
- Member/idea count badge

### 6.5 Frontend Component Specifications

#### OpportunityCard Component

```typescript
interface OpportunityCardProps {
  title: string;
  score: number;
  problemScore: number;
  feasibilityScore: number;
  whyNowScore: number;
  volume: string;           // "2.9K"
  growth: string;           // "+303%"
  competitionLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  description: string;
  actions: string[];        // ['view-report', 'save', 'building']
}
```

#### ActionButton Component

```typescript
interface ActionButtonProps {
  type: 'view-report' | 'save' | 'interested' | 'not-interested' | 'building' | 'researching' | 'rejected';
  icon?: string;
  label: string;
  onClick?: () => void;
}
```

#### Badge Component

```typescript
interface BadgeProps {
  type: 'opportunity' | 'problem' | 'feasibility' | 'why-now';
  score: number;
  label?: string;
}
```

#### Filter State

```typescript
interface Filters {
  sortBy: 'newest' | 'score-desc' | 'score-asc' | 'oldest';
  minScore?: number;
  maxScore?: number;
  validatedOnly?: boolean;
  status?: 'new' | 'researching' | 'building' | 'rejected';
  timeRange?: '3days' | '1week' | '1month' | 'all';
}
```

#### Opportunity List State

```typescript
interface OpportunityListState {
  opportunities: Opportunity[];
  loading: boolean;
  filters: Filters;
  pagination: {
    hasMore: boolean;
    nextCursor: string | null;
    totalCount: number;
  };
  error: string | null;
}
```

#### Loading State Component

```typescript
interface LoadingStateProps {
  message?: string;
  showProgress?: boolean;
  progress?: number;
}
```

### 6.6 UI Pages - Complete List

> **Important:** `docs/PRD/opportunity-finder.html` is a theme template showing visual style (colors, gradients, card design). It is NOT a complete set of pages. All pages below must be implemented.

**Required Pages for MVP (Phase 1):**

| Page | Description | Key Elements |
|-------|-------------|--------------|
| **Public Landing Page** | Product overview for visitors | Explains value prop, features, pricing tiers, CTA to register |
| **Register** | New user signup | Email field, password field, password confirm, submit button |
| **Login** | Existing user access | Email field, password field, "forgot password" link, submit button |
| **Email Verification** | Verify email address | Auto-redirected from email link, shows "Email verified, redirecting to login..." |
| **Forgot Password** | Request password reset | Email field, submit button, sends email with reset link |
| **Reset Password** | Set new password | New password field, confirm field, token (from URL), submit button |
| **Dashboard** | Main opportunity view | Stat cards, filter controls, opportunity cards, scan progress indicator |
| **Scan Progress** | Scan running state | Progress bar, estimated time, "Scanning..." message, sources being processed |
| **Opportunity Detail Modal** | Full opportunity information | All fields, source links, competitor links, status buttons |
| **User Profile** | Account management | Current email, change email, change password, subscription details, payment method update |
| **Settings** | User preferences | Email alert configuration, notification preferences, theme toggle (dark/light) |
| **Admin Panel - Login** | Separate admin access | Admin login page (different URL or `/admin` route) |
| **Admin Panel - Pricing** | Tier management | Tier list, create/edit form, enable/disable toggles, feature gates |
| **Admin Panel - Data Sources** | Source management | Source list, add/edit form, API key inputs, test button, enable/disable |
| **Admin Panel - Users** | User management | User table, search/filter, view details, cancel subscription, grant admin access |
| **Admin Panel - Scoring Criteria** | Algorithm settings | Weights adjustment, threshold settings, validation rules |
| **Admin Panel - Scan Settings** | Scan configuration | Frequency selector, manual "Scan Now" button, view scan history |
| **Admin Panel - Email Settings** | Email configuration | SendGrid/Mailgun API keys, alert frequency per tier, email templates |
| **Admin Panel - Analytics** | System metrics | Dashboard with charts/graphs, user counts, MRR tracking, error logs |

> **Note:** All admin pages require role='admin' authentication.

---

## 7. ADMIN PANEL

> **CRITICAL:** Admin panel is core MVP. Without it, you cannot manage pricing, tiers, or data sources.
>
> **Access:** Separate admin authentication. Admin users have role='admin' in database.

### 7.1 Pricing Management
- View all subscription plans
- Create new pricing tier (name, price, features)
- Edit existing tier price and features
- Enable/disable tiers
- Set feature gates per tier (sources allowed, scan frequency, export limits)

### 7.2 User Management
- View all users (email, subscription tier, status, created date)
- Search/filter users
- View user's subscription details
- Cancel user subscription
- Grant/revoke admin access
- **God-mode:** Impersonate user (view system as that user)

### 7.3 Data Source Management
- View all configured data sources
- Add new source (name, type, API credentials, search config)
- Edit source configuration (keywords, rate limits, enabled subreddits)
- Enable/disable source
- Test source connection
- View source statistics (requests made, opportunities found)

### 7.4 System Settings
- System currency selection (£ GBP or $ USD) - **Applies to entire system, admin chooses. Not per-user selection.**
- Scoring algorithm weights (demand, revenue, competition, complexity) - **Fully adjustable by admin**
- Default scan frequency (daily/weekly/custom) - **Admin-configured schedule**
- Email alert thresholds per tier
- Validation rules (minimum mentions, minimum revenue) - **Admin-configured**
- API rate limit configuration
- Landing page templates management (headline templates, CTA templates) - **Admin-managed**
- Email service configuration (SendGrid/Mailgun API keys, sender email) - **Admin-managed**

> **Deferred to Phase 2:** Multi-currency per-user selection, automated currency conversion, Stripe Price management for multiple currencies. Phase 1: Admin selects GBP or USD for entire system, no per-user currency choice.

### 7.5 Free Trial Configuration

> **DEFERRED TO PHASE 2 (Multi-User SaaS):** Trial flow will be designed and implemented based on Phase 1 outcomes and production requirements. Phase 1 uses single-user model without trials.

**For Future Reference (Phase 2 Planning):**

- **Enabled/Disabled:** Toggle free trials on/off globally
- **Duration:** Input field - any number of days (1, 5, 7, 14, 30, 60, etc.)
- **Trial Tier:** Which subscription tier during trial (Basic/Pro/Premium)
- **Feature Overrides:** Custom restrictions during trial
- **Require Credit Card:** Collect payment method upfront (yes/no)
- **Auto-Convert To:** Which paid tier after trial ends

### 7.6 Analytics Dashboard
- Total users, active subscriptions, MRR
- Opportunities discovered (total, by source)
- User engagement (searches, exports, landing pages created)
- System health (API errors, scan failures)

### 7.7 God-Mode Admin Requirements

- Full system override capability
- User impersonation (view/edit as any user)
- Tier/source/config manipulation without restrictions
- Emergency scan triggers and manual overrides
- Complete audit trail with full snapshot before/after states

---

## 8. SUBSCRIPTION TIERS & PACKAGES

> **CRITICAL:** Pricing is dynamic. Admin can create/modify tiers at any time without code changes.

The system supports multiple subscription tiers with different feature gates. Initial tiers are suggestions - admin can adjust pricing and features based on market response.

### 8.1 Suggested Initial Tiers

#### Basic Tier - £5/month
- 3 data sources (Reddit, Indie Hackers, ProductHunt)
- Weekly scans
- 5 exports per month
- Email alerts disabled
- Landing pages disabled
- Access to opportunities ranked 11+ only

#### Pro Tier - £15/month
- All 6 core data sources
- Daily scans
- Unlimited exports
- Email alerts enabled
- 5 landing pages per month
- Access to opportunities ranked 6+ (includes mid-tier)

#### Premium Tier - £30/month
- All data sources + admin can add more
- Daily scans + on-demand scans
- Unlimited exports
- Priority email alerts (instant for 90+ scores)
- Unlimited landing pages
- Access to ALL opportunities including top 5 ranked (highest quality)

### 8.2 Feature Gates

All features are gated by subscription tier. Frontend checks user's tier and disables features accordingly. Backend enforces limits.

**Opportunity Ranking Access:**
- Opportunities are ranked 1-N based on score (1=highest, N=lowest)
- Ranking recalculated after each scan
- Basic tier: Can only view opportunities ranked 11+ (lower quality)
- Pro tier: Can view opportunities ranked 6+ (includes mid-tier)
- Premium tier: Can view ALL opportunities including top 5 (highest quality)

**Example Enforcement:**
- User on Basic tries to export for 6th time this month → API returns 403 with "Upgrade to Pro for unlimited exports"
- User on Pro clicks 'Create Landing Page' → Works (allowed 5/month)
- User on Basic sees only 3 sources in UI, other sources greyed out with lock icon
- User on Basic sees opportunities ranked #11, #12, #13... but top 10 show as "Premium Only" with upgrade prompt

### 8.3 Upgrade/Downgrade Flow

1. User clicks 'Upgrade' on any tier
2. Redirects to Stripe checkout with new price
3. Stripe handles proration automatically
4. Webhook updates user.subscription_tier_id
5. New features immediately available

### 8.4 Multi-Currency Support

> **DEFERRED TO PHASE 2:** Per-user multi-currency support, automatic currency conversion, and Stripe Price management for multiple currencies will be designed and implemented based on Phase 2 requirements.

**Phase 1 Scope (Current Document):**
- System currency is global (set by admin, applies to all users)
- Admin selects either £ GBP or $ USD for entire system
- Single currency at any time
- Price displays use configured currency symbol (£ or $)

### 8.5 Failed Payment Handling (Dunning)

**Problem:** Credit cards decline for expired cards, insufficient funds, bank fraud alerts, etc.

**Solution:** Automated retry logic with email notifications to recover failed payments.

**Retry Schedule:**

| Day | Action |
|-----|--------|
| Day 0 | Payment fails → User.subscription_status = 'past_due' |
| Day 1 | Automatic retry + email "Payment failed - please update card" |
| Day 3 | Second retry + email "Final notice - update card within 4 days" |
| Day 7 | Third retry + email "Subscription will be cancelled tomorrow" |
| Day 8 | Cancel subscription → User.subscription_status = 'cancelled' |

**User Experience During Past Due:**
- Login shows banner: "Payment failed. Update card to continue service."
- Full access continues for 7 days (grace period)
- User can update card in profile → triggers immediate retry
- After 8 days: Access revoked, downgraded to no access until payment succeeds

**Stripe Webhooks:**
- `invoice.payment_failed` → Set status to past_due, send first email
- `invoice.payment_succeeded` → Set status to active, restore full access
- `customer.subscription.deleted` → Set status to cancelled, revoke access

#### Webhook Retry Logic

Stripe retries failed webhooks automatically, but your endpoint must handle duplicates:

**Idempotency:**
- Store `event.id` in `webhook_events` table on successful processing
- Before processing, check if `event.id` already exists → skip if duplicate
- Return 200 OK even for duplicates (prevents Stripe from retrying)

**Failure Handling:**

| Scenario | Response | Stripe Behavior |
|----------|----------|-----------------|
| Success | 200 OK | No retry |
| Temporary failure (DB down) | 500 Error | Retry up to 3 days |
| Invalid signature | 400 Bad Request | No retry |
| Duplicate event | 200 OK | No retry |

**Alert:** If webhook processing fails 3+ times in 1 hour, send alert to admin email.

---

## 9. DATABASE SCHEMA

> **CRITICAL:** Multi-tenant architecture from day 1. All user-specific data includes user_id foreign key.

### 9.1 users Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PRIMARY KEY | User unique identifier |
| email | VARCHAR(255) UNIQUE | Login email |
| email_verified | BOOLEAN | Email confirmed via verification link |
| password_hash | VARCHAR(255) | Bcrypt hashed password |
| role | VARCHAR(50) | user/admin |
| stripe_customer_id | VARCHAR(255) | Stripe customer ID |
| subscription_tier_id | UUID REFERENCES tiers(id) | Current subscription tier |
| subscription_status | VARCHAR(50) | trial/active/cancelled/past_due |
| subscription_end_date | TIMESTAMP | When subscription expires |
| trial_ends_at | TIMESTAMP | When free trial ends (null if not on trial) |
| created_at | TIMESTAMP | Account creation date |
| last_login | TIMESTAMP | Last login time |

**Indexes:**
```sql
CREATE UNIQUE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_stripe_customer ON users(stripe_customer_id);
CREATE INDEX idx_users_subscription_status ON users(subscription_status);
```

### 9.2 subscription_tiers Table

Purpose: Define pricing tiers and feature gates. Admin can create/modify tiers dynamically.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PRIMARY KEY | Tier unique identifier |
| name | VARCHAR(100) | Tier name (e.g., Basic, Pro, Premium) |
| price_monthly | INTEGER | Price in pence (e.g., 500 = £5.00) |
| stripe_price_id | VARCHAR(255) | Stripe Price ID |
| max_sources | INTEGER | Number of data sources allowed |
| min_opportunity_rank | INTEGER | Minimum rank to view (1=top, 11+=low) |
| scan_frequency | VARCHAR(50) | daily/weekly/monthly |
| export_limit_monthly | INTEGER | Max exports per month (-1 = unlimited) |
| landing_pages_allowed | BOOLEAN | Can create landing pages |
| email_alerts_allowed | BOOLEAN | Receives email alerts |
| enabled | BOOLEAN | Tier available for signup |
| created_at | TIMESTAMP | When tier created |
| updated_at | TIMESTAMP | Last modified |

### 9.3 data_sources Table

Purpose: Dynamic data source configuration. Admin can add new sources without code changes.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PRIMARY KEY | Source unique identifier |
| name | VARCHAR(100) | Display name (e.g., Reddit, Twitter) |
| type | VARCHAR(50) | reddit/api/scraper/rss |
| config | JSONB | Source-specific config (API keys, keywords, etc.) |
| enabled | BOOLEAN | Currently active |
| rate_limit_per_minute | INTEGER | Max requests per minute |
| last_scan | TIMESTAMP | Last successful scan |
| total_opportunities_found | INTEGER | Lifetime count |
| created_at | TIMESTAMP | When added |
| updated_at | TIMESTAMP | Last modified |

### 9.4 opportunities Table

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Auto-incrementing ID |
| user_id | UUID REFERENCES users(id) | Owner of this opportunity record |
| title | VARCHAR(255) | Opportunity title |
| problem | TEXT | Problem statement |
| score | INTEGER | Calculated score (0-100) |
| rank | INTEGER | Ranking position (1=best, updated on each scan) |
| mentions | INTEGER | Total mentions across sources |
| mentions_trend | VARCHAR(20) | up/down/stable |
| revenue | VARCHAR(100) | Display string (e.g. "£5k MRR") |
| revenue_amount | INTEGER | Numeric amount for sorting |
| competitors | INTEGER | Number of competitors |
| competition_level | VARCHAR(50) | Low/Medium/High/Very High |
| build_complexity | VARCHAR(50) | Low/Medium/High |
| sources | JSONB | Array of source names |
| source_urls | JSONB | Array of source URLs |
| example | TEXT | Existing competitor examples |
| competitor_urls | JSONB | Array of competitor URLs |
| validated | BOOLEAN | Passed validation criteria |
| recommendation | TEXT | Action recommendation |
| market_size | TEXT | Market size description |
| status | VARCHAR(50) | new/researching/building/rejected |
| user_notes | TEXT | User research notes |
| problem_score | INTEGER | Problem severity score (1-10) |
| feasibility_score | INTEGER | Feasibility score (1-10) |
| timing_score | INTEGER | Why Now / Timing score (1-10) |
| keyword_volume | VARCHAR(50) | Search volume (e.g., "2.9K") |
| keyword_growth | VARCHAR(50) | YoY growth (e.g., "+303%") |
| keyword_competition | VARCHAR(20) | LOW/MEDIUM/HIGH |
| created_at | TIMESTAMP | When first discovered |
| updated_at | TIMESTAMP | Last updated |
| last_seen | TIMESTAMP | Last time mentioned in sources |

**Indexes:**
```sql
-- Primary query: user's opportunities sorted by score
CREATE INDEX idx_opportunities_user_score ON opportunities(user_id, score DESC);

-- Filtering by status
CREATE INDEX idx_opportunities_user_status ON opportunities(user_id, status);

-- Time-based filtering
CREATE INDEX idx_opportunities_user_created ON opportunities(user_id, created_at DESC);

-- Full-text search
CREATE INDEX idx_opportunities_search ON opportunities
  USING GIN(to_tsvector('english', title || ' ' || problem));

-- Ranking queries
CREATE INDEX idx_opportunities_user_rank ON opportunities(user_id, rank);
```

### 9.5 pain_points Table

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Auto-incrementing ID |
| user_id | UUID REFERENCES users(id) | User who discovered this |
| source | VARCHAR(100) | Source platform (e.g. r/Entrepreneur) |
| text | TEXT | Pain point text |
| url | TEXT | Source URL |
| mentions | INTEGER | Frequency count |
| created_at | TIMESTAMP | When collected |

**Indexes:**
```sql
CREATE INDEX idx_pain_points_user ON pain_points(user_id);
CREATE INDEX idx_pain_points_source ON pain_points(source);
```

### 9.6 scan_jobs Table

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PRIMARY KEY | Job ID |
| user_id | UUID REFERENCES users(id) | User who initiated scan |
| status | VARCHAR(50) | pending/running/complete/failed |
| progress_percentage | INTEGER | 0-100 progress indicator |
| sources_completed | JSONB | Array of completed source names |
| started_at | TIMESTAMP | Start time |
| completed_at | TIMESTAMP | Completion time |
| opportunities_found | INTEGER | Number found |
| error_message | TEXT | Error if failed |

**Indexes:**
```sql
CREATE INDEX idx_scan_jobs_user ON scan_jobs(user_id);
CREATE INDEX idx_scan_jobs_status ON scan_jobs(status);
CREATE INDEX idx_scan_jobs_user_started ON scan_jobs(user_id, started_at DESC);
```

### 9.7 system_settings Table

Purpose: Global system configuration. Single-row table (id=1).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Always 1 (singleton) |
| currency | VARCHAR(3) | GBP or USD |
| currency_symbol | VARCHAR(5) | £ or $ |
| scoring_weights | JSONB | Algorithm weights {demand:25, revenue:35...} |
| default_scan_frequency | VARCHAR(50) | daily/weekly |
| validation_rules | JSONB | Min mentions, min revenue thresholds |
| updated_at | TIMESTAMP | Last modified |
| updated_by | UUID REFERENCES users(id) | Admin who made change |

### 9.8 trial_settings Table

Purpose: Free trial configuration. Single-row table (id=1).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Always 1 (singleton) |
| enabled | BOOLEAN | Free trials enabled/disabled |
| duration_days | INTEGER | Trial length in days |
| trial_tier_id | UUID REFERENCES tiers(id) | Which tier during trial |
| max_sources | INTEGER | Source limit override (null = use tier) |
| max_exports | INTEGER | Export limit override (null = use tier) |
| landing_pages_allowed | BOOLEAN | Landing page access override |
| email_alerts_allowed | BOOLEAN | Email alert override |
| min_opportunity_rank | INTEGER | Rank access override (null = use tier) |
| require_card | BOOLEAN | Require payment method upfront |
| convert_to_tier_id | UUID REFERENCES tiers(id) | Tier after trial ends |
| updated_at | TIMESTAMP | Last modified |
| updated_by | UUID REFERENCES users(id) | Admin who made change |

### 9.9 audit_logs Table

Purpose: Track all admin actions for compliance and debugging.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PRIMARY KEY | Log entry ID |
| admin_id | UUID REFERENCES users(id) | Admin who performed action |
| action_type | VARCHAR(100) | tier_created, user_updated, etc. |
| target_type | VARCHAR(50) | user, tier, source, settings |
| target_id | VARCHAR(255) | ID of affected record |
| old_values | JSONB | Previous values (null for create) |
| new_values | JSONB | New values (null for delete) |
| ip_address | VARCHAR(45) | Admin's IP address |
| created_at | TIMESTAMP | When action occurred |

**Indexes:**
```sql
CREATE INDEX idx_audit_logs_admin ON audit_logs(admin_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action_type);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_target ON audit_logs(target_type, target_id);
```

### 9.10 webhook_events Table

Purpose: Track processed Stripe webhooks for idempotency.

| Column | Type | Description |
|--------|------|-------------|
| id | VARCHAR(255) PRIMARY KEY | Stripe event ID (evt_xxx) |
| event_type | VARCHAR(100) | invoice.payment_failed, etc. |
| processed_at | TIMESTAMP | When successfully processed |
| payload | JSONB | Full event payload for debugging |

**Indexes:**
```sql
CREATE INDEX idx_webhook_events_type ON webhook_events(event_type);
CREATE INDEX idx_webhook_events_processed ON webhook_events(processed_at DESC);
```

---

## 10. IMPLEMENTATION PATTERNS & CONSISTENCY RULES

> **CRITICAL:** All AI agents and developers MUST follow these patterns to ensure consistent, compatible code across the codebase.

### 10.1 Naming Conventions

#### Database Naming (SQL/Python)

| Element | Convention | Example |
|---------|-----------|---------|
| **Tables** | `snake_case`, plural | `users`, `subscription_tiers`, `opportunities` |
| **Columns** | `snake_case` | `user_id`, `stripe_price_id`, `created_at` |
| **Indexes** | `idx_table_column1_column2` | `idx_opportunities_user_score`, `idx_pain_points_source` |
| **Foreign Keys** | `{table}_id` format | `user_id REFERENCES users(id)` |

#### API Naming (REST)

| Element | Convention | Example |
|---------|-----------|---------|
| **Endpoints** | `kebab-case`, plural, `/api/v1/` prefix | `/api/v1/opportunities`, `/api/v1/auth/login` |
| **Route Parameters** | `snake_case` | `?user_id=xxx&filter=score_desc` |
| **Headers** | `Kebab-Case` with hyphens | `X-Request-ID`, `Content-Type`, `Authorization` |

#### Code Naming (Python)

| Element | Convention | Example |
|---------|-----------|---------|
| **Variables** | `snake_case` | `user_id`, `total_count`, `next_cursor` |
| **Functions** | `snake_case` | `get_opportunities()`, `validate_opportunity()` |
| **Classes** | `PascalCase` | `OpportunityService`, `UserRepository` |
| **Constants** | `UPPER_SNAKE_CASE` | `MAX_SCAN_INTERVAL`, `DEFAULT_LIMIT` |

#### Code Naming (TypeScript/React)

| Element | Convention | Example |
|---------|-----------|---------|
| **Variables** | `camelCase` | `userId`, `totalCount`, `nextCursor` |
| **Functions** | `camelCase` | `getOpportunities()`, `validateOpportunity()` |
| **Components** | `PascalCase` | `OpportunityCard`, `UserList` |
| **Constants** | `UPPER_SNAKE_CASE` | `MAX_SCAN_INTERVAL`, `DEFAULT_LIMIT` |

#### File & Directory Naming

| Element | Convention | Example |
|---------|-----------|---------|
| **Directories** | `kebab-case` | `frontend/`, `backend/`, `shared/` |
| **Python files** | `snake_case.py` | `opportunity_service.py`, `data_collector.py` |
| **TypeScript files** | `PascalCase.tsx` | `OpportunityCard.tsx`, `UserProfile.tsx` |
| **Test files** | `test_*.py` or `*.test.tsx` | `test_opportunity_service.py`, `Dashboard.test.tsx` |

### 10.2 API Response Formats

#### Standard API Response Wrapper

```typescript
interface ApiResponse<T> {
  data: T | null;
  error: ApiError | null;
}

interface ApiError {
  message: string;
  code: string;
  details?: any;
}
```

**Usage:**
- Success: `{ data: {...}, error: null }`
- Error: `{ data: null, error: { message: "error", code: "VALIDATION_ERROR" } }`
- Validation: `{ data: null, error: { message: "validation error", code: "INVALID_INPUT", details: ["field1", "field2"] } }`

#### Error Response Codes

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `SUCCESS` | 200 | Request succeeded |
| `UNAUTHORIZED` | 401 | Invalid or expired token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid input data |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

#### Date/Time Formats

| Format | Example | Usage |
|---------|---------|-------|
| **JSON ISO8601** | `2026-01-14T16:30:00.000Z` | API responses |
| **Database timestamp** | PostgreSQL TIMESTAMP | Database storage |
| **Display format** | `2026-01-14 4:30 PM` | UI display |

### 10.3 Error Handling Patterns

#### Global Error Handling Pattern

```python
# Flask error handler
@app.errorhandler(Exception)
def handle_error(e):
    logger.error(f"{request_id} - {str(e)}", extra={"user_id": user_id})
    return jsonify({"data": None, "error": {"message": str(e), "code": "INTERNAL_ERROR"}}), 500
```

#### Validation Error Pattern

```python
def validate_request(data):
    errors = []

    if not data.get("email"):
        errors.append("email_required")

    if errors:
        logger.info(f"{request_id} - validation failed", extra={"errors": errors})
        return jsonify({"data": None, "error": {"message": "validation failed", "code": "VALIDATION_ERROR", "details": errors}}), 400

    return None
```

#### HTTP Status Code Usage

| Status | When to Use |
|---------|-------------|
| **401 Unauthorized** | Invalid/expired JWT token, wrong password |
| **403 Forbidden** | Insufficient tier access, God-mode access check failed |
| **404 Not Found** | Opportunity doesn't exist or was deleted |

### 10.4 Authentication Patterns

#### JWT Token Management

```python
# Access token: 15 minutes expiry
ACCESS_TOKEN_EXPIRY = 15 * 60  # seconds

# Refresh token: 7 days expiry
REFRESH_TOKEN_EXPIRY = 7 * 24 * 60 * 60  # seconds

def generate_tokens(user_id):
    access_token = create_jwt_token(user_id, ACCESS_TOKEN_EXPIRY)
    refresh_token = create_jwt_token(user_id, REFRESH_TOKEN_EXPIRY)

    # Store refresh token in Redis with user_id mapping
    redis_client.set(f"refresh_token:{refresh_token}", user_id, ex=REFRESH_TOKEN_EXPIRY)
```

#### Password Handling

```python
import bcrypt

def hash_password(password):
    return bcrypt.generate_password_hash(password)

def verify_password(password, hashed):
    return bcrypt.check_password_hash(password, hashed)
```

### 10.5 Database Patterns

#### Transaction Boundary Pattern

```python
from sqlalchemy import exc as sa_exc

def create_opportunity(opportunity_data):
    try:
        # All database operations in single transaction
        with db.session.begin():
            opportunity = Opportunity(**opportunity_data)
            db.session.add(opportunity)

            # Calculate score
            score = calculate_score(opportunity)
            opportunity.score = score

            # Validate
            validated = validate_opportunity(opportunity)
            opportunity.validated = validated

            db.session.commit()

    except sa_exc.SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"transaction failed: {e}", extra={"request_id": request_id})
        raise
```

#### Multi-Tenancy Enforcement Pattern

```python
@app.before_request
def enforce_user_context():
    user_id = get_user_id_from_token()
    g.user_id = user_id

    # Every query includes user_id filter
    # Prevents cross-tenant data access

def get_opportunities(user_id):
    return db.session.query(Opportunity).filter_by(user_id=user_id).all()
```

### 10.6 API Design Patterns

#### Cursor-Based Pagination

```python
def get_opportunities_paginated(user_id, cursor=None, limit=50):
    query = Opportunity.query.filter_by(user_id=user_id)

    if cursor:
        query = query.filter(Opportunity.id > cursor)

    opportunities = query.order_by(Opportunity.score.desc()).limit(limit).all()

    next_cursor = opportunities[-1].id if len(opportunities) == limit else None

    return {
        "data": opportunities,
        "pagination": {
            "has_more": len(opportunities) == limit,
            "next_cursor": next_cursor,
            "total_count": count_opportunities(user_id)
        }
    }
```

#### Rate Limiting Pattern

```python
from flask_limiter import Limiter

limiter = Limiter(
    get_remote_address=get_remote_address,
    default_limits=["200 per day"],
    key_func=lambda: f"user_{get_user_id_from_token()}"
)

@app.route("/api/v1/scan", methods=["POST"])
@limiter.limit("5 per hour")  # User-specific, not global
def trigger_scan(user_id):
    # Per-user rate limiting prevents DoS from single abusive user
```

### 10.7 Event & Communication Patterns

#### Event Naming Convention

| Event Type | Format | Example |
|-------------|---------|---------|
| **User Events** | `user.{action}` | `user.created`, `user.deleted`, `opportunity.saved` |
| **Scan Events** | `scan.{action}` | `scan.started`, `scan.completed`, `scan.failed` |
| **Admin Events** | `admin.{action}` | `admin.tier_changed`, `admin.source_modified` |
| **Payment Events** | `payment.{action}` | `payment.succeeded`, `payment.failed`, `subscription.updated` |

#### Event Payload Structure

```json
{
  "event_type": "scan.started",
  "timestamp": "2026-01-14T16:30:00.000Z",
  "request_id": "req_123456",
  "user_id": "user_abc123",
  "data": {
    "scan_type": "daily",
    "sources": ["reddit", "ih", "ph"]
  }
}
```

### 10.8 State Management Patterns

#### Loading States

| State | Usage |
|--------|--------|
| `LOADING_INITIAL` | Initial page/component load |
| `LOADING_DATA` | Fetching from API |
| `LOADING_SAVING` | Saving to server |
| `ERROR` | Operation failed |
| `SUCCESS` | Operation completed |

#### Immutable State Updates

```typescript
// Never mutate existing state, always create new
setOpportunities(prev => [...prev, ...newOpportunity])

// Good
const [opportunities, setOpportunities] = useState<Opportunity[]>([])

// Bad
opportunities.push(...newOpportunity)
```

### 10.9 Testing Patterns

#### Test File Organization

```
backend/tests/
├── unit/                   # Isolated unit tests
│   ├── test_models.py
│   ├── test_scoring.py
│   └── test_auth_service.py
├── integration/            # Integration tests
│   ├── test_api.py
│   └── test_collectors.py
└── fixtures/               # Test data
    └── sample_opportunities.json
```

#### Test Naming

| Element | Convention | Example |
|---------|-----------|---------|
| **Test functions** | `test_` prefix | `test_get_opportunities()` |
| **Test classes** | `Test` prefix | `TestOpportunityService` |
| **Fixtures** | `fixtures_` prefix | `fixtures_opportunities.json` |

### 10.10 Enforcement Guidelines

**All AI Agents and Developers MUST Follow These Rules:**

1. **Naming:**
   - Use `snake_case` for all Python code (variables, functions)
   - Use `PascalCase` for Python classes
   - Use `camelCase` for all TypeScript/React code
   - Use `UPPER_SNAKE_CASE` for all constants
   - Table names: plural `snake_case`
   - Column names: singular `snake_case`
   - API endpoints: `kebab-case`, `/api/v1/` prefix

2. **Project Structure:**
   - Follow the structure defined in Section 11
   - Tests in `tests/` directory
   - Services in `services/` directory
   - Routes in `routes/` directory

3. **API Responses:**
   - Always use `{data: T | null, error: Error | null}` wrapper
   - Include `code` field for programmatic error handling
   - Include `details` array for validation errors
   - Use defined error codes: SUCCESS, UNAUTHORIZED, FORBIDDEN, NOT_FOUND, VALIDATION_ERROR, RATE_LIMITED, INTERNAL_ERROR

4. **Database:**
   - All write operations within transaction boundaries
   - Always include `user_id` filter in queries (multi-tenancy)
   - Use `commit()` or `rollback()` - never auto-commit

5. **Error Handling:**
   - Use `@app.errorhandler(Exception)` for global error handling
   - Validation errors return 400 with VALIDATION_ERROR
   - Unauthorized errors return 401
   - Forbidden errors return 403
   - Not found errors return 404
   - Internal errors return 500

6. **Testing:**
   - Unit tests in `tests/unit/`
   - Integration tests in `tests/integration/`
   - Fixtures in `tests/fixtures/`
   - Test naming: `test_` prefix for functions, `Test` prefix for classes

7. **Logging:**
   - JSON format logs with `timestamp`, `level`, `user_id`, `request_id`, `event_type`
   - User errors (400s) at INFO level
   - System errors (500s) at ERROR level
   - Always include request_id for correlation

---

## 11. PROJECT STRUCTURE

### 11.1 Root Directory Structure

```
opportunity-finder/
├── backend/                    # Flask application
│   ├── app.py                  # Flask app factory
│   ├── config.py               # Configuration management
│   ├── requirements.txt        # Python dependencies
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── opportunity.py
│   │   ├── subscription_tier.py
│   │   ├── data_source.py
│   │   ├── scan_job.py
│   │   ├── pain_point.py
│   │   ├── system_setting.py
│   │   ├── trial_setting.py
│   │   ├── audit_log.py
│   │   └── webhook_event.py
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── scoring_service.py
│   │   ├── data_collector_service.py
│   │   ├── stripe_service.py
│   │   ├── email_service.py
│   │   └── pdf_service.py
│   ├── routes/                 # API routes
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   ├── opportunity_routes.py
│   │   ├── admin_routes.py
│   │   ├── payment_routes.py
│   │   └── scan_routes.py
│   ├── collectors/             # Data source collectors
│   │   ├── __init__.py
│   │   ├── reddit_collector.py
│   │   ├── ih_collector.py
│   │   ├── ph_collector.py
│   │   ├── hn_collector.py
│   │   ├── google_collector.py
│   │   └── microns_collector.py
│   ├── utils/                  # Shared utilities
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── validation.py
│   │   └── constants.py
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_models.py
│   │   │   ├── test_scoring.py
│   │   │   ├── test_auth_service.py
│   │   │   └── test_data_collector_service.py
│   │   └── integration/
│   │       ├── test_api.py
│   │       ├── test_collectors.py
│   │       └── test_webhooks.py
│   └── fixtures/
│       └── sample_opportunities.json
│
├── frontend/                   # React + Vite application
│   ├── src/
│   │   ├── components/
│   │   │   ├── OpportunityCard.tsx
│   │   │   ├── OpportunityList.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── OpportunityModal.tsx
│   │   │   ├── AuthForm.tsx
│   │   │   ├── FilterPanel.tsx
│   │   │   └── admin/
│   │   │       ├── TierManager.tsx
│   │   │       ├── UserManager.tsx
│   │   │       ├── SourceManager.tsx
│   │   │       ├── ScoringCriteria.tsx
│   │   │       └── ScanControl.tsx
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── auth.ts
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useOpportunities.ts
│   │   ├── utils/
│   │   │   └── constants.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── vite-env.d.ts
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   └── tailwind.config.js
│
├── nginx.conf                  # Production nginx config
├── docker-compose.yml          # Local development
├── .env.example                # Environment variables template
├── .gitignore
└── README.md
```

### 11.2 Technology Stack Alignment

| Layer | Technology | Structure Location |
|--------|-----------|-------------------|
| Backend | Flask + SQLAlchemy | `backend/models/`, `backend/services/` |
| Frontend | React + Vite + TypeScript | `frontend/src/` |
| Database | PostgreSQL 15+ | PRD schema definitions |
| Cache | Redis 7.0+ | Session storage, Celery broker |
| Background Jobs | Celery 5.3+ | `backend/services/data_collector_service.py` |

### 11.3 Directory Purpose Summary

| Directory | Purpose |
|-----------|---------|
| `backend/models/` | SQLAlchemy ORM models matching PRD schema |
| `backend/services/` | Business logic layer for auth, scoring, data collection |
| `backend/routes/` | Flask blueprints for API endpoints |
| `backend/collectors/` | Data source collectors (Reddit, IH, PH, HN, Google, Microns) |
| `backend/utils/` | Shared utilities (auth helpers, validation functions) |
| `backend/tests/` | Unit and integration tests |
| `frontend/src/components/` | React components following naming conventions |
| `frontend/src/services/` | API communication layer |
| `frontend/src/hooks/` | Custom React hooks |
| `frontend/src/types/` | TypeScript type definitions |

---

## 12. COMPETITIVE ANALYSIS

The micro-SaaS validation space has several players, but most are static databases or manual services. Our competitive advantage is real-time automated scanning with systematic scoring.

### 12.1 Direct Competitors

#### BigIdeasDB
- **Pricing:** £39-79/month
- **Strengths:** Aggregates Reddit, G2, ProductHunt, app stores; AI-powered research assistant (BuildGuide); Millions of data points
- **Weaknesses:** No systematic scoring, no build complexity assessment, expensive for indie developers

#### MicroSaaSHQ
- **Pricing:** £130 one-time payment
- **Strengths:** 1,200+ pre-validated ideas; Market data and competition analysis; AI build prompts for Cursor/Lovable
- **Weaknesses:** Static database (not live scraping), no automated updates, no personalized discovery

#### Validator (ProductHunt Focus)
- **Pricing:** Unknown (new product)
- **Strengths:** Automated competitor analysis; Trend analysis
- **Weaknesses:** Only ProductHunt data, limited sources, newer player with less data

#### Ideabrowser
- **Pricing:** Starter $499/year, Pro $1,500/year, Empire $3,000/year
- **Strengths:** Detailed idea validation, market analysis, execution planning, multi-platform community signals tracking
- **Weaknesses:** Higher price point, not SaaS-specific (broader startup ideas), no continuous monitoring
- **Relevance:** Provides framework for evaluation methodology and scoring approach that can inform our algorithm design

### 12.2 Adjacent Competitors

#### ValidateMySaaS
- **Pricing:** £29-99 per report
- **Model:** Manual competitor analysis reports (24hr turnaround)
- **Weaknesses:** Manual process, slow, pay per validation, not continuous monitoring

#### Exploding Topics
- **Pricing:** £39-79/month
- **Focus:** Trend discovery, rising search terms
- **Weaknesses:** Not SaaS-specific, no validation framework, requires manual interpretation

### 12.3 Our Competitive Advantages

| Advantage | Description |
|-----------|-------------|
| Real-Time Automated Scanning | Not a static database - continuously monitors sources |
| Systematic Scoring Algorithm | Clear 0-100 scores with actionable recommendations, not just idea lists |
| Multi-Source Validation | 6+ data sources vs competitors' 1-3 |
| Developer-First | Includes tech stack, build complexity, not just market data |
| Historical Tracking | See trending data over time, not point-in-time snapshots |
| Revenue Validation | Won't show opportunities unless existing solutions make £1k+ MRR |
| Price Point | £5/month vs £39-130 - accessible to bootstrappers |

### 12.4 Market Positioning

**Position:** "The systematic validation engine for indie developers - not guessing, not static lists, but live market signals with clear build/no-build scores."

**Target:** Developers building their first micro-SaaS who want validation BEFORE building, not idea inspiration.

---

## 13. IMPLEMENTATION PLAN

### 13.1 Phase 1: Core Backend + Auth + Admin (Days 1-5)

- Set up Flask project structure
- Implement database models with multi-tenant architecture (SQLAlchemy)
- Build authentication system (JWT, bcrypt, register/login endpoints)
- Set up Stripe integration (checkout, webhooks)
- Build Reddit collector with PRAW
- Implement basic scoring algorithm
- Create API endpoints with auth middleware (GET /opportunities, GET /stats)

**Success Criteria:** Can register/login, pay via Stripe, collect Reddit data, score it, save to multi-tenant DB, serve via authenticated API

### 13.2 Phase 2: Data Sources + Tiers (Days 6-10)

- Indie Hackers scraper
- ProductHunt API integration
- HackerNews Algolia API
- Google Search via SerpAPI
- Microns.io / Acquire.com scraper

**Success Criteria:** All sources collecting data, aggregation working, scores accurate

### 13.3 Phase 3: Frontend + Admin Panel (Days 11-15)

- Set up React project (Vite)
- Build authentication pages (login, register, password reset)
- Implement Stripe checkout flow and billing portal
- Build dashboard layout with dark/light mode toggle
- Implement opportunity cards with filtering and time ranges
- Create detail modal with status tracking
- Connect to backend API with JWT auth

**Success Criteria:** Full auth flow works, users can pay and access app, UI connected to live backend, both themes functional, mobile responsive

### 13.4 Phase 4: Polish + Deploy (Days 16-21)

- Add loading states and error handling
- Implement background job system for scans
- Build email alert system (SendGrid/Mailgun integration)
- Create landing page builder with email capture
- Implement CSV/PDF export functionality
- Set up deployment (Nginx, Gunicorn, PostgreSQL)
- Configure automated weekly scans (cron)
- Testing and bug fixes

**Success Criteria:** Deployed to VPS, automated scans running, email alerts working, landing pages generating, exports functional, no critical bugs

---

## 14. ACCEPTANCE CRITERIA

### 14.1 Backend Requirements

- [ ] User authentication working (register, login, JWT tokens)
- [ ] Email verification flow working
- [ ] Password reset flow working
- [ ] Stripe integration functional (checkout, webhooks, subscription status updates)
- [ ] Multi-tenant data isolation (users only see their own opportunities)
- [ ] Collects data from all 6 sources (Reddit, IH, PH, HN, Google, Microns)
- [ ] Scores opportunities correctly (manual verification with 10 test cases)
- [ ] Stores data in PostgreSQL with proper foreign keys
- [ ] API returns JSON with correct schema
- [ ] Handles rate limits gracefully (no crashes)
- [ ] Weekly automated scans run via cron
- [ ] Health endpoints returning correct status

### 14.2 Frontend Requirements

- [ ] Registration flow with email verification works
- [ ] Login and logout functional
- [ ] Password reset flow works (forgot password → email → reset)
- [ ] User profile page works (change email, change password)
- [ ] Stripe checkout integration functional
- [ ] Free trial displays correctly (if enabled)
- [ ] Failed payment banner shows for past_due status
- [ ] Subscription status displayed correctly
- [ ] Displays all opportunities from API
- [ ] Default view shows top opportunities (sorted by score)
- [ ] Tier-based rank filtering works (Basic sees 11+, Pro sees 6+, Premium sees all)
- [ ] Search works in real-time
- [ ] Filters work (min score slider, time range, status)
- [ ] Sorting works (score/revenue/mentions)
- [ ] Detail modal shows all data with clickable source links
- [ ] Dark/light mode toggle works
- [ ] Status tracking (mark as researching/building/rejected)
- [ ] Email alerts configured and sending correctly
- [ ] Export to CSV/PDF functional
- [ ] Data export (GDPR) works for Pro/Premium users
- [ ] Landing page builder generates valid pages
- [ ] Responsive design (works on mobile)
- [ ] Loading states for API calls

### 14.3 Admin Panel Requirements

- [ ] Admin login working (separate from user login)
- [ ] Tier management (create, edit, enable/disable)
- [ ] User management (view, search, cancel subscription, grant admin)
- [ ] Data source management (add, edit, enable/disable, test connection)
- [ ] Scoring criteria adjustment working
- [ ] Scan settings configuration working
- [ ] Analytics dashboard showing correct metrics
- [ ] Audit logs being recorded for all admin actions
- [ ] God-mode user impersonation working

### 14.4 Deployment Requirements

- [ ] Runs on VPS (accessible via domain or IP)
- [ ] Also runs locally (development mode)
- [ ] Environment variables for API keys
- [ ] Database migrations work
- [ ] Setup documentation complete

### 14.5 Quality Criteria

- [ ] 80%+ of score 60+ opportunities validate with landing page
- [ ] System finds 10+ new opportunities per week
- [ ] No crashes during 7-day continuous operation
- [ ] API response time < 500ms for GET /opportunities

---

## 15. OUT OF SCOPE (MVP PHASE 1)

These features are explicitly NOT included in Phase 1 (Single-User MVP):

- Team/multi-user accounts (MVP is single-user for product owner)
- Saving favorites/bookmarks
- Advanced NLP/clustering for theme detection
- Competitor deep analysis (beyond basic URL listing)
- Custom data source configuration (data sources configured by admin, not users)
- Mobile apps (iOS/Android) - architecture supports future development
- Slack/Discord integrations
- Browser extension for pain point capture
- **Multi-currency per-user** - deferred to Phase 2
- **Free trial system** - deferred to Phase 2
- **User-facing landing page builder** - deferred to Phase 2 (product owner can use admin to create pages, not user-facing)

### 15.1 Post-Phase 1 / Phase 2 Features

> **DOCUMENTED FOR FUTURE DEVELOPMENT:** These features will be planned and implemented based on Phase 1 validation results and production model requirements.

#### Help / FAQ Section

**Purpose:** Self-service support to reduce admin workload (Phase 2 when external users added)

- Searchable FAQ database
- Categories: Getting Started, Pricing, Data Sources, Scoring, Exports, Billing
- Video tutorials (3-5 minute screencasts)
- Contact form for unanswered questions
- Admin can add/edit FAQ entries without code changes

#### User Onboarding Flow

**Purpose:** Guide new external users to first value (seeing validated opportunities) in under 5 minutes (Phase 2)

1. Account created → Show welcome modal
2. "Let's run your first scan" → Click button, show progress
3. Results appear → Highlight top opportunity with tooltip
4. Click opportunity → Modal shows "This is how opportunities work"
5. "Try filtering by score" → Highlight filter controls
6. Done → "You're ready! Explore on your own or upgrade for more features"

**Implementation:**
- Use library like Shepherd.js or Intro.js for step-by-step tooltips
- User.onboarding_completed flag tracks progress
- "Skip tutorial" option available at any step

---

## 16. ENVIRONMENT & SETUP

### 16.1 Required API Keys

| Service | Keys Needed | URL |
|---------|-------------|-----|
| Reddit | client_id, client_secret | https://www.reddit.com/prefs/apps |
| ProductHunt | API token | https://api.producthunt.com/v2/docs |
| SerpAPI | API key | https://serpapi.com |
| Stripe | Secret key, Publishable key, Webhook secret | https://stripe.com |
| SendGrid/Mailgun | API key | https://sendgrid.com or https://mailgun.com |

### 16.2 Development Environment

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7.0+
- Git

### 16.3 Account Status Checklist

- [ ] Stripe account created and verified
- [ ] SendGrid/Mailgun API key obtained
- [ ] Reddit app created (client ID/secret)
- [ ] ProductHunt API token obtained
- [ ] SerpAPI key obtained (100 free searches)
- [ ] VPS provisioned (2GB+ RAM, Ubuntu 24)
- [ ] Domain purchased and DNS configured

---

## 17. RISKS & MITIGATION

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| API rate limits block collection | High | Medium | Exponential backoff + caching |
| Scoring algorithm inaccurate | Medium | High | Manual validation of 50 test cases |
| Web scraping breaks | Medium | Medium | Monitor errors, fallback to APIs |
| Low data quality | Medium | High | Multiple source validation |
| Performance issues at scale | Low | Medium | Database indexing + pagination |

---

## 18. SUCCESS METRICS

### 18.1 Product Metrics

| Metric | Target |
|--------|--------|
| Validation Accuracy | 80%+ of score 60+ opportunities validate with landing page test |
| Discovery Rate | 10+ validated opportunities discovered per week |
| System Uptime | 99%+ uptime over 30 days |
| Data Freshness | All data sources updated within 7 days |

### 18.2 User Metrics (If Offered as SaaS)

| Metric | Target |
|--------|--------|
| Time to First Value | < 5 minutes from signup to viewing opportunities |
| Weekly Active Users | Track returning users |
| Conversion Rate | Users who validate an opportunity |

---

## 19. ERROR STATES & USER EXPERIENCE

### 19.1 Loading States

| Component | Loading Behavior |
|-----------|------------------|
| Dashboard | Skeleton cards (8 placeholders) with pulse animation |
| Opportunity List | Skeleton rows matching card layout |
| Detail Modal | Spinner centered in modal body |
| Scan Trigger | Button disabled + "Scanning..." text + progress indicator |
| Auth Forms | Button disabled + spinner inside button |

### 19.2 Error States

| Error Type | User Experience |
|------------|-----------------|
| Network Error | Toast: "Connection lost. Check your internet and try again." + Retry button |
| 401 Unauthorized | Redirect to login with message: "Session expired. Please log in again." |
| 403 Forbidden (tier limit) | Modal: "This feature requires [Tier]. Upgrade now?" + Upgrade button |
| 404 Not Found | "Opportunity not found. It may have been removed." + Back to dashboard link |
| 500 Server Error | Toast: "Something went wrong on our end. We've been notified." + Retry button |
| Rate Limited (429) | Toast: "Too many requests. Please wait a moment." + Auto-retry after delay |
| Scan Timeout | "Scan is taking longer than expected. We'll email you when complete." |

### 19.3 Empty States

| Context | Message | Action |
|---------|---------|--------|
| No opportunities yet | "No opportunities found yet. Run your first scan to discover validated ideas." | "Run Scan" button |
| No search results | "No opportunities match your search. Try different keywords." | Clear search button |
| No opportunities in tier | "Opportunities in this range require [Higher Tier]." | "View Plans" button |
| Filters too restrictive | "No opportunities match these filters. Try adjusting your criteria." | Reset filters button |

### 19.4 Form Validation

All forms validate on blur and on submit:

| Field | Validation | Error Message |
|-------|------------|---------------|
| Email | Valid format, not already registered | "Enter a valid email" / "Email already registered" |
| Password | Min 8 chars, 1 uppercase, 1 number | "Password must be 8+ characters with 1 uppercase and 1 number" |
| Password Confirm | Matches password field | "Passwords do not match" |

---

## 20. TESTING STRATEGY

### 20.1 Backend Testing (Python/Pytest)

**Unit Tests** (`/backend/tests/unit/`)
- Scoring algorithm: Verify correct score calculation for known inputs
- Validation rules: Test all boundary conditions (19 mentions vs 20 mentions)
- Data transformers: Test JSON parsing from each source

**Integration Tests** (`/backend/tests/integration/`)
- Database operations: CRUD for all models
- Authentication flow: Register → verify email → login → refresh token
- Stripe webhooks: Mock webhook payloads, verify DB updates
- API endpoints: Test auth middleware, tier restrictions, pagination

**Collector Tests** (`/backend/tests/collectors/`)
- Mock external API responses
- Test rate limit handling and backoff
- Test error handling for malformed responses

**Test Coverage Target:** 80% minimum for core modules (scoring, auth, payments)

**Run Command:** `pytest --cov=app --cov-report=html`

### 20.2 Frontend Testing (Vitest + React Testing Library)

**Component Tests** (`/frontend/src/__tests__/`)
- OpportunityCard: Renders all fields, correct score badge colors
- Filters: State updates correctly, API calls triggered
- Auth forms: Validation displays, submit handlers fire

**Integration Tests**
- Auth flow: Login → dashboard redirect → logout
- Subscription flow: Checkout → success → tier updated in UI

**E2E Tests (Playwright)** - Post-MVP
- Full user journey: Register → pay → scan → view opportunity → export

**Test Coverage Target:** 70% for components

**Run Command:** `npm run test`

### 20.3 Manual Test Checklist (Pre-Deploy)

- [ ] Register new account, verify email received
- [ ] Login, verify JWT stored correctly
- [ ] Complete Stripe checkout, verify subscription active
- [ ] Run scan, verify opportunities appear
- [ ] Filter by score, verify results update
- [ ] Open detail modal, verify all fields populated
- [ ] Export CSV, verify file downloads correctly
- [ ] Test on mobile viewport (375px width)
- [ ] Test dark/light mode toggle
- [ ] Test with slow network (Chrome DevTools throttling)

---

## 21. MONITORING & OBSERVABILITY

### 21.1 Error Tracking

**Tool:** Sentry (free tier: 5,000 errors/month)

**Backend Integration:**
```python
import sentry_sdk
sentry_sdk.init(dsn=os.environ["SENTRY_DSN"], environment="production")
```

**Frontend Integration:**
```javascript
Sentry.init({ dsn: import.meta.env.VITE_SENTRY_DSN });
```

**Alerts:** Email notification for new error types, Slack for error spike (10+ in 5 min)

### 21.2 Uptime Monitoring

**Tool:** UptimeRobot (free tier: 50 monitors)

| Endpoint | Frequency | Alert After |
|----------|-----------|-------------|
| `GET /health` | 5 min | 2 failures |
| `GET /` (frontend) | 5 min | 2 failures |
| PostgreSQL (via health endpoint) | 5 min | 1 failure |

**Health Endpoint Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2026-01-14T12:00:00Z"
}
```

### 21.3 Application Logging

**Log Format** (JSON for parsing):
```json
{
  "timestamp": "2026-01-14T12:00:00Z",
  "level": "ERROR",
  "correlation_id": "uuid-here",
  "user_id": "user_abc123",
  "event": "stripe_webhook_failed",
  "context": { "customer_id": "cus_xxx", "error": "Invalid signature" }
}
```

**Log Levels:**
- ERROR: Failures requiring attention (payment failures, scan crashes)
- WARNING: Unusual but recoverable (rate limit hit, retry triggered)
- INFO: Normal operations (user registered, scan completed)
- DEBUG: Detailed debugging (disabled in production)

**Log Retention:** 30 days on server, rotate daily

### 21.4 Key Metrics Dashboard

Track in simple admin dashboard or external tool (e.g., Grafana free):
- Active subscriptions by tier
- Daily scan completions
- Opportunities discovered (last 7 days)
- API response times (p50, p95)
- Error rate (errors / total requests)

---

## 22. BACKUP & DISASTER RECOVERY

### 22.1 Database Backups

| Backup Type | Frequency | Retention |
|-------------|-----------|-----------|
| Full backup | Daily at 03:00 UTC | 30 days |
| Transaction log | Continuous (WAL) | 7 days |

**Backup Command** (cron job):
```bash
pg_dump -Fc opportunity_finder > /backups/opportunity_finder_$(date +%Y%m%d).dump
```

**Storage:** Sync to S3-compatible storage (Backblaze B2: $0.005/GB/month)

**Restore Command:**
```bash
pg_restore -d opportunity_finder /backups/opportunity_finder_20260114.dump
```

### 22.2 Recovery Objectives

| Metric | Target |
|--------|--------|
| Recovery Point Objective (RPO) | < 24 hours (max data loss) |
| Recovery Time Objective (RTO) | < 4 hours (max downtime) |

### 22.3 Disaster Recovery Procedure

1. Provision new VPS (same spec)
2. Install dependencies (PostgreSQL, Python, Node, Nginx, Redis)
3. Restore database from latest backup
4. Pull latest code from Git repository
5. Configure environment variables
6. Start services, verify health endpoint
7. Update DNS to point to new server

---

## 23. API RATE LIMITING & SECURITY

### 23.1 API Rate Limits (Your API)

Protect against abuse and ensure fair usage:

| Tier | Requests/Minute | Requests/Hour | Scan Triggers/Day |
|------|-----------------|---------------|-------------------|
| Basic | 60 | 500 | 1 |
| Pro | 120 | 2,000 | 3 |
| Premium | 300 | 10,000 | Unlimited |
| Unauthenticated | 10 | 50 | 0 |

**Implementation:** Flask-Limiter with Redis backend

**Rate Limit Response (429):**
```json
{
  "data": null,
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests. Please wait before trying again.",
    "retry_after": 60
  }
}
```

### 23.2 Authentication Security

**JWT Configuration:**
- Access token expiry: 15 minutes
- Refresh token expiry: 7 days
- Refresh token rotation: New refresh token issued on each refresh
- Token storage: httpOnly cookies (not localStorage)

**Password Requirements:**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 number
- Bcrypt with cost factor 12

**Brute Force Protection:**
- 5 failed login attempts → 15 minute lockout
- 10 failed attempts → 1 hour lockout + email notification to user

### 23.3 CSRF Protection

- All state-changing requests require CSRF token
- Token generated per session, validated server-side
- SameSite=Strict on session cookies

### 23.4 Input Validation

All user inputs sanitized before processing:
- **SQL injection:** Parameterized queries via SQLAlchemy (never string concatenation)
- **XSS:** React escapes by default; sanitize any dangerouslySetInnerHTML
- **Path traversal:** Validate file paths against whitelist

---

## 24. ACCESSIBILITY (a11y)

### 24.1 WCAG 2.1 AA Compliance Target

**Keyboard Navigation:**
- All interactive elements focusable via Tab
- Focus visible indicator (2px outline)
- Escape closes modals
- Arrow keys navigate dropdown options

**Screen Reader Support:**
- Semantic HTML (header, main, nav, button vs div)
- ARIA labels on icon-only buttons
- Live regions for dynamic content updates (e.g., "Scan complete. 15 opportunities found.")
- Alt text on any images

**Color & Contrast:**
- Minimum contrast ratio 4.5:1 for body text
- Score badges use icons/patterns in addition to color (for colorblind users)
- Don't rely solely on color to convey information

### 24.2 Specific Component Requirements

| Component | Requirement |
|-----------|-------------|
| Score Badge | Include text label, not just color (e.g., "88 - Excellent") |
| Filter Slider | Keyboard operable, announces current value |
| Modal | Focus trapped inside, Escape to close, focus returns on close |
| Toast Notifications | role="alert", auto-dismiss after 5s with option to persist |
| Data Tables | Proper th/td, scope attributes |

### 24.3 Testing Tools

- axe DevTools browser extension (automated checks)
- VoiceOver (macOS) / NVDA (Windows) for screen reader testing
- Keyboard-only navigation test (unplug mouse)

---

## 25. DATA RETENTION & GDPR COMPLIANCE

### 25.1 Data Retention Policy

| Data Type | Retention Period | Deletion Trigger |
|-----------|------------------|------------------|
| Active user data | Indefinite while subscribed | Account deletion request |
| Cancelled user data | 90 days after cancellation | Automatic purge |
| Scan job logs | 30 days | Automatic purge |
| Application logs | 30 days | Automatic rotation |
| Backups | 30 days | Automatic rotation |

### 25.2 User Data Deletion

**Trigger:** User requests deletion OR 90 days post-cancellation

**Process:**
1. Delete all records from `opportunities` where user_id matches
2. Delete all records from `pain_points` where user_id matches
3. Delete all records from `scan_jobs` where user_id matches
4. Delete user record from `users`
5. Cancel Stripe subscription (if active)
6. Send confirmation email to user's last known email

**Timeline:** Completed within 30 days of request (GDPR requirement)

### 25.3 Data Export (Existing)

Already covered: `GET /api/v1/user/export-data` for Pro/Premium tiers.

---

## APPENDIX A: REQUIRED ACCOUNTS & API KEYS

The following accounts and API keys are required to build and deploy the MVP. Most have free tiers sufficient for initial launch.

### A.1 Essential (Must Have for MVP)

#### Stripe
- **Purpose:** Payment processing and subscription management
- **URL:** https://stripe.com
- **Cost:** 2.9% + 20p per transaction
- **Keys Needed:** Publishable Key, Secret Key, Webhook Secret

#### SendGrid or Mailgun
- **Purpose:** Email alerts and notifications
- **URL:** https://sendgrid.com or https://mailgun.com
- **Cost:** Free tier: 100 emails/day (SendGrid), 5,000 emails/month (Mailgun)
- **Keys Needed:** API Key

#### Reddit API
- **Purpose:** Primary pain point discovery from subreddits
- **URL:** https://www.reddit.com/prefs/apps
- **Cost:** Free (rate limited: 60 requests/minute)
- **Keys Needed:** Client ID, Client Secret

#### ProductHunt API
- **Purpose:** Product launches and user feedback
- **URL:** https://api.producthunt.com/v2/docs
- **Cost:** Free (GraphQL API)
- **Keys Needed:** API Token

#### SerpAPI
- **Purpose:** Google Search for competitor discovery
- **URL:** https://serpapi.com
- **Cost:** Free tier: 100 searches/month, then $50/month for 5,000 searches
- **Keys Needed:** API Key

### A.2 Infrastructure (Deployment)

#### VPS Provider
- **Purpose:** Host backend and database
- **Options:** DigitalOcean, Hetzner, Linode
- **Cost:** £10-20/month for 2GB RAM droplet

#### Domain Name
- **Purpose:** opportunityfinder.app or similar
- **Provider:** Namecheap, Cloudflare, Google Domains
- **Cost:** £10-15/year

### A.3 Optional (Can Start Without)

#### Mailchimp or ConvertKit
- **Purpose:** Landing page email capture integration
- **Cost:** Free tier: 500 contacts
- **Alternative:** Store emails in database initially, migrate later

---

## APPENDIX B: EXAMPLE API RESPONSES

### GET /api/v1/opportunities

```json
{
  "data": [
    {
      "id": 1,
      "title": "Testimonial Collection Tool",
      "problem": "Businesses struggle to collect customer testimonials efficiently",
      "score": 88,
      "rank": 1,
      "mentions": 67,
      "mentions_trend": "up",
      "revenue": "£83,000 MRR",
      "revenue_amount": 83000,
      "competitors": 4,
      "competition_level": "Medium",
      "build_complexity": "Low",
      "sources": ["r/Entrepreneur", "r/smallbusiness", "Indie Hackers"],
      "source_urls": ["https://reddit.com/...", "https://indiehackers.com/..."],
      "example": "Senja.io",
      "competitor_urls": ["https://senja.io"],
      "validated": true,
      "recommendation": "Build immediately",
      "market_size": "200k+ businesses need testimonials",
      "problem_score": 8,
      "feasibility_score": 7,
      "timing_score": 9,
      "keyword_volume": "4.4K",
      "keyword_growth": "+127%",
      "keyword_competition": "MEDIUM",
      "status": "new",
      "created_at": "2026-01-08T10:30:00Z"
    }
  ],
  "error": null,
  "pagination": {
    "has_more": true,
    "next_cursor": "eyJpZCI6MTAwfQ==",
    "total_count": 500
  }
}
```

---

## APPENDIX C: ENVIRONMENT VARIABLES

Complete list of required environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/opportunity_finder

# Redis (Caching, Sessions, Job Queue)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Authentication
JWT_SECRET_KEY=<generate-256-bit-key>
JWT_ACCESS_TOKEN_EXPIRES=900  # 15 minutes in seconds
JWT_REFRESH_TOKEN_EXPIRES=604800  # 7 days in seconds

# Stripe
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Email
SENDGRID_API_KEY=SG.xxx

# Data Sources
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx
PRODUCTHUNT_TOKEN=xxx
SERPAPI_KEY=xxx

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx

# Application
FLASK_ENV=production
FRONTEND_URL=https://opportunityfinder.app

# File Storage
EXPORT_PATH=/var/app/exports
EXPORT_RETENTION_HOURS=24
```

---

## DOCUMENT CONTROL

### Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 10/01/2026 | Mark | Initial PRD - Core validation system |
| 1.1 | 10/01/2026 | Mark | Added multi-tenant architecture, authentication, Stripe payments, mobile-ready API design, competitive analysis |
| 1.2 | 10/01/2026 | Mark | Moved Email Alerts, Landing Page Builder, and Export Functionality into core MVP v1.0 (removed from out of scope) |
| 1.3 | 10/01/2026 | Mark | Added Admin Panel, subscription tiers/packages, dynamic data source management, required accounts list, updated timeline to 2-3 weeks |
| 1.4 | 10/01/2026 | Mark | Added tier-based opportunity ranking access (Basic: rank 11+, Pro: rank 6+, Premium: all), multi-currency support (£ GBP / $ USD switchable) |
| 1.5 | 10/01/2026 | Mark | Added password reset, email verification, user profile page, failed payment handling (dunning), GDPR data export (Pro/Premium), flexible free trial configuration, documented Help/FAQ and Onboarding for post-MVP |
| 1.6 | 11/01/2026 | Mark + Maya | Added error states & UX (Section 19), testing strategy (Section 20), monitoring & observability (Section 21), backup & disaster recovery (Section 22), API rate limiting & security (Section 23), accessibility (Section 24), data retention & GDPR compliance (Section 25), environment variables (Appendix C). Converted to Markdown format. |
| 1.7 | 11/01/2026 | Mark + Maya | Integrated scalability specs: Redis caching + Celery job queue, API versioning + pagination standard + search implementation, audit logging, webhook retry logic, database indexes, webhook_events table, file storage + CDN path, updated environment variables. |
| 1.9 | 13/01/2026 | Mark | Incorporated Ideabrowser methodology analysis (4-factor scoring, keyword volume metrics), Phase 1 scope clarification |
| 2.0 | 14/01/2026 | Mark + Claude | **Major consolidation release:** Integrated all planning artifacts including: Quality Architecture Requirements (Section 3.4), Architectural Decisions (Section 3.5), Implementation Patterns & Consistency Rules (Section 10), Complete Project Structure (Section 11), Frontend Page Structure & Component Specifications (Section 6.4-6.5), Keyword volume columns added to opportunities table (Section 9.4), God-mode admin requirements (Section 7.7). Resolved version numbering inconsistencies. |

### Approvals

| Field | Value |
|-------|-------|
| Document Owner | Mark |
| Status | APPROVED FOR DEVELOPMENT |
| Date | 14/01/2026 |

---

**— END OF DOCUMENT —**
