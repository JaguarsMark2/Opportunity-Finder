# Opportunity Finder - Setup & Usage Guide

Complete micro-SaaS opportunity validation system.

## What You Have

1. **Frontend (Web App)** - `opportunity-finder.html`
   - Beautiful dashboard UI
   - Currently shows sample data
   - Can be connected to live backend

2. **Backend (Python)** - `backend/`
   - Reddit scraper for pain points
   - Opportunity validation engine
   - Scoring algorithm
   - SQLite database
   - REST API server

## Quick Start (Frontend Only)

**Option 1: View Sample Data**
1. Download `opportunity-finder.html`
2. Double-click to open in any browser
3. You'll see 8 real example opportunities (static data)

That's it! The frontend works standalone.

## Full Setup (Backend + Frontend)

### Prerequisites
- Python 3.8+
- pip package manager

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt --break-system-packages
```

This installs:
- Flask (API server)
- PRAW (Reddit API)
- BeautifulSoup4 (web scraping)
- Requests (HTTP)

### Step 2: Get Reddit API Credentials (Optional)

The system works without Reddit credentials (uses mock data), but for real data:

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" type
4. Note your:
   - client_id (under app name)
   - client_secret (labeled "secret")

### Step 3: Run Your First Scan

**Without Reddit (mock data):**
```bash
cd backend
python opportunity_finder.py
```

**With Reddit (real data):**
Edit `opportunity_finder.py` line 420-424:
```python
finder = OpportunityFinder(reddit_credentials={
    'client_id': 'YOUR_CLIENT_ID_HERE',
    'client_secret': 'YOUR_CLIENT_SECRET_HERE',
    'user_agent': 'OpportunityFinder/1.0'
})
```

Then run:
```bash
python opportunity_finder.py
```

You'll see:
- Pain points collected
- Themes identified
- Opportunities validated
- Scores calculated
- Results saved to `opportunities.db`

### Step 4: Start API Server

```bash
cd backend
python api_server.py
```

API runs at `http://localhost:5000`

Test it:
```bash
curl http://localhost:5000/api/health
curl http://localhost:5000/api/opportunities
```

### Step 5: Connect Frontend to API

Currently the HTML file uses static data. To connect it to your live backend:

1. Open `opportunity-finder.html` in a text editor
2. Find the `sampleOpportunities` array (around line 100)
3. Replace the component with API-connected version:

```javascript
// Add at top of script
const [loading, setLoading] = useState(true);
const [opportunities, setOpportunities] = useState([]);

// Add useEffect to fetch data
useEffect(() => {
  fetch('http://localhost:5000/api/opportunities')
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        setOpportunities(data.data);
        setLoading(false);
      }
    })
    .catch(err => {
      console.error('Failed to load opportunities:', err);
      setLoading(false);
    });
}, []);

// Replace sampleOpportunities with opportunities variable
```

## Usage Guide

### Running Automated Scans

Set up weekly scans with cron (Linux/Mac):

```bash
# Edit crontab
crontab -e

# Add this line (runs every Monday at 9am)
0 9 * * 1 cd /path/to/backend && python opportunity_finder.py
```

### API Endpoints

**GET /api/opportunities**
- Get all opportunities
- Query params:
  - `min_score=60` - Filter by minimum score
  - `sort=revenue` - Sort by revenue/mentions/score
  - `search=testimonial` - Search term

**GET /api/opportunities/:id**
- Get single opportunity

**POST /api/scan**
- Trigger new scan
- Optional body: `{"reddit_credentials": {...}}`

**GET /api/stats**
- Get summary statistics

### Database

SQLite database: `opportunities.db`

Tables:
- `opportunities` - Validated opportunities with scores
- `pain_points` - Raw pain point mentions

View with:
```bash
sqlite3 opportunities.db
sqlite> SELECT title, score, revenue FROM opportunities ORDER BY score DESC;
```

## How It Works

### 1. Pain Point Collection
Scans Reddit for phrases like:
- "looking for a tool"
- "need software for"
- "wish there was"
- "tired of manually"

Subreddits monitored:
- r/Entrepreneur
- r/smallbusiness
- r/freelance
- r/SaaS
- r/startups

### 2. Theme Aggregation
Groups similar pain points into opportunities.

### 3. Validation
For each opportunity:
- Searches for existing paid solutions
- Checks revenue data (Indie Hackers, etc)
- Counts competitors

### 4. Scoring (0-100)
- **25%** - Demand Frequency (mentions)
- **35%** - Revenue Proof (existing MRR)
- **20%** - Competition Level
- **20%** - Build Complexity

### 5. Recommendation
- 80-100: "Build immediately"
- 60-79: "Validate with landing page first"
- 40-59: "High risk - need unique angle"
- 0-39: "Reject - insufficient validation"

## Customization

### Add More Data Sources

Edit `OpportunityFinder` class:

```python
def collect_from_indie_hackers(self):
    # Add scraper for Indie Hackers
    pass

def collect_from_twitter(self):
    # Add Twitter API integration
    pass
```

### Adjust Scoring Weights

Edit `OpportunityScorer.calculate_score()`:

```python
# Change from 35% to 40%
if revenue_amount >= 10000:
    score += 40  # was 35
```

### Change Subreddits

Edit `RedditCollector.SUBREDDITS`:

```python
SUBREDDITS = [
    'webdev',
    'programming',
    'marketing',
    # Add your niche subreddits
]
```

## Troubleshooting

**"praw not installed"**
```bash
pip install praw --break-system-packages
```

**"CORS error" in browser**
- Make sure API server is running
- Check browser console for exact error
- Verify `flask-cors` is installed

**"No opportunities found"**
- Run with mock data first to test system
- Check Reddit credentials are correct
- Verify subreddits are accessible

**"Rate limit exceeded"**
- Reddit API has limits (60 requests/min)
- Add delays between requests
- Reduce `limit_per_subreddit` parameter

## Next Steps

### For Personal Use
1. Run weekly scans
2. Review high-scoring opportunities
3. Validate top 3 with landing pages
4. Build the winner

### To Build as SaaS
1. Deploy API to cloud (Heroku, AWS, DigitalOcean)
2. Update HTML to point to deployed API
3. Add authentication
4. Add payment processing (Stripe)
5. Price at £5-20/month

### To Improve
1. Add more data sources (Twitter, HN, forums)
2. Implement NLP for better theme clustering
3. Add automated competitor research
4. Build email alerts for high scores
5. Create detailed market size calculations

## File Structure

```
opportunity-finder.html          # Frontend (standalone)
Opportunity_Finder_Specification.docx  # Full spec document

backend/
├── opportunity_finder.py        # Main backend system
├── api_server.py               # Flask API
├── requirements.txt            # Python dependencies
├── opportunities.db            # SQLite database (created on first run)
└── opportunities.json          # Export file (created on scan)
```

## Support

This is a complete working system. Everything you need is here:
- Frontend works standalone with sample data
- Backend collects and scores real opportunities
- API connects them together

Start with the frontend to see the UI, then add the backend when you're ready to find real opportunities.
