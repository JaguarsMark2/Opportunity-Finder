"""Data collector service for orchestrating all collectors.

Implements a consensus-based pipeline: posts are analyzed by AI and held
as PendingPosts until multiple posts describe the same problem.  Only
then are they promoted to Opportunities with SourceLinks.
"""

import os
import re
import sys
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Callable

from sqlalchemy.orm import Session

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.collectors import BaseCollector, get_available_collectors, get_enabled_collectors
from app.collectors.microns_collector import MicronsCollector
from app.models import Opportunity, PendingPost, Scan, SourceLink, SystemSettings
from app.services.ai_service import AIService

# Minimum number of posts describing the same problem before we create
# an Opportunity.  This prevents storing every random post.
MIN_CONSENSUS_POSTS = 2

# How long pending posts are kept before being expired (days).
PENDING_POST_TTL_DAYS = 30

# Maximum number of existing Opportunities to compare against in one
# AI matching call (keeps token usage reasonable).
MAX_MATCH_OPPORTUNITIES = 50

# Maximum pending posts to cluster in one AI call.
MAX_CLUSTER_BATCH = 80


class DataCollectorService:
    """Service for orchestrating data collection from all sources.

    This service manages data collection from multiple sources, handles
    deduplication, and stores results in the database.

    New sources can be added by:
    1. Creating a new collector class extending BaseCollector
    2. Using the @register_collector decorator
    3. Adding the source name to the enabled_sources config

    Example:
        # Run scan with specific sources
        service = DataCollectorService(db, config)
        result = service.run_scan(sources=['reddit', 'hacker_news'])

        # Run scan with all enabled sources
        result = service.run_scan()
    """

    def __init__(self, db: Session, config: dict[str, Any] | None = None):
        """Initialize data collector service.

        Args:
            db: Database session
            config: Configuration for collectors including:
                - enabled_sources: List of source names to enable
                - reddit: Config for Reddit collector
                - product_hunt: Config for Product Hunt collector
                - google_trends: Config for Google Trends collector
                - etc. (one key per source)
        """
        self.db = db
        self.config = config or {}

        # Get enabled sources from config or use all available
        self.enabled_sources = get_enabled_collectors(self.config)

        # Initialize collectors
        self.collectors = self._initialize_collectors()

        # Initialize AI service
        self.ai_service = AIService(db)

        # Load filter rules
        self.filter_rules = self._load_filter_rules()

    def _load_filter_rules(self) -> dict[str, Any]:
        """Load filter rules from database."""
        settings = self.db.query(SystemSettings).filter(
            SystemSettings.key == 'filter_rules'
        ).first()

        if settings and settings.value:
            rules = settings.value
            # Ensure signal_phrases exists (migration)
            rules.setdefault('signal_phrases', [])
            return rules

        # Default filter rules
        return {
            'exclude_keywords': [
                'hiring', 'job', 'career', 'salary', 'remote work',
                'who is hiring', 'seeking freelancer', 'looking for developer'
            ],
            'signal_phrases': [],
            'require_keywords': [],
            'min_upvotes': 5,
            'min_comments': 2,
            'exclude_categories': ['job_posting', 'promotional'],
            'custom_rules': [],
        }

    def _passes_filter_rules(self, opp_data: dict[str, Any]) -> tuple[bool, str | None]:
        """Check if an opportunity passes the filter rules.

        Posts containing signal phrases get a pass on engagement
        thresholds, because a low-upvote post that says "I wish
        someone would build X" is still valuable signal.

        Args:
            opp_data: Opportunity data dict

        Returns:
            Tuple of (passes, rejection_reason)
        """
        title = opp_data.get('title', '').lower()
        description = opp_data.get('description', '').lower()
        text = f"{title} {description}"
        engagement = opp_data.get('engagement_metrics', {})

        # Check exclude keywords against title only — a post body might
        # mention "hiring" or "job" in passing while still being a valid
        # opportunity discussion.
        for keyword in self.filter_rules.get('exclude_keywords', []):
            if keyword.lower() in title:
                return False, f"Title contains excluded keyword: {keyword}"

        # Check required keywords (if any specified, at least one must match)
        require_keywords = self.filter_rules.get('require_keywords', [])
        if require_keywords:
            found = any(kw.lower() in text for kw in require_keywords)
            if not found:
                return False, "Missing required keywords"

        # Check if post contains any signal phrases
        has_signal = self._contains_signal_phrase(text)

        # Check minimum engagement — but signal phrases bypass this
        if not has_signal:
            upvotes = engagement.get('upvotes', 0) or engagement.get('points', 0) or 0
            comments = engagement.get('comments', 0) or 0
            min_upvotes = self.filter_rules.get('min_upvotes', 5)
            min_comments = self.filter_rules.get('min_comments', 2)

            if upvotes < min_upvotes:
                return False, f"Below minimum upvotes ({upvotes} < {min_upvotes})"

            if comments < min_comments:
                return False, f"Below minimum comments ({comments} < {min_comments})"

        # Check custom rules (always enforced)
        for rule in self.filter_rules.get('custom_rules', []):
            rule_type = rule.get('type', '')
            rule_value = rule.get('value', '').lower()

            if rule_type == 'exclude_phrase' and rule_value in text:
                return False, f"Matches custom rule: {rule.get('reason', rule_value)}"

            if rule_type == 'exclude_regex':
                try:
                    if re.search(rule_value, text, re.IGNORECASE):
                        return False, f"Matches regex rule: {rule.get('reason', rule_value)}"
                except re.error:
                    pass  # Invalid regex, skip

        return True, None

    def _contains_signal_phrase(self, text: str) -> bool:
        """Check if text contains any configured signal phrases.

        Args:
            text: Lowercased text to check

        Returns:
            True if any signal phrase is found
        """
        for sp in self.filter_rules.get('signal_phrases', []):
            phrase = sp['phrase'] if isinstance(sp, dict) else sp
            if phrase.lower() in text:
                return True
        return False

    def _get_signal_phrases_for_prompt(self) -> str:
        """Format signal phrases for inclusion in the AI prompt.

        Returns:
            Formatted string of signal phrases, or empty string if none.
        """
        phrases = self.filter_rules.get('signal_phrases', [])
        if not phrases:
            return ''

        formatted = [
            sp['phrase'] if isinstance(sp, dict) else sp
            for sp in phrases
        ]
        return ', '.join(f'"{p}"' for p in formatted)

    def _initialize_collectors(self) -> dict[str, BaseCollector]:
        """Initialize all enabled collectors.

        Returns:
            Dict of collector instances
        """
        collectors = {}

        for source_name in self.enabled_sources:
            try:
                # Get source-specific config
                source_config = self.config.get(source_name, {})
                source_config['collector_config'] = self.config.get('collector_config', {})

                # Create collector instance
                collector = BaseCollector.create_collector(source_name, source_config)

                # Only add if enabled and valid
                if collector.is_enabled():
                    is_valid, missing = collector.validate_config()
                    if is_valid:
                        collectors[source_name] = collector
                    else:
                        print(f"Collector {source_name} missing config: {missing}")
                else:
                    print(f"Collector {source_name} is disabled")

            except Exception as e:
                print(f"Error initializing {source_name} collector: {e}")
                continue

        return collectors

    def get_available_sources(self) -> list[str]:
        """Get list of all available sources.

        Returns:
            List of source names
        """
        return list(get_available_collectors().keys())

    def get_enabled_sources(self) -> list[str]:
        """Get list of currently enabled sources.

        Returns:
            List of enabled source names
        """
        return list(self.collectors.keys())

    def add_source(self, source_name: str, source_config: dict[str, Any] | None = None) -> bool:
        """Add a new source to the service.

        This allows dynamically adding new sources at runtime.

        Args:
            source_name: Name of the source to add
            source_config: Configuration for the source

        Returns:
            True if source was added successfully
        """
        try:
            source_config = source_config or {}
            source_config['collector_config'] = self.config.get('collector_config', {})

            collector = BaseCollector.create_collector(source_name, source_config)

            if collector.is_enabled():
                is_valid, missing = collector.validate_config()
                if not is_valid:
                    print(f"Cannot add {source_name}: missing config {missing}")
                    return False

                self.collectors[source_name] = collector
                print(f"Added source: {source_name}")
                return True
            else:
                print(f"Source {source_name} is disabled")
                return False

        except Exception as e:
            print(f"Error adding source {source_name}: {e}")
            return False

    def remove_source(self, source_name: str) -> bool:
        """Remove a source from the service.

        Args:
            source_name: Name of the source to remove

        Returns:
            True if source was removed
        """
        if source_name in self.collectors:
            del self.collectors[source_name]
            print(f"Removed source: {source_name}")
            return True
        return False

    def run_scan(
        self,
        sources: list[str] | None = None,
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> dict[str, Any]:
        """Run a consensus-based data collection scan.

        Pipeline:
        1. Collect posts from sources
        2. Deduplicate against SourceLinks AND PendingPosts
        3. Filter (keyword / engagement rules)
        4. AI analyze each post (extract pain point, check if software opp)
        5. Store surviving posts as PendingPosts
        6. Match ALL pending posts against existing Opportunities
           (promote matches → SourceLinks, delete from pending)
        7. Cluster remaining pending posts
           (2+ post clusters → new Opportunity + SourceLinks, delete from pending)
           (singles stay pending for future scans)
        8. Expire old pending posts that never clustered

        Args:
            sources: List of sources to scan (None = all enabled)
            progress_callback: Optional (progress_pct, message) callback

        Returns:
            Scan results with counts
        """
        if sources is None:
            sources = list(self.collectors.keys())

        sources = [s for s in sources if s in self.collectors]

        def _report(pct: int, msg: str) -> None:
            """Report progress if callback is provided."""
            print(f"[Scan] [{pct}%] {msg}")
            if progress_callback:
                progress_callback(pct, msg)

        # Create scan record
        scan = Scan(
            id=str(uuid.uuid4()),
            status='running',
            started_at=datetime.now(UTC),
            sources_processed={},
        )
        self.db.add(scan)
        self.db.commit()
        assert scan.sources_processed is not None

        all_results: list[Any] = []
        stats = {
            'collected': 0,
            'duplicates': 0,
            'filtered': 0,
            'ai_analyzed': 0,
            'ai_rejected': 0,
            'pending_added': 0,
            'matched_to_existing': 0,
            'new_opportunities': 0,
            'pending_remaining': 0,
            'expired': 0,
        }

        try:
            # Inject user signal phrases into collectors that support them
            signal_phrases = self.filter_rules.get('signal_phrases', [])
            for collector in self.collectors.values():
                collector.collector_config.custom_params['signal_phrases'] = signal_phrases

            # ----------------------------------------------------------
            # Phase 1: Collect raw posts from each source
            # ----------------------------------------------------------
            for source in sources:
                if source not in self.collectors:
                    continue

                _report(15, f"Collecting from {source}...")
                collector = self.collectors[source]

                if source in ['google_trends', 'microns']:
                    scan.sources_processed[source] = {
                        'status': 'skipped',
                        'count': 0,
                        'message': 'Handled separately',
                    }
                    continue

                results = collector.collect()
                all_results.extend(results)
                scan.sources_processed[source] = {
                    'status': 'completed',
                    'count': len(results),
                }
                self.db.commit()

            stats['collected'] = len(all_results)
            _report(25, f"Collected {len(all_results)} posts, enriching engagement scores...")

            # Enrich with Microns engagement scores
            microns_collector = MicronsCollector(self.config.get('microns', {}))
            enriched = microns_collector.collect([
                {
                    'title': r.title,
                    'description': r.description,
                    'url': r.url,
                    'source_type': r.source_type,
                    'engagement_metrics': r.engagement_metrics,
                }
                for r in all_results
            ])

            # ----------------------------------------------------------
            # Phase 2: Deduplicate, filter, AI analyze → PendingPosts
            # ----------------------------------------------------------
            new_pending: list[PendingPost] = []
            _report(30, f"Processing {len(enriched)} posts (dedup, filter)...")

            # First pass: dedup and filter (fast, no API calls)
            filtered_posts: list[dict[str, Any]] = []
            for opp_data in enriched:
                url = opp_data['url']

                if self._is_duplicate_url(url):
                    stats['duplicates'] += 1
                    continue

                passes, reason = self._passes_filter_rules(opp_data)
                if not passes:
                    stats['filtered'] += 1
                    continue

                filtered_posts.append(opp_data)

            total_to_analyze = len(filtered_posts)
            _report(32, f"{total_to_analyze} posts passed filters, starting AI analysis...")

            # Second pass: batch AI analysis
            BATCH_SIZE = 5
            signal_phrases = self._get_signal_phrases_for_prompt()

            for batch_start in range(0, total_to_analyze, BATCH_SIZE):
                batch = filtered_posts[batch_start:batch_start + BATCH_SIZE]
                batch_end = batch_start + len(batch)

                # Report progress: AI analysis spans 32-75%
                ai_pct = 32 + int((batch_start / max(total_to_analyze, 1)) * 43)
                _report(ai_pct, f"AI analyzing posts {batch_start + 1}-{batch_end}/{total_to_analyze}...")

                # Prepare batch results (default to no AI analysis)
                batch_analyses: list[dict[str, Any] | None] = [None] * len(batch)

                if self.ai_service.is_configured():
                    try:
                        batch_input = [
                            {'title': p['title'], 'content': p.get('description', '')}
                            for p in batch
                        ]
                        batch_analyses = self.ai_service.analyze_posts_batch(
                            batch_input, signal_phrases
                        )
                    except Exception as e:
                        print(f"[Scan] Batch AI error at {batch_start}: {e}")

                # Process each post in the batch
                for i, opp_data in enumerate(batch):
                    analysis = batch_analyses[i] if i < len(batch_analyses) else None

                    pain_point = opp_data.get('description', '')
                    opp_name = opp_data.get('title', '')
                    category = None
                    ai_analysis = None

                    if analysis:
                        stats['ai_analyzed'] += 1

                        if not analysis.get('is_software_opportunity', True):
                            stats['ai_rejected'] += 1
                            continue

                        pain_point = analysis.get('pain_point', pain_point)
                        opp_name = analysis.get('opportunity_name', opp_name)
                        category = analysis.get('category')
                        ai_analysis = analysis

                    pending = PendingPost(
                        id=str(uuid.uuid4()),
                        title=opp_data['title'],
                        description=opp_data.get('description', ''),
                        url=opp_data['url'],
                        source_type=opp_data['source_type'],
                        pain_point=pain_point,
                        opportunity_name=opp_name,
                        category=category,
                        ai_analysis=ai_analysis,
                        engagement_metrics={
                            'engagement_score': opp_data.get('engagement_score', 0),
                            'engagement_level': opp_data.get('engagement_level', 'LOW'),
                            **(opp_data.get('engagement_metrics', {})),
                        },
                        scan_id=scan.id,
                    )
                    self.db.add(pending)
                    new_pending.append(pending)
                    stats['pending_added'] += 1

            self.db.commit()

            # ----------------------------------------------------------
            # Phase 3: Match ALL pending posts against existing Opportunities
            # ----------------------------------------------------------
            _report(78, f"Matching {stats['pending_added']} pending posts against existing opportunities...")
            matched_count = self._match_pending_to_opportunities()
            stats['matched_to_existing'] = matched_count

            # ----------------------------------------------------------
            # Phase 4: Cluster remaining pending posts (consensus check)
            # ----------------------------------------------------------
            _report(85, "Clustering pending posts for consensus...")
            new_opp_count = self._cluster_pending_posts()
            stats['new_opportunities'] = new_opp_count

            # ----------------------------------------------------------
            # Phase 5: Expire old pending posts
            # ----------------------------------------------------------
            _report(92, "Expiring stale pending posts...")
            expired = self._expire_old_pending_posts()
            stats['expired'] = expired

            # Count remaining pending
            stats['pending_remaining'] = self.db.query(PendingPost).count()

            # Finalize scan
            scan.status = 'completed'
            scan.completed_at = datetime.now(UTC)
            scan.opportunities_found = stats['new_opportunities'] + stats['matched_to_existing']
            scan.progress = 100
            self.db.commit()

            print(
                f"[Scan] Complete: {stats['pending_added']} pending, "
                f"{stats['matched_to_existing']} matched existing, "
                f"{stats['new_opportunities']} new opportunities, "
                f"{stats['pending_remaining']} still pending, "
                f"{stats['expired']} expired"
            )

            return {
                'scan_id': scan.id,
                'status': 'completed',
                **stats,
                'sources': scan.sources_processed,
            }

        except Exception as e:
            scan.status = 'failed'
            scan.error_message = str(e)
            scan.completed_at = datetime.now(UTC)
            self.db.commit()
            raise

    # ------------------------------------------------------------------
    # Pipeline helpers
    # ------------------------------------------------------------------

    def _is_duplicate_url(self, url: str) -> bool:
        """Check if a URL already exists in SourceLinks or PendingPosts."""
        in_source = self.db.query(SourceLink).filter(
            SourceLink.url == url
        ).first() is not None

        if in_source:
            return True

        in_pending = self.db.query(PendingPost).filter(
            PendingPost.url == url
        ).first() is not None

        return in_pending

    def _match_pending_to_opportunities(self) -> int:
        """Match all pending posts against existing Opportunities.

        Posts that match an existing Opportunity are promoted to
        SourceLinks under that Opportunity, then removed from pending.

        Returns:
            Number of posts matched and promoted.
        """
        if not self.ai_service.is_configured():
            return 0

        all_pending = self.db.query(PendingPost).all()
        if not all_pending:
            return 0

        # Only match posts that have a pain_point (were AI-analyzed)
        analyzed_pending = [p for p in all_pending if p.pain_point]
        if not analyzed_pending:
            return 0

        # Load recent existing Opportunities to match against
        recent_cutoff = datetime.now(UTC) - timedelta(days=90)
        existing_opps = (
            self.db.query(Opportunity)
            .filter(Opportunity.created_at >= recent_cutoff)
            .order_by(Opportunity.score.desc().nullslast())
            .limit(MAX_MATCH_OPPORTUNITIES)
            .all()
        )

        if not existing_opps:
            return 0

        # Format for AI
        opp_dicts = [
            {'id': o.id, 'title': o.title, 'description': o.description or o.problem or ''}
            for o in existing_opps
        ]
        post_dicts = [
            {'id': p.id, 'title': p.title, 'pain_point': p.pain_point or ''}
            for p in analyzed_pending
        ]

        print(f"[Scan] Matching {len(post_dicts)} pending posts against {len(opp_dicts)} existing opportunities...")
        result = self.ai_service.match_to_opportunities(post_dicts, opp_dicts)

        matched_count = 0
        for match in result.get('matches', []):
            post_id = match.get('post_id')
            opp_id = match.get('opportunity_id')

            pending = self.db.query(PendingPost).filter(PendingPost.id == post_id).first()
            opp = self.db.query(Opportunity).filter(Opportunity.id == opp_id).first()

            if not pending or not opp:
                continue

            # Promote: create SourceLink under the matched Opportunity
            source_link = SourceLink(
                id=str(uuid.uuid4()),
                opportunity_id=opp.id,
                source_type=pending.source_type,
                url=pending.url,
                title=pending.title,
                engagement_metrics={
                    **(pending.engagement_metrics or {}),
                    'ai_analysis': pending.ai_analysis,
                },
                collected_at=datetime.now(UTC),
            )
            self.db.add(source_link)

            # Update Opportunity metadata
            opp.mention_count = (opp.mention_count or 0) + 1
            if pending.source_type and pending.source_type not in (opp.source_types or []):
                opp.source_types = list(set((opp.source_types or []) + [pending.source_type]))

            # Remove from pending
            self.db.delete(pending)
            matched_count += 1

        if matched_count:
            self.db.commit()
            print(f"[Scan] Matched {matched_count} posts to existing opportunities")

        return matched_count

    def _cluster_pending_posts(self) -> int:
        """Cluster remaining pending posts and promote consensus clusters.

        Only clusters with >= MIN_CONSENSUS_POSTS posts become
        Opportunities.  Singles remain as PendingPosts.

        Returns:
            Number of new Opportunities created.
        """
        if not self.ai_service.is_configured():
            return 0

        all_pending = self.db.query(PendingPost).all()
        # Only cluster posts that were properly AI-analyzed (pain_point
        # differs from raw description, meaning AI extracted something)
        analyzed = [
            p for p in all_pending
            if p.ai_analysis and p.pain_point and p.pain_point != p.description
        ]

        if len(analyzed) < MIN_CONSENSUS_POSTS:
            return 0

        to_cluster = analyzed[:MAX_CLUSTER_BATCH]

        # Use short numeric IDs in the prompt to save tokens (UUIDs are huge)
        id_map: dict[str, PendingPost] = {}  # short_id -> PendingPost
        pain_points = []
        for idx, p in enumerate(to_cluster):
            short_id = str(idx)
            id_map[short_id] = p
            pain_points.append({
                'id': short_id,
                'pain_point': p.pain_point or '',
                'title': p.title,
                'opportunity_name': p.opportunity_name or '',
            })

        print(f"[Scan] Clustering {len(pain_points)} pending posts...")
        clusters = self.ai_service.cluster_pain_points(pain_points)

        new_opp_count = 0

        for cluster in clusters:
            post_ids = cluster.get('post_ids', [])

            # Only promote clusters with consensus (2+ posts)
            if len(post_ids) < MIN_CONSENSUS_POSTS:
                continue

            confidence = cluster.get('confidence', 0)
            if confidence < 0.6:
                continue

            # Map short IDs back to PendingPost records
            cluster_posts = [id_map[pid] for pid in post_ids if pid in id_map]
            if len(cluster_posts) < MIN_CONSENSUS_POSTS:
                continue

            # Create the Opportunity
            opp_title = cluster.get('name', cluster_posts[0].opportunity_name or cluster_posts[0].title)
            opp_description = cluster.get('pain_point', cluster_posts[0].pain_point or '')
            category = cluster_posts[0].category  # Use first post's category

            # Calculate initial score from engagement
            total_engagement = 0
            source_types: set[str] = set()
            for cp in cluster_posts:
                metrics = cp.engagement_metrics or {}
                total_engagement += metrics.get('upvotes', 0) or metrics.get('points', 0) or 0
                total_engagement += metrics.get('comments', 0) or 0
                source_types.add(cp.source_type)

            initial_score = min(100, total_engagement)

            opportunity = Opportunity(
                id=str(uuid.uuid4()),
                title=opp_title,
                description=opp_description,
                problem=opp_description,
                score=initial_score,
                source_types=list(source_types),
                mention_count=len(cluster_posts),
                category=category,
                created_at=datetime.now(UTC),
            )
            self.db.add(opportunity)

            # Create SourceLinks for each post in the cluster
            for cp in cluster_posts:
                source_link = SourceLink(
                    id=str(uuid.uuid4()),
                    opportunity_id=opportunity.id,
                    source_type=cp.source_type,
                    url=cp.url,
                    title=cp.title,
                    engagement_metrics={
                        **(cp.engagement_metrics or {}),
                        'ai_analysis': cp.ai_analysis,
                    },
                    collected_at=datetime.now(UTC),
                )
                self.db.add(source_link)

                # Remove from pending
                self.db.delete(cp)

            new_opp_count += 1
            print(f"[Scan] New opportunity: '{opp_title}' ({len(cluster_posts)} posts)")

        if new_opp_count:
            self.db.commit()

        return new_opp_count

    def _expire_old_pending_posts(self) -> int:
        """Remove pending posts older than PENDING_POST_TTL_DAYS.

        Returns:
            Number of expired posts removed.
        """
        cutoff = datetime.now(UTC) - timedelta(days=PENDING_POST_TTL_DAYS)
        expired = self.db.query(PendingPost).filter(
            PendingPost.created_at < cutoff
        ).all()

        count = len(expired)
        for p in expired:
            self.db.delete(p)

        if count:
            self.db.commit()
            print(f"[Scan] Expired {count} old pending posts (>{PENDING_POST_TTL_DAYS} days)")

        return count

    def get_scan_status(self, scan_id: str) -> dict[str, Any]:
        """Get status of a scan.

        Args:
            scan_id: ID of the scan

        Returns:
            Scan status information
        """
        scan = self.db.query(Scan).filter(Scan.id == scan_id).first()

        if not scan:
            return {'error': 'Scan not found'}

        return {
            'scan_id': scan.id,
            'status': scan.status,
            'progress': scan.progress,
            'opportunities_found': scan.opportunities_found,
            'sources_processed': scan.sources_processed,
            'started_at': scan.started_at.isoformat() if scan.started_at else None,
            'completed_at': scan.completed_at.isoformat() if scan.completed_at else None,
            'error_message': scan.error_message
        }
