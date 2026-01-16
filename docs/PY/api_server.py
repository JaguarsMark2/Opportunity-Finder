"""
Flask API Server for Opportunity Finder
Provides REST API endpoints for the frontend
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from opportunity_finder import OpportunityFinder, Database
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Initialize
db = Database()
finder = OpportunityFinder()


@app.route('/api/opportunities', methods=['GET'])
def get_opportunities():
    """
    Get all opportunities
    
    Query params:
    - min_score: Minimum score filter (default: 0)
    - sort: Sort by (score, revenue, mentions) (default: score)
    - search: Search term for title/problem
    """
    try:
        min_score = int(request.args.get('min_score', 0))
        sort_by = request.args.get('sort', 'score')
        search = request.args.get('search', '').lower()
        
        opportunities = db.get_all_opportunities()
        
        # Filter by min score
        opportunities = [o for o in opportunities if o['score'] >= min_score]
        
        # Filter by search term
        if search:
            opportunities = [
                o for o in opportunities 
                if search in o['title'].lower() or search in o['problem'].lower()
            ]
        
        # Sort
        sort_key = {
            'score': lambda x: x['score'],
            'revenue': lambda x: x['revenue_amount'],
            'mentions': lambda x: x['mentions']
        }.get(sort_by, lambda x: x['score'])
        
        opportunities = sorted(opportunities, key=sort_key, reverse=True)
        
        return jsonify({
            'success': True,
            'data': opportunities,
            'count': len(opportunities)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/opportunities/<int:opportunity_id>', methods=['GET'])
def get_opportunity(opportunity_id):
    """Get single opportunity by ID"""
    try:
        opportunities = db.get_all_opportunities()
        opportunity = next((o for o in opportunities if o['id'] == opportunity_id), None)
        
        if not opportunity:
            return jsonify({
                'success': False,
                'error': 'Opportunity not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': opportunity
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/scan', methods=['POST'])
def run_scan():
    """
    Trigger new opportunity scan
    
    Body (optional):
    {
        "reddit_credentials": {
            "client_id": "...",
            "client_secret": "...",
            "user_agent": "..."
        }
    }
    """
    try:
        data = request.get_json() or {}
        reddit_creds = data.get('reddit_credentials')
        
        # Initialize finder with credentials if provided
        if reddit_creds:
            finder_instance = OpportunityFinder(reddit_credentials=reddit_creds)
        else:
            finder_instance = OpportunityFinder()
        
        # Run scan
        opportunities = finder_instance.run_scan()
        
        return jsonify({
            'success': True,
            'message': f'Scan complete. Found {len(opportunities)} opportunities.',
            'data': [
                {
                    'id': o.id,
                    'title': o.title,
                    'score': o.score
                } for o in opportunities
            ]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get summary statistics"""
    try:
        opportunities = db.get_all_opportunities()
        
        if not opportunities:
            return jsonify({
                'success': True,
                'data': {
                    'total': 0,
                    'validated': 0,
                    'high_score': 0,
                    'avg_score': 0
                }
            })
        
        stats = {
            'total': len(opportunities),
            'validated': len([o for o in opportunities if o['validated']]),
            'high_score': len([o for o in opportunities if o['score'] >= 70]),
            'avg_score': round(sum(o['score'] for o in opportunities) / len(opportunities))
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'API is running',
        'version': '1.0.0'
    })


if __name__ == '__main__':
    print("Starting Opportunity Finder API...")
    print("API will be available at: http://localhost:5000")
    print("\nEndpoints:")
    print("  GET  /api/opportunities     - Get all opportunities")
    print("  GET  /api/opportunities/:id - Get single opportunity")
    print("  POST /api/scan              - Run new scan")
    print("  GET  /api/stats             - Get statistics")
    print("  GET  /api/health            - Health check")
    print("\n" + "=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
