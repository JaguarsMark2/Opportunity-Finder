"""AI Service for analyzing pain points and clustering opportunities.

Uses LLM to:
1. Extract core pain point from posts
2. Generate opportunity names
3. Cluster similar pain points
4. Assess if it's a valid software opportunity
"""

import json
import os
from typing import Any

import requests
from sqlalchemy.orm import Session

from app.models import SystemSettings


class AIService:
    """Service for AI-powered opportunity analysis."""

    SETTINGS_KEY = 'ai_config'

    # Default prompts
    EXTRACT_PAIN_POINT_PROMPT = """Analyze this post and extract the core pain point or need.

Post Title: {title}
Post Content: {content}

Respond in JSON format:
{{
    "is_software_opportunity": true/false,
    "pain_point": "Brief description of the core pain/need (max 50 words)",
    "opportunity_name": "Short name for a solution (3-6 words, like 'LLM Database Access Manager')",
    "category": "One of: developer_tools, productivity, automation, analytics, communication, security, infrastructure, other",
    "rejection_reason": "If not a software opportunity, explain why (otherwise null)"
}}

Only mark as software opportunity if someone could build a SaaS/tool to solve it.
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

    def __init__(self, db: Session):
        """Initialize AI service."""
        self.db = db
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load AI configuration from database."""
        settings = self.db.query(SystemSettings).filter(
            SystemSettings.key == self.SETTINGS_KEY
        ).first()

        if settings and settings.value:
            return settings.value

        return {
            'provider': 'glm',  # glm, openai, anthropic
            'api_key': '',
            'model': 'glm-4',
            'api_url': 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
            'enabled': False
        }

    def save_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Save AI configuration to database."""
        settings = self.db.query(SystemSettings).filter(
            SystemSettings.key == self.SETTINGS_KEY
        ).first()

        if settings:
            settings.value = config
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
        """Get current AI configuration (without exposing full API key)."""
        config = self.config.copy()
        if config.get('api_key'):
            # Mask API key for display
            key = config['api_key']
            config['api_key_masked'] = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
            config['api_key_set'] = True
        else:
            config['api_key_masked'] = ''
            config['api_key_set'] = False
        del config['api_key']
        return config

    def is_configured(self) -> bool:
        """Check if AI service is properly configured."""
        return bool(self.config.get('api_key')) and self.config.get('enabled', False)

    def _call_llm(self, prompt: str) -> str | None:
        """Call the configured LLM API."""
        if not self.is_configured():
            print("AI Service not configured")
            return None

        provider = self.config.get('provider', 'glm')
        api_key = self.config.get('api_key')
        model = self.config.get('model', 'glm-4')

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
        """Call Zhipu GLM API."""
        url = self.config.get('api_url', 'https://open.bigmodel.cn/api/paas/v4/chat/completions')

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
        url = 'https://api.openai.com/v1/chat/completions'

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
        url = 'https://api.anthropic.com/v1/messages'

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

    def analyze_post(self, title: str, content: str) -> dict[str, Any] | None:
        """Analyze a single post to extract pain point.

        Returns:
            Dict with pain_point, opportunity_name, category, is_software_opportunity
            or None if analysis fails
        """
        prompt = self.EXTRACT_PAIN_POINT_PROMPT.format(
            title=title,
            content=content[:2000]  # Limit content length
        )

        response = self._call_llm(prompt)
        if not response:
            return None

        try:
            # Parse JSON from response
            # Handle markdown code blocks
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]

            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            print(f"Failed to parse AI response: {e}")
            print(f"Response was: {response[:500]}")
            return None

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
            # Fallback: treat each as its own cluster
            return [
                {
                    'name': p.get('opportunity_name', p['pain_point'][:50]),
                    'pain_point': p['pain_point'],
                    'post_ids': [p['id']],
                    'confidence': 0.5
                }
                for p in pain_points
            ]

        try:
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]

            data = json.loads(response.strip())
            return data.get('clusters', [])
        except json.JSONDecodeError:
            # Fallback
            return [
                {
                    'name': p.get('opportunity_name', p['pain_point'][:50]),
                    'pain_point': p['pain_point'],
                    'post_ids': [p['id']],
                    'confidence': 0.5
                }
                for p in pain_points
            ]

    def test_connection(self) -> dict[str, Any]:
        """Test the AI API connection."""
        if not self.config.get('api_key'):
            return {
                'success': False,
                'message': 'API key not configured'
            }

        try:
            response = self._call_llm("Say 'OK' if you can read this.")
            if response:
                return {
                    'success': True,
                    'message': f'Connected successfully. Response: {response[:100]}'
                }
            else:
                return {
                    'success': False,
                    'message': 'No response from API'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Connection failed: {str(e)}'
            }
