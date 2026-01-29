"""Scoring service for calculating opportunity scores.

Implements admin-configurable scoring algorithm with 4 weighted criteria:
- Demand Frequency (25%): Based on mention count and upvotes
- Revenue Proof (35%): Based on competitor revenue data
- Competition (20%): Inverted - fewer competitors is better
- Build Complexity (20%): Lower complexity is better

UPVOTE VALIDATION CRITERIA:
Posts with upvotes are prioritized because upvotes serve as community validation:
- Each upvote represents another person with the same pain point
- Upvoters are interested enough to take action (not passive)
- Higher upvotes = larger addressable market
- Community has vetted this as a legitimate need, not noise

Upvote Thresholds:
- 10+ upvotes = Initial validation (worth investigating)
- 50+ upvotes = Strong validation (build MVP priority)
- 100+ upvotes = Validated market (fast-track to development)

Sources with Upvote Data: Reddit, Hacker News, Indie Hackers, Product Hunt
"""

import math
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models import Competitor, Opportunity, SystemSettings


class ScoringService:
    """Service for calculating opportunity scores.

    Scores are calculated from 0-100 based on admin-configurable weights.
    Validation status determined by: existing paid solution, £1k+ MRR,
    20+ mentions, B2B focus.
    """

    # Default scoring weights (admin-configurable)
    DEFAULT_WEIGHTS = {
        'demand_frequency': 0.25,  # 25%
        'revenue_proof': 0.35,      # 35%
        'competition': 0.20,        # 20%
        'build_complexity': 0.20    # 20%
    }

    # Validation thresholds (admin-configurable)
    DEFAULT_THRESHOLDS = {
        'min_revenue_mrr': 1000,   # £1,000 MRR
        'min_mentions': 20,
        'min_competitors': 1
    }

    # Enabled criteria (admin-configurable - which criteria to use)
    DEFAULT_ENABLED_CRITERIA = {
        'upvotes': True,           # Include upvote validation
        'mentions': True,          # Include mention count
        'revenue_proof': True,     # Include competitor revenue data
        'competition': True,       # Include competitor count analysis
        'build_complexity': True,  # Include complexity assessment
        'b2b_focus': True,         # Include B2B focus check
        'engagement_signals': True, # Include comments, shares, etc.
    }

    def __init__(self, db: Session):
        """Initialize scoring service.

        Args:
            db: Database session
        """
        self.db = db
        self.weights = self._load_weights()
        self.thresholds = self._load_thresholds()
        self.enabled_criteria = self._load_enabled_criteria()

    def _load_weights(self) -> dict[str, float]:
        """Load scoring weights from database or use defaults.

        Returns:
            Dict of criterion -> weight
        """
        settings = self.db.query(SystemSettings).filter(
            SystemSettings.key == 'scoring_weights'
        ).first()

        if settings and settings.value:
            return settings.value
        return self.DEFAULT_WEIGHTS.copy()

    def _load_thresholds(self) -> dict[str, int]:
        """Load validation thresholds from database or use defaults.

        Returns:
            Dict of threshold -> value
        """
        settings = self.db.query(SystemSettings).filter(
            SystemSettings.key == 'validation_thresholds'
        ).first()

        if settings and settings.value:
            return settings.value
        return self.DEFAULT_THRESHOLDS.copy()

    def _load_enabled_criteria(self) -> dict[str, bool]:
        """Load enabled criteria from database or use defaults.

        Returns:
            Dict of criterion -> enabled status
        """
        settings = self.db.query(SystemSettings).filter(
            SystemSettings.key == 'enabled_criteria'
        ).first()

        if settings and settings.value:
            return settings.value
        return self.DEFAULT_ENABLED_CRITERIA.copy()

    def update_weights(self, weights: dict[str, float]) -> dict[str, Any]:
        """Update scoring weights in database.

        Args:
            weights: New weight values (must sum to 1.0)

        Returns:
            Updated weights
        """
        # Validate weights sum to 1.0
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

        # Update in database
        settings = self.db.query(SystemSettings).filter(
            SystemSettings.key == 'scoring_weights'
        ).first()

        if settings:
            settings.value = weights
        else:
            settings = SystemSettings(
                key='scoring_weights',
                value=weights
            )
            self.db.add(settings)

        self.db.commit()
        self.weights = weights

        return weights

    def update_thresholds(self, thresholds: dict[str, int]) -> dict[str, int]:
        """Update validation thresholds in database.

        Args:
            thresholds: New threshold values

        Returns:
            Updated thresholds
        """
        # Update in database
        settings = self.db.query(SystemSettings).filter(
            SystemSettings.key == 'validation_thresholds'
        ).first()

        if settings:
            settings.value = thresholds
        else:
            settings = SystemSettings(
                key='validation_thresholds',
                value=thresholds
            )
            self.db.add(settings)

        self.db.commit()
        self.thresholds = thresholds

        return thresholds

    def update_enabled_criteria(self, criteria: dict[str, bool]) -> dict[str, bool]:
        """Update enabled scoring criteria in database.

        Args:
            criteria: Dict of criterion -> enabled status

        Returns:
            Updated enabled criteria
        """
        # Update in database
        settings = self.db.query(SystemSettings).filter(
            SystemSettings.key == 'enabled_criteria'
        ).first()

        if settings:
            settings.value = criteria
        else:
            settings = SystemSettings(
                key='enabled_criteria',
                value=criteria
            )
            self.db.add(settings)

        self.db.commit()
        self.enabled_criteria = criteria

        return criteria

    def calculate_score(self, opportunity: Opportunity) -> dict[str, Any]:
        """Calculate score for an opportunity.

        Args:
            opportunity: Opportunity model instance

        Returns:
            Dict with score and breakdown
        """
        # Get competitors
        competitors = self.db.query(Competitor).filter(
            Competitor.opportunity_id == opportunity.id
        ).all()

        # Calculate component scores
        demand_score = self._calculate_demand_score(opportunity)
        revenue_score = self._calculate_revenue_score(competitors)
        competition_score = self._calculate_competition_score(len(competitors))
        complexity_score = self._calculate_complexity_score(opportunity)

        # Weighted sum
        total_score = (
            demand_score * self.weights['demand_frequency'] +
            revenue_score * self.weights['revenue_proof'] +
            competition_score * self.weights['competition'] +
            complexity_score * self.weights['build_complexity']
        )

        # Round to integer and clamp to 0-100
        total_score = round(min(100, max(0, total_score)))

        return {
            'score': total_score,
            'breakdown': {
                'demand_score': round(demand_score),
                'revenue_score': round(revenue_score),
                'competition_score': round(competition_score),
                'complexity_score': round(complexity_score)
            }
        }

    def _calculate_demand_score(self, opportunity: Opportunity) -> float:
        """Calculate demand score based on mentions.

        Args:
            opportunity: Opportunity instance

        Returns:
            Score 0-100
        """
        mentions = opportunity.mention_count or 0

        # Scale: 100 mentions = 100 score, logarithmic after that
        if mentions <= 100:
            return float(mentions)
        else:
            # Logarithmic scaling for high mention counts
            return 100 + (math.log(mentions) - math.log(100)) * 10

    def _calculate_revenue_score(self, competitors: list) -> float:
        """Calculate revenue proof score.

        Args:
            competitors: List of competitor models

        Returns:
            Score 0-100
        """
        if not competitors:
            return 0.0

        # Check for revenue data
        has_revenue = 0
        total_mrr = 0

        for comp in competitors:
            if comp.revenue_est:
                has_revenue += 1
                # Extract MRR from revenue estimate
                mrr = self._extract_mrr(comp.revenue_est)
                if mrr:
                    total_mrr += mrr

        # Base score from having revenue data
        revenue_ratio = has_revenue / len(competitors)
        base_score = revenue_ratio * 50

        # Bonus for high MRR
        if total_mrr >= 10000:  # £10k+ MRR
            base_score += 50
        elif total_mrr >= 5000:  # £5k+ MRR
            base_score += 40
        elif total_mrr >= 1000:  # £1k+ MRR
            base_score += 25

        return min(100.0, base_score)

    def _calculate_competition_score(self, competitor_count: int) -> float:
        """Calculate competition score (inverted - fewer is better).

        Args:
            competitor_count: Number of competitors

        Returns:
            Score 0-100
        """
        if competitor_count == 0:
            return 100.0  # No competition is great
        elif competitor_count == 1:
            return 80.0
        elif competitor_count <= 3:
            return 60.0
        elif competitor_count <= 5:
            return 40.0
        elif competitor_count <= 10:
            return 20.0
        else:
            return 10.0  # Saturated market

    def _calculate_complexity_score(self, opportunity: Opportunity) -> float:
        """Calculate build complexity score (lower complexity = higher score).

        Args:
            opportunity: Opportunity instance

        Returns:
            Score 0-100
        """
        # Keyword-based complexity assessment
        title_lower = opportunity.title.lower() if opportunity.title else ''
        desc_lower = opportunity.description.lower() if opportunity.description else ''
        combined = title_lower + ' ' + desc_lower

        # High complexity keywords (lower score)
        high_complexity = ['ai', 'machine learning', 'ml', 'algorithm', 'blockchain',
                          'ar', 'vr', 'computer vision', 'nlp', 'natural language']

        # Medium complexity keywords
        med_complexity = ['api', 'integration', 'database', 'real-time',
                         'streaming', 'infrastructure']

        # Low complexity keywords (higher score)
        low_complexity = ['dashboard', 'admin panel', 'crud', 'form',
                         'listing', 'directory', 'calculator', 'template']

        # Count matches
        high_count = sum(1 for kw in high_complexity if kw in combined)
        med_count = sum(1 for kw in med_complexity if kw in combined)
        low_count = sum(1 for kw in low_complexity if kw in combined)

        # Calculate score
        score = 50.0  # Base score

        score -= high_count * 15  # Penalty for high complexity
        score -= med_count * 5   # Small penalty for medium
        score += low_count * 10   # Bonus for low complexity

        return min(100.0, max(0.0, score))

    def _extract_mrr(self, revenue_str: str) -> int | None:
        """Extract MRR from revenue string.

        Args:
            revenue_str: Revenue estimate string

        Returns:
            MRR value or None
        """
        # Pattern: $X,XXX MRR or £X,XXX/month
        patterns = [
            r'\$?([\d,]+)\s*MRR',
            r'\$?([\d,]+)\/month',
            r'£?([\d,]+)\/month',
            r'MRR\s*\$?([\d,]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, revenue_str, re.IGNORECASE)
            if match:
                value = match.group(1).replace(',', '')
                try:
                    return int(value)
                except ValueError:
                    continue

        return None

    def check_validation(self, opportunity: Opportunity, competitors: list) -> bool:
        """Check if opportunity meets validation criteria.

        Args:
            opportunity: Opportunity instance
            competitors: List of competitors

        Returns:
            True if validated
        """
        # Must have at least 1 competitor
        if len(competitors) < self.thresholds['min_competitors']:
            return False

        # Must have minimum mentions
        if (opportunity.mention_count or 0) < self.thresholds['min_mentions']:
            return False

        # Must have revenue proof
        has_revenue = any(comp.revenue_est for comp in competitors)
        if not has_revenue:
            return False

        # Extract and check MRR threshold
        total_mrr = 0
        for comp in competitors:
            if comp.revenue_est:
                mrr = self._extract_mrr(comp.revenue_est)
                if mrr:
                    total_mrr += mrr

        if total_mrr < self.thresholds['min_revenue_mrr']:
            return False

        # Check B2B focus (keyword heuristics)
        if not self._is_b2b(opportunity):
            return False

        return True

    def _is_b2b(self, opportunity: Opportunity) -> bool:
        """Check if opportunity appears to be B2B.

        Args:
            opportunity: Opportunity instance

        Returns:
            True if likely B2B
        """
        title_lower = opportunity.title.lower() if opportunity.title else ''
        desc_lower = opportunity.description.lower() if opportunity.description else ''
        target_lower = opportunity.target_market.lower() if opportunity.target_market else ''
        combined = title_lower + ' ' + desc_lower + ' ' + target_lower

        # B2B keywords
        b2b_keywords = ['business', 'company', 'enterprise', 'startup', 'saas',
                       'team', 'professional', 'workflow', 'productivity',
                       'analytics', 'automation', 'integration', 'api']

        # B2C keywords
        b2c_keywords = ['personal', 'individual', 'consumer', 'lifestyle', 'fitness',
                       'health', 'recipe', 'gaming', 'social', 'dating']

        b2b_count = sum(1 for kw in b2b_keywords if kw in combined)
        b2c_count = sum(1 for kw in b2c_keywords if kw in combined)

        return b2b_count >= b2c_count and b2b_count > 0

    def get_recommendation(self, score: int, is_validated: bool) -> str:
        """Get build/no-build recommendation.

        Args:
            score: Opportunity score (0-100)
            is_validated: Whether opportunity is validated

        Returns:
            Recommendation string
        """
        if score >= 80:
            if is_validated:
                return "Build immediately - All signals green, revenue proof confirmed"
            else:
                return "Strong candidate - validate with landing page before building"
        elif score >= 60:
            if is_validated:
                return "Strong candidate - validate with landing page before building"
            else:
                return "Promising but needs validation - test with landing page first"
        elif score >= 40:
            return "High risk - need unique angle, proceed with caution"
        elif score >= 20:
            return "Reject - insufficient validation, do not build"
        else:
            return "Reject - minimal data, do not build"

    def score_opportunity(self, opportunity_id: str) -> dict[str, Any]:
        """Score an opportunity and update database.

        Args:
            opportunity_id: Opportunity ID

        Returns:
            Scoring results
        """
        opportunity = self.db.query(Opportunity).filter(
            Opportunity.id == opportunity_id
        ).first()

        if not opportunity:
            raise ValueError("Opportunity not found")

        # Calculate score
        result = self.calculate_score(opportunity)

        # Get competitors for validation check
        competitors = self.db.query(Competitor).filter(
            Competitor.opportunity_id == opportunity_id
        ).all()

        # Check validation
        is_validated = self.check_validation(opportunity, competitors)

        # Get recommendation
        recommendation = self.get_recommendation(result['score'], is_validated)

        # Update opportunity
        opportunity.score = result['score']
        opportunity.problem_score = result['breakdown']['demand_score']
        opportunity.feasibility_score = result['breakdown']['complexity_score']
        opportunity.why_now_score = result['breakdown']['competition_score']
        opportunity.is_validated = is_validated
        opportunity.competitor_count = len(competitors)

        self.db.commit()

        return {
            **result,
            'is_validated': is_validated,
            'recommendation': recommendation
        }

    def rescore_all(self) -> dict[str, Any]:
        """Rescore all opportunities (e.g., after weight change).

        Returns:
            Summary of rescored opportunities
        """
        opportunities = self.db.query(Opportunity).all()

        summary = {
            'total': len(opportunities),
            'rescored': 0,
            'validated': 0,
            'avg_score': 0.0
        }

        total_score = 0

        for opp in opportunities:
            try:
                result = self.score_opportunity(opp.id)
                summary['rescored'] += 1
                total_score += result['score']
                if result['is_validated']:
                    summary['validated'] += 1
            except Exception as e:
                print(f"Error scoring opportunity {opp.id}: {e}")

        if summary['rescored'] > 0:
            summary['avg_score'] = round(total_score / summary['rescored'], 2)

        return summary

    def get_scoring_config(self) -> dict[str, Any]:
        """Get current scoring configuration.

        Returns:
            Current weights, thresholds, and enabled criteria
        """
        return {
            'weights': self.weights,
            'thresholds': self.thresholds,
            'enabled_criteria': self.enabled_criteria
        }
