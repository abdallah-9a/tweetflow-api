from rest_framework import serializers
from .models import Tweet, Like, Comment


class CreateTweetSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    comments = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Tweet
        fields = ["user", "content", "likes_count", "image", "comments"]

    def get_user(self, obj):
        return obj.user.profile.name

    def get_comments(self, obj):
        return obj.comments.all()


class RetrieveTweetSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    comments = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Tweet
        fields = ["user", "content", "image", "likes_count", "comments", "created_at"]

    def get_user(self, obj):
        return obj.user.profile.name

    def get_comments(self, obj):
        return obj.comments.all()


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


class CommentOnTweetSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    tweet = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ["user", "tweet", "content", "image"]

    def get_user(self, obj):
        return obj.user.profile.name

    def validate(self, attrs):
        content = attrs.get("content", "")
        image = attrs.get("image")

        if not content and not image:
            raise serializers.ValidationError(
                {
                    "error": "empty_comment",
                    "detail": "A comment must have either content, image or both",
                }
            )
        return attrs


class ListCommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        fields = ["user", "content", "image", "created_at"]

    def get_user(self, obj):
        return obj.user.profile.name
