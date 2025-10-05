from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Follow

User = get_user_model()


class FollowUserSerializer(serializers.ModelSerializer):
    follower = serializers.SerializerMethodField(read_only=True)
    following = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Follow
        fields = ["follower", "following"]

    def get_follower(self, obj):
        return obj.follower.profile.name

    def get_following(self, obj):
        return obj.following.profile.name

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
    follower = serializers.SerializerMethodField(read_only=True)
    following = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Follow
        fields = ["follower", "following"]

    def get_follower(self, obj):
        return obj.follower.profile.name

    def get_following(self, obj):
        return obj.following.profile.name

    def validate(self, attrs):
        follower = self.context.get("follower")
        following = self.context.get("following")

        if not Follow.objects.filter(follower=follower, following=following).exists():
            raise serializers.ValidationError(
                {"error": "not_following", "detail": "You didn't follow this user"}
            )

        return attrs


class ListFollowersSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    followers = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ["user", "followers"]

    def get_user(self, obj):
        return obj.profile.name

    def get_followers(self, obj):
        qs = obj.followers.select_related("follower", "follower__profile")
        return [(f.follower.profile.name) for f in qs]


class ListFollowingSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    following = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ["user", "following"]

    def get_user(self, obj):
        return obj.profile.name

    def get_following(self, obj):
        qs = obj.following.select_related("following", "following__profile")
        return [f.following.profile.name for f in qs]
