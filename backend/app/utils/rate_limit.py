"""Rate limiting utility using Redis."""

import functools

from flask import jsonify

from app.redis_client import redis_client


def rate_limit(limit: int, period: int, key_func=None):
    """Rate limiting decorator.

    Args:
        limit: Maximum number of requests
        period: Time period in seconds
        key_func: Function to generate rate limit key (defaults to IP)

    Returns:
        Decorator function
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            from flask import request

            # Get key
            if key_func:
                key = key_func()
            else:
                key = f"rate_limit:{request.remote_addr}:{f.__name__}"

            # Check current count
            current = redis_client.get(key)
            if current is None:
                redis_client.setex(key, period, 1)
            else:
                current = int(current)
                if current >= limit:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'retry_after': redis_client.ttl(key)
                    }), 429
                redis_client.incr(key)

            return f(*args, **kwargs)
        return wrapper
    return decorator
