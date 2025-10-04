from rest_framework import serializers
from .models import Tweet


class CreateTweetSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Tweet
        fields = ["user", "content", "image"]

    def get_user(self, obj):
        return obj.user.profile.name


class RetrieveTweetSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Tweet
        fields = ["user", "content", "image", "created_at"]

    def get_user(self, obj):
        return obj.user.profile.name
