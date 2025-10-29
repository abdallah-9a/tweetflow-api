from rest_framework import serializers
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from .models import User, Profile
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from interactions.utils import create_notification


class UserRegistrationSerializer(serializers.ModelSerializer):

    password2 = serializers.CharField(style={"input_type": "password"}, write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password2",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    # Vaidate password and confirm password while registration
    def validate(self, attrs):
        password = attrs.get("password")
        password2 = attrs.get("password2")
        if password != password2:
            raise serializers.ValidationError("Passwords Don't Match")
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],
        )
        return user


class UserLoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=225)

    class Meta:
        model = User
        fields = ["username", "password"]


class UserLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    default_error_messages = {"bad_token": "Token is invalid or expired"}

    def validate(self, attrs):
        self.token = attrs.get("refresh")
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            self.fail("bad_token")


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "name",
            "bio",
            "profile_image",
            "cover_image",
            "location",
            "website",
        ]


class UserUpdateProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = [
            "name",
            "bio",
            "profile_image",
            "cover_image",
            "location",
            "website",
        ]


class ChangePasswordSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(
        max_length=255, style={"input_type": "password"}, write_only=True
    )
    password = serializers.CharField(
        max_length=255, style={"input_type": "password"}, write_only=True
    )
    password2 = serializers.CharField(
        max_length=255, style={"input_type": "password"}, write_only=True
    )

    class Meta:
        model = User
        fields = ["old_password", "password", "password2"]

    def validate(self, attrs):
        old_password = attrs.get("old_password")
        password = attrs.get("password")
        password2 = attrs.get("password2")
        user = self.context.get("user")

        if not user.check_password(old_password):
            raise serializers.ValidationError("Old Password isn't correct")

        if password != password2:
            raise serializers.ValidationError("Passwords Don't Match")

        return attrs

    def save(self, **kwargs):
        user = self.context["user"]
        user.set_password(self.validated_data["password"])
        user.save()
        
        create_notification(receiver=user, verb="changed")

        return user


class SendPasswordRestEmailSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255)

    class Meta:
        fields = ["email"]


class UserPasswordResetSerializer(serializers.Serializer):
    password = serializers.CharField(
        max_length=255, style={"input_type": "password"}, write_only=True
    )
    password2 = serializers.CharField(
        max_length=255, style={"input_type": "password"}, write_only=True
    )

    class Meta:
        fields = ["password", "password2"]

    def validate(self, attrs):
        try:
            password = attrs.get("password")
            password2 = attrs.get("password2")

            token = self.context.get("token")
            uid = self.context.get("uid")

            if password != password2:
                raise serializers.ValidationError("Passwords Don't Match")

            id = force_bytes(urlsafe_base64_decode(uid))
            user = User.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                raise serializers.ValidationError("Reset link is invalid or expired")

            self.user = user
            return attrs

        except Exception:
            raise serializers.ValidationError(
                "Something went wrong with resetting password"
            )

    def save(self, **kwargs):
        user = getattr(self, "user", None)
        user.set_password(self.validated_data["password"])
        user.save()
        create_notification(receiver=user, verb="reset-password")

        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "id",
            "name",
            "bio",
            "profile_image",
            "cover_image",
            "website",
            "location",
        ]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)
    followers = serializers.SerializerMethodField(read_only=True)
    following = serializers.SerializerMethodField(read_only=True)
    posts = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username",
            "profile",
            "followers_count",
            "followers",
            "following_count",
            "following",
            "posts",
        ]

    def get_followers(self, obj):
        request = self.context.get("request")
        url = reverse("followers", kwargs={"pk": obj.pk})
        return request.build_absolute_uri(url) if request else url

    def get_following(self, obj):
        request = self.context.get("request")
        url = reverse("following", kwargs={"pk": obj.pk})
        return request.build_absolute_uri(url) if request else url

    def get_posts(self, obj):
        from tweets.serializers import PostSerializer
        from itertools import chain
        from operator import attrgetter

        tweets = obj.tweets.select_related("user", "user__profile").prefetch_related(
            "comments"
        )
        retweets = obj.retweets.select_related("user", "user__profile", "tweet")
        posts = sorted(
            chain(tweets, retweets),
            key=attrgetter("created_at"),
            reverse=True,
        )
        return PostSerializer(posts, many=True).data


class ListUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
