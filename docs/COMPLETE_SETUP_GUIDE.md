# Opportunity Finder - Complete Setup Guide

This guide covers everything you need to get the data collection engine working.

---

## Quick Start Summary

| What | Where | Time |
|------|-------|------|
| Hacker News | No setup needed | Ready now |
| Indie Hackers | No setup needed | Ready now |
| Bluesky | No setup needed (public API) | Ready now |
| Mastodon | No setup needed (public API) | Ready now |
| Reddit | https://reddit.com/prefs/apps | 5 min |
| Product Hunt | https://api.producthunt.com/v2/docs | 10 min |
| Google Trends | https://serpapi.com | 5 min |

---

## Part 1: Sources That Work Immediately

These sources don't require any API keys:

### Hacker News
- **Status:** Ready to use
- **How it works:** Uses free Algolia HN Search API
- **What it collects:** Posts about startups, SaaS, pain points

### Indie Hackers
- **Status:** Ready to use
- **How it works:** Web scraping of public product listings
- **What it collects:** Product listings with revenue data
- **Note:** May break if Indie Hackers changes their website

### Bluesky
- **Status:** Ready to use
- **How it works:** Public AT Protocol API (no auth for search)
- **What it collects:** Posts about startups, building in public
- **Optional:** Add your Bluesky credentials for higher rate limits

### Mastodon
- **Status:** Ready to use
- **How it works:** Public API across multiple instances
- **What it collects:** Tech/startup posts from Mastodon, Hachyderm, Fosstodon, etc.
- **Optional:** Add access token for higher rate limits

---

## Part 2: Sources That Need API Keys

### Reddit API (Recommended)

**Why Reddit:** High volume of pain point discussions in subreddits like r/SaaS, r/startups, r/Entrepreneur

**Time needed:** 5 minutes

**Steps:**

1. Go to https://www.reddit.com/prefs/apps
2. Log in to Reddit (create account if needed)
3. Scroll down and click **"create another app..."** (or "are you a developer? create an app...")
4. Fill in the form:
   - **name:** `OpportunityFinder`
   - **App type:** Select **"script"** (important!)
   - **description:** `Opportunity research tool`
   - **about url:** Leave blank
   - **redirect uri:** `http://localhost:8000` (required but not used)
5. Click **"create app"**
6. You'll see your new app. Copy these values:
   - **client_id:** The string under "personal use script" (e.g., `Ab1Cd2Ef3Gh4Ij`)
   - **client_secret:** Next to "secret"

**Where to enter:**
- Go to Admin → Data Sources → Reddit → Configure
- Or edit `backend/.env`:
  ```
  REDDIT_CLIENT_ID=your_client_id_here
  REDDIT_CLIENT_SECRET=your_client_secret_here
  ```

---

### Product Hunt API (Optional)

**Why Product Hunt:** See what's being launched, identify market gaps

**Time needed:** 10 minutes

**Steps:**

1. Go to https://www.producthunt.com
2. Log in or create an account
3. Go to https://www.producthunt.com/v2/oauth/applications
4. Click **"Add an Application"**
5. Fill in:
   - **Name:** `OpportunityFinder`
   - **Redirect URI:** `http://localhost:5173/callback`
6. After creation, find your **Developer Token** (API Token)

**Where to enter:**
- Go to Admin → Data Sources → Product Hunt → Configure
- Or edit `backend/.env`:
  ```
  PRODUCT_HUNT_TOKEN=your_token_here
  ```

---

### Google Trends via SerpAPI (Optional)

**Why Google Trends:** Validate keyword interest and growth

**Time needed:** 5 minutes

**Cost:** 100 free searches/month, then paid

**Steps:**

1. Go to https://serpapi.com
2. Click **"Get Started Free"**
3. Create account (email or Google sign-in)
4. After signup, go to https://serpapi.com/manage-api-key
5. Copy your API key

**Where to enter:**
- Go to Admin → Data Sources → Google Trends → Configure
- Or edit `backend/.env`:
  ```
  SERPAPI_KEY=your_key_here
  ```

---

### Bluesky (Optional Enhanced)

**Why authenticate:** Higher rate limits, access to more features

**Steps:**

1. Go to https://bsky.app/settings/app-passwords
2. Create an **App Password** (not your main password)
3. Your identifier is your handle (e.g., `yourname.bsky.social`)

**Where to enter:**
- Go to Admin → Data Sources → Bluesky → Configure
- Or edit `backend/.env`:
  ```
  BLUESKY_IDENTIFIER=yourname.bsky.social
  BLUESKY_PASSWORD=your_app_password
  ```

