from rest_framework import serializers
from .models import Tweet, Like, Comment, Retweet


class CreateTweetSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    comments = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Tweet
        fields = ["user", "content", "likes_count", "image", "comments"]

    def get_user(self, obj):
        return obj.user.profile.name

    def get_comments(self, obj):
        queryset = (
            obj.comments.select_related("user", "user__profile")
            .filter(parent=None)
            .all()
        )
        return CommentSerializer(queryset, many=True).data


class RetrieveTweetSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    comments = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Tweet
        fields = ["user", "content", "image", "likes_count", "comments", "created_at"]

    def get_user(self, obj):
        return obj.user.profile.name

    def get_comments(self, obj):
        queryset = (
            obj.comments.select_related("user", "user__profile")
            .filter(parent=None)
            .all()
        )
        return CommentSerializer(queryset, many=True).data


class RetweetSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    tweet = RetrieveTweetSerializer(read_only=True)

    class Meta:
        model = Retweet
        fields = ["user", "tweet", "quote"]


class ListRetweetsSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Retweet
        fields = ["user", "tweet", "quote", "created_at"]

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


class CommentOnTweetSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    tweet = serializers.PrimaryKeyRelatedField(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Comment
        fields = ["user", "tweet", "parent", "content", "image"]

    def get_user(self, obj):
        return obj.user.profile.name

    def validate(self, attrs):
        content = attrs.get("content", "")
        image = attrs.get("image")
        parent = attrs.get("parent")
        tweet = self.context.get("tweet")

        if not content and not image:
            raise serializers.ValidationError(
                {
                    "error": "empty_comment",
                    "detail": "A comment must have either content, image or both",
                }
            )

        if parent:
            # Ensure replies stay on the same tweet
            if tweet and parent.tweet_id != tweet.pk:
                raise serializers.ValidationError(
                    {
                        "error": "invalid_parent",
                        "detail": "Reply must reference a comment from the same tweet",
                    }
                )

        return attrs


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "parent",
            "content",
            "image",
            "created_at",
            "replies",
        ]

    def get_user(self, obj):
        return obj.user.profile.name

    def get_replies(self, obj):
        queryset = obj.replies.select_related("user", "user__profile")
        return CommentSerializer(queryset, many=True).data


class ListCommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "parent",
            "content",
            "image",
            "replies",
            "created_at",
        ]

    def get_user(self, obj):
        return obj.user.profile.name

    def get_replies(self, obj):
        queryset = obj.replies.select_related("user", "user__profile")
        return CommentSerializer(queryset, many=True).data
