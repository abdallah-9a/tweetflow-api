from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserLogoutView,
    UserProfileView,
    UserUpdateProfileView,
    UserListView,
    UserRetrieveView,
    ChangePasswordView,
    SendPasswordResetEmailView,
    UserPasswordResetView,
    ActivateAPIView,
    DeactivateAPIView,
)

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("me/", UserProfileView.as_view(), name="profile"),
    path("users/", UserListView.as_view(), name="users-list"),  # Admin
    path("users/<str:username>/", UserRetrieveView.as_view(), name="user-detail"),
    path("me/update/", UserUpdateProfileView.as_view(), name="update-profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path(
        "send-reset-password-email/",
        SendPasswordResetEmailView.as_view(),
        name="send-reset-password-email",
    ),
    path(
        "reset-password/<uid>/<token>/",
        UserPasswordResetView.as_view(),
        name="reset-password",
    ),
    path("deactivate/", DeactivateAPIView.as_view(), name="deactivate"),
    path("activate/", ActivateAPIView.as_view(), name="activate"),
]