---

### Mastodon (Optional Enhanced)

**Why authenticate:** Higher rate limits on your home instance

**Steps:**

1. Go to your Mastodon instance (e.g., https://mastodon.social)
2. Go to Settings → Development → New Application
3. Create an application with read permissions
4. Copy the access token

**Where to enter:**
- Go to Admin → Data Sources → Mastodon → Configure
- Or edit `backend/.env`:
  ```
  MASTODON_ACCESS_TOKEN=your_token
  MASTODON_INSTANCE=https://mastodon.social
  ```

---

## Part 3: Using the Admin Interface

### Accessing the Admin Panel

1. Start the backend: `cd backend && python run.py`
2. Start the frontend: `cd frontend && npm run dev`
3. Open http://localhost:5173
4. Log in as admin
5. Go to Admin → Data Sources

### For Each Data Source You Can:

| Action | What It Does |
|--------|--------------|
| **Enable/Disable** | Toggle whether the source is used in scans |
| **Configure** | Enter API keys (saved to database) |
| **Test** | Verify the source works before enabling |
| **Docs** | Open the official documentation |

### Testing Sources

1. Click **Test** next to any source
2. Wait for the test to complete
3. You'll see:
   - ✓ Green = Working (shows sample items found)
   - ✗ Red = Not working (shows error message)

**Test sources before enabling them!**

---

## Part 4: Running Your First Scan

### Prerequisites

1. Start PostgreSQL database
2. Start Redis: `redis-server`
3. Start the backend: `cd backend && python run.py`
4. Start Celery worker: `cd backend && celery -A app.celery_app worker --loglevel=info`
5. Start the frontend: `cd frontend && npm run dev`

### Via Admin UI

1. Go to Admin → Scans
2. Click "Run Scan"
3. Watch progress update

### Via API (Command Line)

```bash
# Trigger scan for all enabled sources
curl -X POST http://localhost:5000/api/v1/scan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Trigger scan for specific sources only
curl -X POST http://localhost:5000/api/v1/scan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"sources": ["hacker_news", "bluesky"]}'
```

### Check Scan Status

```bash
curl http://localhost:5000/api/v1/scan/SCAN_ID
```

---

## Part 5: Troubleshooting

### "Connection failed" on Test

| Source | Common Issue | Solution |
|--------|--------------|----------|
| Reddit | Invalid credentials | Check client_id and client_secret, ensure app type is "script" |
| Product Hunt | Token expired | Generate a new Developer Token |
| Google Trends | API limit reached | Wait or upgrade SerpAPI plan |
| Bluesky | Wrong password | Use an App Password, not your main password |
| Mastodon | Instance blocked search | Try a different instance |

### Celery Not Running

```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Check Celery logs
celery -A app.celery_app worker --loglevel=debug
```

### No Opportunities Found

1. Check that at least one source is enabled
2. Run a test on each enabled source
3. Check Celery worker logs for errors
4. Verify the scan completed (check Admin → Scans)

### API Keys Not Working

1. Make sure there are no extra spaces in the keys
2. Reddit: Verify app type is "script"
3. Product Hunt: Use Developer Token, not OAuth token
4. SerpAPI: Check remaining credits

---

## Part 6: Source Overview

| Source | Auth Required | Rate Limit | Data Type |
|--------|---------------|------------|-----------|
| Hacker News | No | Unlimited | Posts, comments |
| Indie Hackers | No | ~100/min | Product listings, revenue |
| Bluesky | No (optional) | ~100/min | Posts |
| Mastodon | No (optional) | Varies by instance | Posts |
| Reddit | Yes (free) | 60/min | Posts from 10+ subreddits |
| Product Hunt | Yes (free) | 100/day | Product launches |
| Google Trends | Yes (paid) | 100 free/month | Keyword trends |

---

## Part 7: Recommended Setup Order

### Minimum Viable Test

1. Enable Hacker News (no setup)
2. Enable Bluesky (no setup)
3. Run a test scan
4. Check dashboard for opportunities

### Full Setup

1. Enable all free sources (HN, IH, Bluesky, Mastodon)
2. Get Reddit API keys → Enable Reddit
3. Get Product Hunt token → Enable Product Hunt
4. (Optional) Get SerpAPI key → Enable Google Trends
5. Run full scan

---

## Need Help?

- Check `backend/logs/` for error details
- Test each source individually to isolate issues
- Disable problematic sources to keep others running
