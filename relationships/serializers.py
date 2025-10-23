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


class ListFollowersSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    followers = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ["user", "followers"]

    def get_user(self, obj):
        return obj.profile.name

    def get_followers(self, obj):
        request = self.context.get("request")
        search = None

        if request:
            search = request.query_params.get("search")

        qs = obj.followers.select_related("follower", "follower__profile")

        if search:

            followers = qs.filter(
                Q(follower__profile__name__icontains=search)
                | Q(follower__username__icontains=search)
            )
            return [(f.follower.profile.name) for f in followers]

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
        request = self.context.get("request")
        search = None
        if request:
            search = request.query_params.get("search")

        qs = obj.following.select_related("following", "following__profile")

        if search:
            following = qs.filter(
                Q(following__profile__name__icontains=search)
                | Q(following__username__icontains=search)
            )
            return [f.following.profile.name for f in following]

        return [f.following.profile.name for f in qs]
