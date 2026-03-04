from django.core.cache import cache

def invalidate_feed_cache(user_id):
    """
    Invalidate all cached feed pages for a specific user.
    Uses versioning: bumping the version makes all old keys stale.
    Stale keys will be automatically removed by Redis based on their TTL.
    """
    version_key = f"feed_version:{user_id}"
    try:
        cache.incr(version_key)
    except ValueError:
        cache.set(version_key, 1, timeout=None)


def get_feed_cache_key(user_id, page, search=""):
    """
    Build a cache key for the feed that includes the user's local version number.
    """
    version_key = f"feed_version:{user_id}"
    version = cache.get(version_key, 0)
    
    return f"feed:u{user_id}:v{version}:p{page}:s{search}"