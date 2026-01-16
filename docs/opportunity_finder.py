#!/usr/bin/env python3
"""
Micro-SaaS Opportunity Finder
Scrapes Reddit, forums, and analyzes search trends to find validated business opportunities
"""

import json
import re
from datetime import datetime
from typing import List, Dict
import urllib.request
import urllib.parse

class OpportunityFinder:
    def __init__(self):
        self.opportunities = []
        self.pain_point_keywords = [
            "frustrated with", "hate that", "wish there was", "need a tool",
            "looking for a solution", "tired of", "can't find", "doesn't exist",
            "paying too much", "waste time", "manual process", "time consuming"
        ]
        
    def search_reddit_pain_points(self, subreddit: str, keywords: List[str]) -> List[Dict]:
        """
        Searches Reddit for pain points in specific subreddits
        Note: In production, you'd use PRAW (Reddit API) or scraping library
        """
        print(f"\n[REDDIT] Searching r/{subreddit} for: {', '.join(keywords)}")
        
        # Simulated results - in real implementation, use Reddit API
        simulated_results = [
            {
                "source": f"r/{subreddit}",
                "pain_point": "Manual invoicing takes 5+ hours per week",
                "frequency": "67 mentions",
                "urgency_score": 8,
                "potential_solution": "Automated invoice generation for freelancers"
            },
            {
                "source": f"r/{subreddit}",
                "pain_point": "No easy way to track client project hours across multiple tools",
                "frequency": "43 mentions", 
                "urgency_score": 7,
                "potential_solution": "Unified time tracking dashboard"
            }
        ]
        
        return simulated_results
    
    def analyze_search_volume(self, keyword: str) -> Dict:
        """
        Analyzes search volume and competition for a keyword
        In production: use Google Keyword Planner API, Ahrefs, or similar
        """
        print(f"[SEARCH] Analyzing: {keyword}")
        
        # Simulated data - replace with real API calls
        return {
            "keyword": keyword,
            "monthly_searches": 2400,
            "competition": "Low",
            "cpc": "$3.20",
            "trend": "Rising +15%"
        }
    
    def score_opportunity(self, pain_point: Dict, search_data: Dict) -> int:
        """
        Scores opportunity from 0-100 based on multiple factors
        """
        score = 0
        
        # Frequency of mentions
        freq = int(re.search(r'\d+', pain_point['frequency']).group())
        if freq > 50: score += 25
        elif freq > 20: score += 15
        else: score += 5
        
        # Urgency
        score += pain_point['urgency_score'] * 3
        
        # Search volume
        monthly = search_data['monthly_searches']
        if monthly > 5000: score += 25
        elif monthly > 1000: score += 15
        elif monthly > 500: score += 10
        else: score += 5
        
        # Competition
        if search_data['competition'] == 'Low': score += 20
        elif search_data['competition'] == 'Medium': score += 10
        
        # Trend
        if 'Rising' in search_data['trend']: score += 10
        
        return min(score, 100)
    
    def find_opportunities(self):
        """
        Main method to find and score opportunities
        """
        print("=" * 60)
        print("MICRO-SAAS OPPORTUNITY FINDER")
        print("=" * 60)
        
        # Subreddits to monitor
        subreddits = [
            'Entrepreneur', 'smallbusiness', 'freelance', 
            'SaaS', 'indiehackers', 'startups'
        ]
        
        keywords = ['automation', 'time tracking', 'invoicing', 'analytics']
        
        all_opportunities = []
        
        for sub in subreddits[:2]:  # Limit for demo
            results = self.search_reddit_pain_points(sub, keywords)
            
            for result in results:
                search_data = self.analyze_search_volume(result['potential_solution'])
                score = self.score_opportunity(result, search_data)
                
                opportunity = {
                    **result,
                    "search_data": search_data,
                    "opportunity_score": score,
                    "validated": score > 60
                }
                
                all_opportunities.append(opportunity)
        
        # Sort by score
        all_opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        return all_opportunities
    
    def generate_report(self, opportunities: List[Dict]):
        """
        Generates a detailed report of opportunities
        """
        print("\n" + "=" * 60)
        print("OPPORTUNITY REPORT")
        print("=" * 60)
        
        for i, opp in enumerate(opportunities, 1):
            print(f"\n#{i} - SCORE: {opp['opportunity_score']}/100")
            print(f"Status: {'✓ VALIDATED' if opp['validated'] else '✗ NEEDS MORE VALIDATION'}")
            print(f"\nPain Point: {opp['pain_point']}")
            print(f"Source: {opp['source']}")
            print(f"Frequency: {opp['frequency']}")
            print(f"Urgency: {opp['urgency_score']}/10")
            print(f"\nPotential Solution: {opp['potential_solution']}")
            print(f"Search Volume: {opp['search_data']['monthly_searches']}/mo")
            print(f"Competition: {opp['search_data']['competition']}")
            print(f"Trend: {opp['search_data']['trend']}")
            print(f"Est. CPC: {opp['search_data']['cpc']}")
            print("-" * 60)
        
        # Save to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"opportunities_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(opportunities, f, indent=2)
        
        print(f"\n✓ Full report saved to: {filename}")
        
    def get_implementation_blueprint(self, opportunity: Dict):
        """
        Generates step-by-step implementation plan
        """
        print("\n" + "=" * 60)
        print(f"IMPLEMENTATION BLUEPRINT")
        print(f"Solution: {opportunity['potential_solution']}")
        print("=" * 60)
        
        print("\nWEEK 1-2: VALIDATION")
        print("• Create landing page with problem statement")
        print("• Run $50 Google Ads test")
        print("• Post in 5 relevant subreddits")
        print("• Target: 50 email signups or kill it")
        
        print("\nWEEK 3-4: MVP BUILD")
        print("• Build core feature only")
        print("• No fancy UI - functional is enough")
        print("• Set up Stripe for payments")
        print("• Target: 5 beta customers at 50% off")
        
        print("\nWEEK 5-6: LAUNCH & ITERATE")
        print("• ProductHunt launch")
        print("• Indie Hackers post")
        print("• Email beta users for feedback")
        print("• Target: 10 paying customers at $20-50/mo")
        
        print("\nMONTH 2-3: SCALE OR KILL")
        print("• If <$500 MRR: pivot or kill")
        print("• If >$500 MRR: double down on marketing")
        print("• Add automation to reduce support")
        print("• Target: $2k MRR or move on")


def main():
    finder = OpportunityFinder()
    
    # Find opportunities
    opportunities = finder.find_opportunities()
    
    # Generate report
    finder.generate_report(opportunities)
    
    # Show blueprint for top opportunity
    if opportunities:
        print("\n" + "=" * 60)
        response = input("\nShow implementation blueprint for top opportunity? (y/n): ")
        if response.lower() == 'y':
            finder.get_implementation_blueprint(opportunities[0])


if __name__ == "__main__":
    main()
