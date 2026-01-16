"""
Opportunity Finder Backend
Collects, validates, and scores micro-SaaS opportunities from multiple sources
"""

import os
import re
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import time

# Requirements to install:
# pip install praw requests beautifulsoup4 --break-system-packages


@dataclass
class Opportunity:
    id: Optional[int]
    title: str
    problem: str
    score: int
    mentions: int
    revenue: str
    revenue_amount: int
    competitors: int
    competition_level: str
    build_complexity: str
    sources: List[str]
    example: str
    validated: bool
    recommendation: str
    market_size: str
    created_at: str
    
    def to_dict(self):
        return {
            **asdict(self),
            'sources': json.dumps(self.sources)
        }


class Database:
    """Handles all database operations"""
    
    def __init__(self, db_path='opportunities.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                problem TEXT NOT NULL,
                score INTEGER NOT NULL,
                mentions INTEGER NOT NULL,
                revenue TEXT,
                revenue_amount INTEGER,
                competitors INTEGER,
                competition_level TEXT,
                build_complexity TEXT,
                sources TEXT,
                example TEXT,
                validated BOOLEAN,
                recommendation TEXT,
                market_size TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pain_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                text TEXT NOT NULL,
                url TEXT,
                mentions INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_opportunity(self, opportunity: Opportunity) -> int:
        """Save an opportunity to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        data = opportunity.to_dict()
        del data['id']  # Let DB handle ID
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        
        cursor.execute(
            f'INSERT INTO opportunities ({columns}) VALUES ({placeholders})',
            tuple(data.values())
        )
        
        opportunity_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return opportunity_id
    
    def get_all_opportunities(self) -> List[Dict]:
        """Retrieve all opportunities"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM opportunities ORDER BY score DESC')
        rows = cursor.fetchall()
        conn.close()
        
        opportunities = []
        for row in rows:
            opp = dict(row)
            opp['sources'] = json.loads(opp['sources'])
            opportunities.append(opp)
        
        return opportunities
    
    def save_pain_point(self, source: str, text: str, url: Optional[str] = None):
        """Save a pain point mention"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO pain_points (source, text, url, created_at)
            VALUES (?, ?, ?, ?)
        ''', (source, text, url, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()


class RedditCollector:
    """Collects pain points from Reddit"""
    
    # Pain point detection keywords
    PAIN_KEYWORDS = [
        "looking for a tool",
        "need software for",
        "wish there was",
        "hate that I have to",
        "tired of manually",
        "paying too much for",
        "can't find a simple",
        "frustrated with",
        "how do I automate",
        "is there a way to"
    ]
    
    SUBREDDITS = [
        'Entrepreneur',
        'smallbusiness',
        'freelance',
        'SaaS',
        'startups',
        'indiehackers',
        'productivity'
    ]
    
    def __init__(self, reddit_credentials: Optional[Dict] = None):
        """
        Initialize Reddit collector
        
        reddit_credentials should contain:
        {
            'client_id': 'your_client_id',
            'client_secret': 'your_client_secret',
            'user_agent': 'OpportunityFinder/1.0'
        }
        """
        self.credentials = reddit_credentials
        self.reddit = None
        
        if reddit_credentials:
            try:
                import praw
                self.reddit = praw.Reddit(**reddit_credentials)
            except ImportError:
                print("Warning: praw not installed. Install with: pip install praw --break-system-packages")
    
    def collect_pain_points(self, limit_per_subreddit: int = 100) -> List[Dict]:
        """
        Scan Reddit for pain points
        
        Returns list of pain points with metadata
        """
        if not self.reddit:
            print("Reddit collector not initialized. Using mock data.")
            return self._get_mock_data()
        
        pain_points = []
        
        for subreddit_name in self.SUBREDDITS:
            print(f"Scanning r/{subreddit_name}...")
            
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search for pain point keywords
                for keyword in self.PAIN_KEYWORDS[:3]:  # Limit to avoid rate limits
                    for submission in subreddit.search(keyword, limit=limit_per_subreddit, time_filter='month'):
                        
                        # Check title and body for pain signals
                        text = f"{submission.title} {submission.selftext}"
                        
                        if self._contains_pain_signal(text):
                            pain_points.append({
                                'source': f'r/{subreddit_name}',
                                'title': submission.title,
                                'text': submission.selftext[:500],
                                'url': f'https://reddit.com{submission.permalink}',
                                'score': submission.score,
                                'num_comments': submission.num_comments
                            })
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"Error scanning r/{subreddit_name}: {e}")
                continue
        
        return pain_points
    
    def _contains_pain_signal(self, text: str) -> bool:
        """Check if text contains pain point indicators"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.PAIN_KEYWORDS)
    
    def _get_mock_data(self) -> List[Dict]:
        """Return mock data for testing without Reddit API"""
        return [
            {
                'source': 'r/Entrepreneur',
                'title': 'Looking for a tool to collect customer testimonials easily',
                'text': 'Running a small agency and manually asking clients for testimonials via email. Half dont respond. Need something automated.',
                'url': 'https://reddit.com/r/entrepreneur/mock1',
                'score': 45,
                'num_comments': 23
            },
            {
                'source': 'r/freelance',
                'title': 'Tired of manually tracking time across projects',
                'text': 'I have 5 clients and switching between tools is killing my productivity. Looking for something simple.',
                'url': 'https://reddit.com/r/freelance/mock2',
                'score': 67,
                'num_comments': 31
            }
        ]


class OpportunityScorer:
    """Scores opportunities based on validation criteria"""
    
    @staticmethod
    def calculate_score(
        mentions: int,
        revenue_amount: int,
        competitors: int,
        build_complexity: str
    ) -> int:
        """
        Calculate opportunity score (0-100)
        
        Weighting:
        - Demand Frequency: 25%
        - Revenue Proof: 35%
        - Competition: 20%
        - Build Complexity: 20%
        """
        score = 0
        
        # Demand Frequency (25 points max)
        if mentions >= 50:
            score += 25
        elif mentions >= 30:
            score += 15
        elif mentions >= 20:
            score += 10
        
        # Revenue Proof (35 points max)
        if revenue_amount >= 10000:
            score += 35
        elif revenue_amount >= 5000:
            score += 25
        elif revenue_amount >= 2000:
            score += 15
        elif revenue_amount >= 1000:
            score += 10
        
        # Competition Level (20 points max)
        if competitors <= 2:
            score += 20
        elif competitors <= 5:
            score += 15
        elif competitors <= 10:
            score += 10
        else:
            score += 5
        
        # Build Complexity (20 points max)
        complexity_scores = {
            'Low': 20,
            'Medium': 15,
            'High': 10,
            'Very High': 0
        }
        score += complexity_scores.get(build_complexity, 0)
        
        return min(score, 100)
    
    @staticmethod
    def get_recommendation(score: int) -> str:
        """Get action recommendation based on score"""
        if score >= 80:
            return "Build immediately"
        elif score >= 60:
            return "Validate with landing page first"
        elif score >= 40:
            return "High risk - need unique angle"
        else:
            return "Reject - insufficient validation"
    
    @staticmethod
    def get_competition_level(competitors: int) -> str:
        """Classify competition level"""
        if competitors <= 2:
            return "Very Low"
        elif competitors <= 5:
            return "Low"
        elif competitors <= 10:
            return "Medium"
        elif competitors <= 20:
            return "High"
        else:
            return "Very High"


class OpportunityValidator:
    """Validates opportunities by checking existing solutions"""
    
    def validate_opportunity(self, problem: str) -> Dict:
        """
        Validate if opportunity has existing paid solutions
        
        In production, this would:
        1. Search Google for "{problem} software"
        2. Check Indie Hackers for revenue data
        3. Analyze competitor websites
        
        Returns validation data
        """
        # Mock validation - in production, implement actual searches
        return {
            'has_paid_solutions': True,
            'competitors': 4,
            'estimated_revenue': 5000,
            'examples': ['Example SaaS'],
            'market_size': 'Small to Medium'
        }


class OpportunityFinder:
    """Main orchestrator for finding and scoring opportunities"""
    
    def __init__(self, reddit_credentials: Optional[Dict] = None):
        self.db = Database()
        self.reddit_collector = RedditCollector(reddit_credentials)
        self.validator = OpportunityValidator()
        self.scorer = OpportunityScorer()
    
    def run_scan(self) -> List[Opportunity]:
        """
        Run complete scan:
        1. Collect pain points
        2. Aggregate by theme
        3. Validate each opportunity
        4. Score and store
        """
        print("Starting opportunity scan...")
        print("=" * 60)
        
        # Step 1: Collect pain points
        print("\n[1/4] Collecting pain points from Reddit...")
        pain_points = self.reddit_collector.collect_pain_points()
        print(f"Found {len(pain_points)} pain point mentions")
        
        # Save pain points to DB
        for point in pain_points:
            self.db.save_pain_point(
                source=point['source'],
                text=point['text'],
                url=point.get('url')
            )
        
        # Step 2: Aggregate by theme (simplified - in production use NLP clustering)
        print("\n[2/4] Aggregating by theme...")
        themes = self._aggregate_themes(pain_points)
        print(f"Identified {len(themes)} opportunity themes")
        
        # Step 3: Validate each theme
        print("\n[3/4] Validating opportunities...")
        opportunities = []
        
        for theme in themes:
            print(f"  - Validating: {theme['title']}")
            
            validation = self.validator.validate_opportunity(theme['problem'])
            
            if not validation['has_paid_solutions']:
                print(f"    ✗ No paid solutions found - skipping")
                continue
            
            # Step 4: Score
            score = self.scorer.calculate_score(
                mentions=theme['mentions'],
                revenue_amount=validation['estimated_revenue'],
                competitors=validation['competitors'],
                build_complexity=theme['build_complexity']
            )
            
            competition_level = self.scorer.get_competition_level(
                validation['competitors']
            )
            
            recommendation = self.scorer.get_recommendation(score)
            
            opportunity = Opportunity(
                id=None,
                title=theme['title'],
                problem=theme['problem'],
                score=score,
                mentions=theme['mentions'],
                revenue=f"£{validation['estimated_revenue']:,} MRR",
                revenue_amount=validation['estimated_revenue'],
                competitors=validation['competitors'],
                competition_level=competition_level,
                build_complexity=theme['build_complexity'],
                sources=theme['sources'],
                example=', '.join(validation['examples']),
                validated=score >= 60,
                recommendation=recommendation,
                market_size=validation['market_size'],
                created_at=datetime.now().isoformat()
            )
            
            # Save to database
            opportunity.id = self.db.save_opportunity(opportunity)
            opportunities.append(opportunity)
            
            print(f"    ✓ Score: {score}/100 - {recommendation}")
        
        print("\n[4/4] Scan complete!")
        print(f"\nResults: {len(opportunities)} validated opportunities")
        print(f"High score (60+): {len([o for o in opportunities if o.score >= 60])}")
        
        return opportunities
    
    def _aggregate_themes(self, pain_points: List[Dict]) -> List[Dict]:
        """
        Aggregate pain points into common themes
        
        In production: use NLP/clustering
        For now: simplified keyword matching
        """
        # Mock theme aggregation
        themes = [
            {
                'title': 'Testimonial Collection Tool',
                'problem': 'Businesses struggle to collect customer testimonials efficiently',
                'mentions': 67,
                'build_complexity': 'Low',
                'sources': ['r/Entrepreneur', 'r/smallbusiness']
            },
            {
                'title': 'Time Tracking for Freelancers',
                'problem': 'Freelancers waste time tracking hours across multiple tools',
                'mentions': 31,
                'build_complexity': 'Low',
                'sources': ['r/freelance']
            }
        ]
        
        return themes
    
    def get_opportunities(self, min_score: int = 0) -> List[Dict]:
        """Get all opportunities from database"""
        all_opps = self.db.get_all_opportunities()
        return [o for o in all_opps if o['score'] >= min_score]
    
    def export_json(self, filepath: str):
        """Export opportunities to JSON file"""
        opportunities = self.get_opportunities()
        
        with open(filepath, 'w') as f:
            json.dump(opportunities, f, indent=2)
        
        print(f"Exported {len(opportunities)} opportunities to {filepath}")


def main():
    """Example usage"""
    
    # Initialize without Reddit credentials (will use mock data)
    finder = OpportunityFinder()
    
    # Or with real credentials:
    # finder = OpportunityFinder(reddit_credentials={
    #     'client_id': 'YOUR_CLIENT_ID',
    #     'client_secret': 'YOUR_CLIENT_SECRET',
    #     'user_agent': 'OpportunityFinder/1.0'
    # })
    
    # Run scan
    opportunities = finder.run_scan()
    
    # Display results
    print("\n" + "=" * 60)
    print("TOP OPPORTUNITIES")
    print("=" * 60)
    
    for opp in sorted(opportunities, key=lambda x: x.score, reverse=True)[:5]:
        print(f"\n{opp.title} (Score: {opp.score}/100)")
        print(f"  Problem: {opp.problem}")
        print(f"  Revenue: {opp.revenue}")
        print(f"  Competition: {opp.competition_level}")
        print(f"  Recommendation: {opp.recommendation}")
    
    # Export to JSON
    finder.export_json('opportunities.json')


if __name__ == '__main__':
    main()
