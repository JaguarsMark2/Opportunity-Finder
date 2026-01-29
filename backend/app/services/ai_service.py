"""AI Service for analyzing pain points and clustering opportunities.

Uses LLM to:
1. Extract core pain point from posts
2. Generate opportunity names
3. Cluster similar pain points
4. Assess if it's a valid software opportunity
"""

import copy
import json
import os
from typing import Any

import requests
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models import SystemSettings


# Default API URLs per provider
PROVIDER_DEFAULTS: dict[str, dict[str, str]] = {
    'glm': {
        'model': 'glm-4-flash',
        'api_url': 'https://api.z.ai/api/paas/v4/chat/completions',
    },
    'openai': {
        'model': 'gpt-4o-mini',
        'api_url': 'https://api.openai.com/v1/chat/completions',
    },
    'anthropic': {
        'model': 'claude-3-haiku-20240307',
        'api_url': 'https://api.anthropic.com/v1/messages',
    },
}

# Domain patterns used to verify a stored URL matches a provider
_PROVIDER_DOMAINS: dict[str, list[str]] = {
    'glm': ['bigmodel.cn', 'z.ai'],
    'openai': ['openai.com'],
    'anthropic': ['anthropic.com'],
}


class AIService:
    """Service for AI-powered opportunity analysis."""

    SETTINGS_KEY = 'ai_config'

    # Default prompts
    EXTRACT_OPPORTUNITY_PROMPT = """Analyze this post for market opportunity signals.

Look for ANY of these signal types:
- Pain points: frustrations, complaints about current tools
- Feature requests: "I wish", "looking for", "does anyone know a tool that..."
- Workarounds: "I ended up building", "my hack for this", "wrote a script to..."
- Integration gaps: "need X to talk to Y", "no way to connect"
- Manual process complaints: spending hours on repetitive tasks
- Idea discussions: "someone should build", "why doesn't X exist"
- Willingness to pay: "I'd pay for", "paying $X/month for a mediocre..."
- Building in public: someone built a solution, proving the gap exists
{signal_context}
Post Title: {title}
Post Content: {content}

Respond in JSON format:
{{
    "is_software_opportunity": true/false,
    "pain_point": "Brief description of the core need/gap/idea (max 50 words)",
    "opportunity_name": "Short name for a potential solution (3-6 words, like 'LLM Database Access Manager')",
    "signal_type": "One of: pain_point, feature_request, workaround, integration_gap, idea, willingness_to_pay, manual_process",
    "category": "One of: developer_tools, productivity, automation, analytics, communication, security, infrastructure, other",
    "rejection_reason": "If not a software opportunity, explain why (otherwise null)"
}}

Mark as software opportunity if someone could build a SaaS/tool/integration to address it.
Reject: job posts, political discussions, general questions, hardware issues, non-actionable complaints."""

    CLUSTER_PROMPT = """Given these pain points, identify which ones are essentially the same problem.

Pain points:
{pain_points}

Group them by similarity. Respond in JSON:
{{
    "clusters": [
        {{
            "name": "Opportunity name for this cluster",
            "pain_point": "Core pain point description",
            "post_ids": ["id1", "id2"],
            "confidence": 0.0-1.0
        }}
    ]
}}"""

    MATCH_OPPORTUNITIES_PROMPT = """You are matching new posts against existing known opportunities.

Existing opportunities (these already exist in our database):
{existing_opportunities}

New posts to match:
{new_posts}

For each new post, determine if it describes the SAME core problem as any existing opportunity.
Only match if the pain point is essentially the same problem — not just the same category.

Respond in JSON:
{{
    "matches": [
        {{
            "post_id": "the new post ID",
            "opportunity_id": "the matching existing opportunity ID",
            "confidence": 0.0-1.0
        }}
    ],
    "unmatched_post_ids": ["id1", "id2"]
}}

Rules:
- Only match with confidence >= 0.7
- A post should match at most ONE opportunity
- If no good match exists, put the post_id in unmatched_post_ids
- Be strict: similar category is NOT enough, the core problem must be the same"""

    def __init__(self, db: Session):
        """Initialize AI service."""
        self.db = db
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load AI configuration from database.

        Returns a deep copy so callers can mutate without affecting
        the SQLAlchemy-tracked object (which would prevent change detection).
        """
        settings = self.db.query(SystemSettings).filter(
            SystemSettings.key == self.SETTINGS_KEY
        ).first()

        if settings and settings.value:
            config = copy.deepcopy(settings.value)
            # Migrate old single api_key format to per-provider api_keys
            if 'api_key' in config and 'api_keys' not in config:
                old_key = config.pop('api_key')
                provider = config.get('provider', 'glm')
                config['api_keys'] = {provider: old_key}
                # Persist migration via ORM (not bulk .update() which
                # gets overwritten by ORM flush of the stale object)
                settings.value = copy.deepcopy(config)
                flag_modified(settings, 'value')
                self.db.commit()
            return config

        return {
            'provider': 'glm',
            'api_keys': {},
            'model': 'glm-4-flash',
            'api_url': 'https://api.z.ai/api/paas/v4/chat/completions',
            'enabled': False
        }

    def _get_api_key(self, provider: str | None = None) -> str:
        """Get the API key for the given or current provider."""
        provider = provider or self.config.get('provider', 'glm')
        api_keys = self.config.get('api_keys', {})
        # Backward compat: check old single key field
        if not api_keys and self.config.get('api_key'):
            return self.config['api_key']
        return api_keys.get(provider, '')

    def _get_provider_url(self, provider: str) -> str:
        """Get the API URL for a provider.

        Uses the stored api_url only if it matches the provider's known
        domains. Otherwise falls back to the provider's default URL.
        This prevents cross-provider URL contamination when switching.
        """
        stored_url = self.config.get('api_url', '')
        default_url = PROVIDER_DEFAULTS.get(provider, {}).get('api_url', '')

        if not stored_url:
            return default_url

        # Only use stored URL if it belongs to this provider
        domains = _PROVIDER_DOMAINS.get(provider, [])
        if any(domain in stored_url for domain in domains):
            return stored_url

        return default_url

    def save_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Save AI configuration to database."""
        settings = self.db.query(SystemSettings).filter(
            SystemSettings.key == self.SETTINGS_KEY
        ).first()

        if settings:
            settings.value = copy.deepcopy(config)
            flag_modified(settings, 'value')
        else:
            settings = SystemSettings(
                key=self.SETTINGS_KEY,
                value=config
            )
            self.db.add(settings)

        self.db.commit()
        self.config = config
        return config

    def get_config(self) -> dict[str, Any]:
        """Get current AI configuration (without exposing full API keys).

        Returns masked key info for the CURRENT provider only.
        """
        config = self.config.copy()
        provider = config.get('provider', 'glm')

        # Get key for current provider
        api_key = self._get_api_key(provider)

        if api_key:
            config['api_key_masked'] = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            config['api_key_set'] = True
        else:
            config['api_key_masked'] = ''
            config['api_key_set'] = False

        # Ensure api_url is present (use provider default if missing)
        if not config.get('api_url'):
            config['api_url'] = PROVIDER_DEFAULTS.get(provider, {}).get('api_url', '')

        # Remove raw keys from response
        config.pop('api_keys', None)
        config.pop('api_key', None)

        return config

    def is_configured(self) -> bool:
        """Check if AI service is properly configured."""
        return bool(self._get_api_key()) and self.config.get('enabled', False)

    def _call_llm(self, prompt: str) -> str | None:
        """Call the configured LLM API."""
        if not self.is_configured():
            print("AI Service not configured")
            return None

        provider = self.config.get('provider', 'glm')
        api_key = self._get_api_key()
        model = self.config.get('model', 'glm-4-flash')

        try:
            if provider == 'glm':
                return self._call_glm(prompt, api_key, model)
            elif provider == 'openai':
                return self._call_openai(prompt, api_key, model)
            elif provider == 'anthropic':
                return self._call_anthropic(prompt, api_key, model)
            else:
                print(f"Unknown AI provider: {provider}")
                return None
        except Exception as e:
            print(f"AI API error: {e}")
            return None

    def _call_glm(self, prompt: str, api_key: str, model: str) -> str | None:
        """Call Zhipu GLM API (BigModel or Z.ai)."""
        url = self._get_provider_url('glm')

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': model,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 1000
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        return data['choices'][0]['message']['content']

    def _call_openai(self, prompt: str, api_key: str, model: str) -> str | None:
        """Call OpenAI API."""
        url = self._get_provider_url('openai')

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': model or 'gpt-4o-mini',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 1000
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        return data['choices'][0]['message']['content']

    def _call_anthropic(self, prompt: str, api_key: str, model: str) -> str | None:
        """Call Anthropic Claude API."""
        url = self._get_provider_url('anthropic')

        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }

        payload = {
            'model': model or 'claude-3-haiku-20240307',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 1000
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        return data['content'][0]['text']

    def analyze_post(
        self,
        title: str,
        content: str,
        signal_phrases: str = '',
    ) -> dict[str, Any] | None:
        """Analyze a single post for market opportunity signals.

        Args:
            title: Post title
            content: Post content (truncated to 2000 chars)
            signal_phrases: Optional formatted signal phrases to include in prompt

        Returns:
            Dict with pain_point, opportunity_name, category,
            is_software_opportunity, signal_type — or None if analysis fails
        """
        signal_context = ''
        if signal_phrases:
            signal_context = (
                f"\nAlso look for these specific phrases/patterns the user "
                f"has flagged as important signals: {signal_phrases}\n"
            )

        prompt = self.EXTRACT_OPPORTUNITY_PROMPT.format(
            title=title,
            content=content[:2000],
            signal_context=signal_context,
        )

        response = self._call_llm(prompt)
        if not response:
            return None

        return self._parse_json_response(response)

    def cluster_pain_points(self, pain_points: list[dict]) -> list[dict]:
        """Cluster similar pain points together.

        Args:
            pain_points: List of dicts with 'id', 'pain_point', 'title'

        Returns:
            List of clusters with aggregated data
        """
        if not pain_points:
            return []

        # Format pain points for prompt
        formatted = "\n".join([
            f"ID: {p['id']}\nPain: {p['pain_point']}\nTitle: {p.get('title', '')}\n"
            for p in pain_points
        ])

        prompt = self.CLUSTER_PROMPT.format(pain_points=formatted)
        response = self._call_llm(prompt)

        if not response:
            # Fallback: treat each as its own cluster (single-item)
            return [
                {
                    'name': p.get('opportunity_name', p['pain_point'][:50]),
                    'pain_point': p['pain_point'],
                    'post_ids': [p['id']],
                    'confidence': 0.5
                }
                for p in pain_points
            ]

        data = self._parse_json_response(response)
        if not data:
            # Fallback on parse failure
            return [
                {
                    'name': p.get('opportunity_name', p['pain_point'][:50]),
                    'pain_point': p['pain_point'],
                    'post_ids': [p['id']],
                    'confidence': 0.5
                }
                for p in pain_points
            ]

        return data.get('clusters', [])

    def _parse_json_response(self, response: str) -> dict | None:
        """Parse a JSON response from the LLM, handling markdown code blocks.

        Args:
            response: Raw LLM response string

        Returns:
            Parsed dict or None if parsing fails
        """
        try:
            cleaned = response
            if '```json' in cleaned:
                cleaned = cleaned.split('```json')[1].split('```')[0]
            elif '```' in cleaned:
                cleaned = cleaned.split('```')[1].split('```')[0]

            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            print(f"Failed to parse AI JSON response: {e}")
            print(f"Response was: {response[:500]}")
            return None

    def match_to_opportunities(
        self,
        posts: list[dict],
        opportunities: list[dict],
    ) -> dict[str, Any]:
        """Match pending posts against existing Opportunities.

        Uses AI to determine if any new posts describe the same core
        problem as existing Opportunities in the database.

        Args:
            posts: List of dicts with 'id', 'pain_point', 'title'
            opportunities: List of dicts with 'id', 'title', 'description'

        Returns:
            Dict with 'matches' (list of {post_id, opportunity_id, confidence})
            and 'unmatched_post_ids' (list of post IDs that didn't match)
        """
        if not posts or not opportunities:
            return {
                'matches': [],
                'unmatched_post_ids': [p['id'] for p in posts],
            }

        # Format existing opportunities
        formatted_opps = "\n".join([
            f"OPP_ID: {o['id']}\nTitle: {o['title']}\nProblem: {o.get('description', '')}\n"
            for o in opportunities
        ])

        # Format new posts
        formatted_posts = "\n".join([
            f"POST_ID: {p['id']}\nTitle: {p.get('title', '')}\nPain: {p['pain_point']}\n"
            for p in posts
        ])

        prompt = self.MATCH_OPPORTUNITIES_PROMPT.format(
            existing_opportunities=formatted_opps,
            new_posts=formatted_posts,
        )

        response = self._call_llm(prompt)
        if not response:
            # No response — treat all as unmatched
            return {
                'matches': [],
                'unmatched_post_ids': [p['id'] for p in posts],
            }

        data = self._parse_json_response(response)
        if not data:
            return {
                'matches': [],
                'unmatched_post_ids': [p['id'] for p in posts],
            }

        # Filter matches to confidence >= 0.7
        matches = [
            m for m in data.get('matches', [])
            if m.get('confidence', 0) >= 0.7
        ]

        # Build unmatched list from what wasn't matched
        matched_post_ids = {m['post_id'] for m in matches}
        unmatched = [p['id'] for p in posts if p['id'] not in matched_post_ids]

        return {
            'matches': matches,
            'unmatched_post_ids': unmatched,
        }

    def test_connection(self) -> dict[str, Any]:
        """Test the AI API connection.

        Reloads config from database to ensure latest saved settings.
        Bypasses the 'enabled' check so users can test their API key
        before enabling AI analysis.
        """
        # Reload to pick up any changes saved by a prior request
        self.config = self._load_config()

        provider = self.config.get('provider', 'glm')
        api_key = self._get_api_key(provider)

        if not api_key:
            return {
                'success': False,
                'message': f'No API key set for {provider}. Save your API key first.'
            }

        model = self.config.get('model', PROVIDER_DEFAULTS.get(provider, {}).get('model', ''))
        url = self._get_provider_url(provider)
        prompt = "Say 'OK' if you can read this."

        # Log diagnostic info to server console
        key_preview = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "***"
        print(f"[AI Test] provider={provider}, model={model}, url={url}, key={key_preview}")

        try:
            # Call provider directly, bypassing is_configured() check
            if provider == 'glm':
                response = self._call_glm(prompt, api_key, model)
            elif provider == 'openai':
                response = self._call_openai(prompt, api_key, model)
            elif provider == 'anthropic':
                response = self._call_anthropic(prompt, api_key, model)
            else:
                return {
                    'success': False,
                    'message': f'Unknown AI provider: {provider}'
                }

            if response:
                return {
                    'success': True,
                    'message': f'Connected to {provider} ({model}) via {url}. Response: {response[:100]}'
                }
            else:
                return {
                    'success': False,
                    'message': f'No response from {provider} ({model}) at {url}'
                }

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else 'unknown'
            try:
                body = e.response.json() if e.response is not None else {}
                error_msg = body.get('error', {}).get('message', '') or body.get('msg', '') or str(body)
            except Exception:
                error_msg = str(e)
            return {
                'success': False,
                'message': f'HTTP {status_code} from {url} (model={model}): {error_msg[:200]}'
            }

        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'message': f'Cannot connect to {url}. If using GLM, try switching the API URL to https://api.z.ai/api/paas/v4/chat/completions (international endpoint).'
            }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': f'Connection to {url} timed out (30s). Try again or switch to the international endpoint (api.z.ai).'
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Connection failed ({url}): {type(e).__name__}: {str(e)}'
            }
