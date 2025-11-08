from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers
from .models import Follow

User = get_user_model()


class FollowUserSerializer(serializers.ModelSerializer):
    follower = serializers.CharField(source="follower.profile.name", read_only=True)
    following = serializers.CharField(source="following.profile.name", read_only=True)

    class Meta:
        model = Follow
        fields = ["follower", "following"]

    def validate(self, attrs):
        follower = self.context.get("follower")
        following = self.context.get("following")

        if follower == following:
            raise serializers.ValidationError(
                {"error": "self_follow", "detail": "You cannot follow yourself"}
            )

        if Follow.objects.filter(follower=follower, following=following).exists():
            raise serializers.ValidationError(
                {
                    "error": "already_following",
                    "detail": "You already follow this user",
                }
            )

        return attrs


class UnFollowUserSerializer(serializers.ModelSerializer):
    follower = serializers.CharField(source="follower.profile.name", read_only=True)
    following = serializers.CharField(source="following.profile.name", read_only=True)

    class Meta:
        model = Follow
        fields = ["follower", "following"]

    def validate(self, attrs):
        follower = self.context.get("follower")
        following = self.context.get("following")

        if not Follow.objects.filter(follower=follower, following=following).exists():
            raise serializers.ValidationError(
                {"error": "not_following", "detail": "You didn't follow this user"}
            )

        return attrs


class FollowerUserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="profile.name")
    profile_image = serializers.ImageField(source="profile.profile_image")

    class Meta:
        model = User
        fields = ["id", "username", "name", "profile_image"]


class FollowingUserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="profile.name")
    profile_image = serializers.ImageField(source="profile.profile_image")

    class Meta:
        model = User
        fields = ["id", "username", "name", "profile_image"]
