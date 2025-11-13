from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Tweet, Like, Comment, Retweet

User = get_user_model()


class TweetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tweet
        fields = ["id", "content", "image"]

    def validate(self, attrs):
        content = attrs.get("content")
        image = attrs.get("image")

        if not content and not image:
            raise serializers.ValidationError(
                {
                    "error": "empty_tweet",
                    "detail": "A tweet must have content, image, or both",
                }
            )


class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for author details in posts"""

    name = serializers.CharField(source="profile.name", read_only=True)
    profile_image = serializers.ImageField(
        source="profile.profile_image", read_only=True
    )

    class Meta:
        model = User
        fields = ["id", "username", "name", "profile_image"]


class OriginalTweetSerializer(serializers.ModelSerializer):
    """Serializer for original tweet in retweets (nested)"""

    author = AuthorSerializer(source="user", read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    comments_count = serializers.IntegerField(read_only=True)
    retweets_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.BooleanField(read_only=True)
    is_retweeted = serializers.BooleanField(read_only=True)

    class Meta:
        model = Tweet
        fields = [
            "id",
            "author",
            "content",
            "image",
            "likes_count",
            "comments_count",
            "retweets_count",
            "is_liked",
            "is_retweeted",
            "created_at",
        ]


class FeedSerializer(serializers.Serializer):
    def to_representation(self, instance):
        if isinstance(instance, Tweet):
            return {
                "id": instance.id,
                "type": "tweet",
                "author": AuthorSerializer(instance.user).data,
                "content": instance.content,
                "image": instance.image.url if instance.image else None,
                "likes_count": getattr(instance, "likes_count", 0),
                "comments_count": getattr(instance, "comments_count", 0),
                "retweets_count": getattr(instance, "retweets_count", 0),
                "is_liked": getattr(instance, "is_liked", False),
                "is_retweeted": getattr(instance, "is_retweeted", False),
                "created_at": instance.created_at,
            }

        else:
            original_tweet = {
                "id": instance.tweet.id,
                "author": AuthorSerializer(instance.tweet.user).data,
                "content": instance.tweet.content,
                "image": instance.tweet.image.url if instance.tweet.image else None,
                "likes_count": getattr(instance, "tweet_likes_count", 0),
                "comments_count": getattr(instance, "tweet_comments_count", 0),
                "retweets_count": getattr(instance, "tweet_retweets_count", 0),
                "created_at": instance.tweet.created_at,
            }

            return {
                "id": instance.id,
                "type": "retweet",
                "author": AuthorSerializer(instance.user).data,
                "quote": instance.quote,
                "original_tweet": original_tweet,
                "created_at": instance.created_at,
            }


class PostSerializer(serializers.Serializer):
    """
    Unified serializer for tweets and retweets feed.
    Returns rich nested data matching modern social platform patterns.
    """

    def to_representation(self, instance):
        if isinstance(instance, Tweet):
            return {
                "id": instance.id,
                "type": "tweet",
                "author": AuthorSerializer(instance.user).data,
                "content": instance.content,
                "image": instance.image.url if instance.image else None,
                "likes_count": getattr(instance, "likes_count", 0),
                "comments_count": getattr(instance, "comments_count", 0),
                "retweets_count": getattr(instance, "retweets_count", 0),
                "is_liked": getattr(instance, "is_liked", False),
                "is_retweeted": getattr(instance, "is_retweeted", False),
                "created_at": instance.created_at,
            }

        elif isinstance(instance, Retweet):
            original_tweet_data = {
                "id": instance.tweet.id,
                "author": AuthorSerializer(instance.tweet.user).data,
                "content": instance.tweet.content,
                "image": instance.tweet.image.url if instance.tweet.image else None,
                "likes_count": getattr(instance, "tweet_likes_count", 0),
                "comments_count": getattr(instance, "tweet_comments_count", 0),
                "retweets_count": getattr(instance, "tweet_retweets_count", 0),
                "created_at": instance.tweet.created_at,
            }

            return {
                "id": instance.id,
                "type": "retweet",
                "author": AuthorSerializer(instance.user).data,
                "quote": instance.quote,
                "original_tweet": original_tweet_data,
                "created_at": instance.created_at,
            }

        return {}


class RetrieveTweetSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.profile.name", read_only=True)
    comments = serializers.SerializerMethodField(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tweet
        fields = ["user", "content", "image", "likes_count", "comments", "created_at"]

    def get_comments(self, obj):
        queryset = obj.comments.filter(parent=None)
        return CommentSerializer(queryset, many=True).data


class RetweetSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField(read_only=True)
    author = serializers.SerializerMethodField(read_only=True)
    tweet = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Retweet
        fields = ["id", "type", "author", "quote", "tweet", "created_at"]

    def validate(self, attrs):
        user = self.context["user"]
        tweet = self.context["tweet"]

        if Retweet.objects.filter(user=user, tweet=tweet).exists():
            raise serializers.ValidationError(
                {
                    "error": "already_retweeted",
                    "detail": "You have already retweeted this tweet. Use DELETE to unretweet.",
                }
            )

        return attrs

    def get_type(self, obj):
        return "retweet"

    def get_author(self, obj):
        return AuthorSerializer(obj.user).data

    def get_tweet(self, obj):
        tweet = obj.tweet
        tweet.likes_count = getattr(obj, "tweet_likes_count", 0)
        tweet.comments_count = getattr(obj, "tweet_comments_count", 0)
        tweet.retweets_count = getattr(obj, "tweet_retweets_count", 0)
        tweet.is_liked = getattr(obj, "tweet_is_liked", False)
        tweet.is_retweeted = getattr(obj, "tweet_is_retweeted", False)
        return OriginalTweetSerializer(tweet).data


class LikeTweetSerializer(serializers.ModelSerializer):
    user = AuthorSerializer(read_only=True)
    tweet_id = serializers.IntegerField(source="tweet.id", read_only=True)

    class Meta:
        model = Like
        fields = ["id", "user", "tweet_id", "created_at"]

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


class CommentOnTweetSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.profile.name", read_only=True)
    tweet = serializers.PrimaryKeyRelatedField(read_only=True)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Comment
        fields = ["user", "tweet", "parent", "content", "image"]

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
    user = serializers.CharField(source="user.profile.name", read_only=True)
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

    def get_replies(self, obj):
        queryset = obj.replies.all()
        return CommentSerializer(queryset, many=True).data


class ListCommentSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.profile.name", read_only=True)
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

    def get_replies(self, obj):
        queryset = obj.replies.all()
        return CommentSerializer(queryset, many=True).data
