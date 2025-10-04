from rest_framework import serializers
from .models import Tweet, Like


class CreateTweetSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Tweet
        fields = ["user", "content", "likes_count", "image"]

    def get_user(self, obj):
        return obj.user.profile.name


class RetrieveTweetSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Tweet
        fields = ["user", "content", "image", "likes_count", "created_at"]

    def get_user(self, obj):
        return obj.user.profile.name


class LikeTweetSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    tweet = RetrieveTweetSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ["user", "tweet"]

    def get_user(self, obj):
        return obj.user.profile.name

    def validate(self, attrs):
        user = self.context["request"].user
        tweet = self.context["tweet"]

        if Like.objects.filter(user=user, tweet=tweet).exists():
            raise serializers.ValidationError(
                {
                    "error": "already_liked",
                    "detail": "You have already liked this tweet. Use DELETE to unlike.",
                }
            )

        return attrs


class UnlikTweetSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    tweet = RetrieveTweetSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ["user", "tweet"]

    def get_user(self, obj):
        return obj.user.profile.name


class ListLikesSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Like
        fields = ["user", "created_at"]

    def get_user(self, obj):
        return obj.user.profile.name
