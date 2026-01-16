import os
import sys

import redis

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    health_check_interval=30,
)


def get_redis():
    """Get Redis client instance.

    Returns:
        Redis client
    """
    return redis_client
