from rest_framework.throttling import SimpleRateThrottle


class UserOrIPRateThrottle(SimpleRateThrottle):
    """Base throttle that limits by user id for authenticated users, otherwise by IP."""

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}


class AuthRateThrottle(UserOrIPRateThrottle):
    # Protect auth/account endpoints from brute-force and bot abuse.
    scope = "auth"


class ContentCreationRateThrottle(UserOrIPRateThrottle):
    # Limit high-cost content creation actions to reduce spam and DB pressure.
    scope = "content_creation"


class InteractionRateThrottle(UserOrIPRateThrottle):
    # Control rapid interaction actions such as like/retweet/follow to deter bots.
    scope = "interaction"


class AccountSensitiveRateThrottle(UserOrIPRateThrottle):
    # Apply stricter limits to sensitive account actions such as changing password.
    scope = "account_sensitive"
