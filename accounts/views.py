from django.db.models import Count
from django.contrib.auth import authenticate, logout
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from .models import User
from .utils import Util
from rest_framework import status, filters
from rest_framework.response import Response
from interactions.utils import create_notification
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserLogoutSerializer,
    UserProfileSerializer,
    UserUpdateProfileSerializer,
    UserSerializer,
    ListUserSerializer,
    ChangePasswordSerializer,
    SendPasswordRestEmailSerializer,
    UserPasswordResetSerializer,
    ActivateSerializer,
    PasswordCheckSerializer,
)
from .permissions import IsActiveUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser

# Create your views here.


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {"refresh": str(refresh), "access": str(refresh.access_token)}


class UserRegistrationView(APIView):

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = get_tokens_for_user(user)
        return Response(
            {"token": token, "detail": "Registration successful"},
            status=status.HTTP_201_CREATED,
        )


class UserLoginView(APIView):

    def post(self, request):

        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data.get("username")
        password = serializer.validated_data.get("password")

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {"detail": "This user is Deactivated"}, status=status.HTTP_403_FORBIDDEN
            )

        token = get_tokens_for_user(user)
        return Response(
            {"token": token, "detail": "Login Success"}, status=status.HTTP_200_OK
        )


class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = UserLogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"detail": "Logout Successful"}, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user.profile)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserUpdateProfileView(generics.UpdateAPIView):
    serializer_class = UserUpdateProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.profile


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Password changed successfully"}, status=status.HTTP_200_OK
        )


class SendPasswordResetEmailView(APIView):

    def post(self, request):
        serializer = SendPasswordRestEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = request.data.get("email")
        user = User.objects.filter(email=email).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)

            url = reverse("reset-password", kwargs={"uid": uid, "token": token})
            link = request.build_absolute_uri(url)

            # Send Email

            body = f"Click following this link to reset your password ---> {link}"
            data = {
                "subject": "reset your password",
                "body": body,
                "to_email": user.email,
            }
            Util.send_email(data)

        # Always return 200
        return Response(
            {"detail": "If the email is registered, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class UserPasswordResetView(APIView):

    def post(self, request, uid, token):
        serializer = UserPasswordResetSerializer(
            data=request.data, context={"uid": uid, "token": token}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "Password reset successfully"}, status=status.HTTP_200_OK
        )


class UserListView(generics.ListAPIView):
    serializer_class = ListUserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "profile__name"]

    def get_queryset(self):
        return User.objects.all().exclude(pk=self.request.user.pk)


class UserRetrieveView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "username"

    def get_queryset(self):  # avoid N+1 problem by precomputing in one query
        return (
            super()
            .get_queryset()
            .select_related("profile")
            .prefetch_related("tweets", "retweets")
            .annotate(
                followers_count=Count("followers", distinct=True),
                following_count=Count("following", distinct=True),
            )
        )


class DeactivateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data.get("password")

        if not request.user.check_password(password):
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
            )

        if request.user.profile.status == "deactive":
            return Response(
                {"detail": "Account already deactivated"}, status=status.HTTP_200_OK
            )

        profile = request.user.profile
        profile.status = "deactive"
        request.user.is_active = False
        request.user.save()
        profile.save()

        Util.send_email(
            {
                "subject": "Your account was deactivated",
                "body": "If this wasn't you, please contact support immediately",
                "to_email": request.user.email,
            }
        )
        create_notification(receiver=request.user, verb="deactivated")

        logout(request)
        return Response(
            {"detail": "Your account has been deactivated"}, status=status.HTTP_200_OK
        )


class ActivateAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = ActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data.get("username")
        password = serializer.validated_data.get("password")
        try:
            user = User.objects.select_related("profile").get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if user.profile.status == "active":
            return Response(
                {"detail": "Account already active"}, status=status.HTTP_200_OK
            )

        user.profile.status = "active"
        user.is_active = True
        user.save()
        user.profile.save()

        Util.send_email(
            {
                "subject": "Your account was reactivated",
                "body": "If this wasn't you, please contact support immediately",
                "to_email": user.email,
            }
        )
        create_notification(receiver=user, verb="reactivated")
        return Response(
            {"detail": "Your account has been successfully reactivated"},
            status=status.HTTP_200_OK,
        )


class DeleteAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        serializer = PasswordCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data["password"]):
            return Response(
                {"detail": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST
            )

        request.user.delete()
        return Response(
            {"detail": "Your account has been permanently deleted"},
            status=status.HTTP_200_OK,
        )
