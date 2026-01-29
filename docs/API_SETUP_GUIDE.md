# API Setup Guide for Opportunity Finder Data Sources

This guide will help you set up the API keys needed to run the data collection engine.

---

## Quick Reference

| Source | API Keys Needed | Free? | Required? |
|--------|-----------------|-------|-----------|
| Reddit | Yes | Yes (free) | YES |
| Hacker News | No | Yes (free) | Already works |
| Indie Hackers | No | Yes (scraping) | Already works |
| Product Hunt | Yes | Yes (free tier) | Recommended |
| Google Trends (SerpAPI) | Yes | 100 free/month | Optional |

---

## 1. Reddit API (Required)

**Time:** 5 minutes

### Steps:

1. Go to https://www.reddit.com/prefs/apps
2. Scroll down and click **"create another app..."**
3. Fill in:
   - **name:** `OpportunityFinder` (or any name)
   - **App type:** Select **"script"**
   - **description:** `Data collection for opportunity research`
   - **about url:** Leave blank
   - **redirect uri:** `http://localhost:8000` (required but not used)
4. Click **"create app"**
5. You'll see your app. Copy:
   - **client_id:** The string under "personal use script" (looks like: `Ab1Cd2Ef3Gh4Ij`)
   - **client_secret:** The "secret" value

### Add to .env:

```
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=OpportunityFinder/1.0
```

---

## 2. Hacker News (No Setup Needed)

Uses the free Algolia HN Search API. No authentication required.

**Status:** Ready to use immediately.

---

## 3. Indie Hackers (No Setup Needed)

Uses web scraping of public pages. No API key required.

**Status:** Ready to use immediately.

**Note:** May break if Indie Hackers changes their website structure.

---

## 4. Product Hunt API (Recommended)

**Time:** 10 minutes

### Steps:

1. Go to https://www.producthunt.com/v2/oauth/applications
2. Sign in with your Product Hunt account (create one if needed)
3. Click **"Add an Application"**
4. Fill in:
   - **Name:** `OpportunityFinder`
   - **Redirect URI:** `http://localhost:5173/callback`
5. After creation, you'll see your credentials
6. Copy the **API Token** (also called Developer Token)

### Add to .env:

```
PRODUCT_HUNT_TOKEN=your_api_token_here
```

---

## 5. SerpAPI / Google Trends (Optional)

**Time:** 5 minutes
**Cost:** 100 free searches/month, then paid

### Steps:

1. Go to https://serpapi.com/
2. Click **"Get Started Free"**
3. Create account (email or Google)
4. After signup, go to https://serpapi.com/manage-api-key
5. Copy your API key

### Add to .env:

```
SERPAPI_KEY=your_serpapi_key_here
```

**Note:** If you skip this, the system will still work but won't have Google Trends data (keyword volume, growth metrics).

---

## Final .env Configuration

Your `backend/.env` file should have these data source entries:

```bash
# Reddit API (Required)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=OpportunityFinder/1.0

# Product Hunt API (Recommended)
PRODUCT_HUNT_TOKEN=your_token

# SerpAPI for Google Trends (Optional)
SERPAPI_KEY=your_key

# Enabled sources (comma-separated)
# Remove any sources you don't have keys for
ENABLED_SOURCES=reddit,hacker_news,indie_hackers,product_hunt
```

---

## Testing Your Setup

After configuring your `.env` file:

1. Start the backend:
   ```bash
   cd backend
   source .venv/bin/activate
   python run.py
   ```

2. Start Redis (required for Celery):
   ```bash
   redis-server
   ```

3. Start Celery worker:
   ```bash
   cd backend
   celery -A app.celery_app worker --loglevel=info
   ```

4. Trigger a test scan via API:
   ```bash
   curl -X POST http://localhost:5000/api/v1/scan \
     -H "Content-Type: application/json" \
     -d '{"sources": ["hacker_news"]}'
   ```

This will test with Hacker News first (no auth needed) to verify the system works.

---

## Troubleshooting

### Reddit: "Invalid credentials"
- Double-check client_id and client_secret
- Make sure app type is "script"
- user_agent must not be empty

### Product Hunt: "Unauthorized"
- Token may have expired, generate a new one
- Check if you're using the Developer Token (not OAuth)

### SerpAPI: "Invalid API key"
- Free tier has 100 searches/month limit
- Check for trailing spaces in key

### Celery not running
- Ensure Redis is running: `redis-cli ping` should return `PONG`
- Check CELERY_BROKER_URL in .env matches your Redis setup
