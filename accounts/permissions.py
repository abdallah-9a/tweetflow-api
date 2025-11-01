from rest_framework import permissions


class IsActiveUser(permissions.BasePermission):
    """
    Custom permission to only allow access to users whose profile status is 'active'.

    This permission checks if the requesting user is authenticated and has an active profile status.
    """

    def has_permission(self, request, view):
        user = request.user

        return bool(user and user.is_authenticated and user.profile.status == "active")
