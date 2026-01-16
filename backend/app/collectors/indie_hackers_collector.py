"""Indie Hackers data collector using web scraping."""

import os
import sys
from typing import Any

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_collector import BaseCollector, CollectorResult, register_collector


@register_collector('indie_hackers')
class IndieHackersCollector(BaseCollector):
    """Collector for Indie Hackers data.

    Scrapes product listings and revenue data.

    Configuration:
        custom_params: {
            'limit': Maximum listings to collect (default: 50)
            'include_unlaunched': Include unlaunched products (default: false)
        }
    """

    BASE_URL = "https://www.indiehackers.com"

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize Indie Hackers collector."""
        super().__init__(config)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _authenticate(self) -> None:
        """No authentication required for public scraping."""
        pass

    def get_required_config_keys(self) -> list[str]:
        """Get required configuration keys.

        Returns:
            Empty list - no API keys required
        """
        return []

    def collect(  # type: ignore[override]
        self,
        limit: int = 50,
        **kwargs: Any
    ) -> list[CollectorResult]:
        """Collect product listings from Indie Hackers.

        Args:
            limit: Maximum listings to collect

        Returns:
            List of collector results
        """
        # Get custom params
        custom_params = self.collector_config.custom_params
        if custom_params.get('limit'):
            limit = custom_params['limit']

        results = []

        try:
            # Scrape the products page
            url = f"{self.BASE_URL}/products"
            response = self.session.get(url, timeout=self.collector_config.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find product cards
            # Note: Selectors may need adjustment based on actual IH HTML structure
            product_cards = soup.find_all('div', class_='product-card')[:limit]

            for card in product_cards:
                try:
                    # Extract data
                    title_elem = card.find(['h3', 'h4'], class_='title')
                    desc_elem = card.find('p', class_='description')
                    link_elem = card.find('a', href=True)

                    if not title_elem or not link_elem:
                        continue

                    # Extract revenue if available
                    revenue_text = self._extract_revenue(card)

                    result = CollectorResult(
                        title=self._normalize_text(title_elem.get_text()),
                        description=self._normalize_text(desc_elem.get_text() if desc_elem else ''),
                        url=f"{self.BASE_URL}{link_elem['href']}",
                        source_type='indie_hackers',
                        engagement_metrics={
                            'revenue': revenue_text or 'N/A'
                        },
                        metadata={
                            'has_revenue_proof': bool(revenue_text)
                        }
                    )
                    results.append(result)

                except Exception as e:
                    print(f"Error parsing product card: {e}")
                    continue

        except Exception as e:
            print(f"Error scraping Indie Hackers: {e}")

        return results

    def _extract_revenue(self, card) -> str | None:
        """Extract revenue information from card.

        Args:
            card: BeautifulSoup element

        Returns:
            Revenue string or None
        """
        import re
        text = card.get_text()

        # Common revenue patterns on IH
        patterns = [
            r'\$?[\d,]+\/month\s*MRR',
            r'\$?[\d,]+\/mo\s*MRR',
            r'MRR\s*\$?[\d,]+',
            r'\$?[\d,]+\/month\s*revenue',
            r'making\s*\$?[\d,]+\/month'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)

        return None
