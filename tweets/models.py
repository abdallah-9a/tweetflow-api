from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

# Create your models here.
User = get_user_model()


class Tweet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tweets")
    content = models.TextField(max_length=1000)
    image = models.ImageField(upload_to="tweets/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"

    @property
    def likes_count(self):
        return self.likes.count()


class Retweet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name="retweets")
    quote = models.TextField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.profile.name} repost {self.tweet.content[:20]}"


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name="likes")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "tweet"], name="unique_user_tweet_like"
            )
        ]
        ordering = ["-created_at"]
        verbose_name = "Like"
        verbose_name_plural = "Likes"

    def __str__(self):
        return f"{self.user.profile.name} likes {self.tweet.content[:20]}"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    content = models.TextField(max_length=500)
    image = models.ImageField(upload_to="comments/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.profile.name} comments on {self.tweet.content[:20]}"

    def clean(self):
        if not self.content and not self.image:
            raise ValidationError("A comment must have a content, an image or both")
        if self.parent and self.parent.tweet != self.tweet:
            raise ValidationError(
                "Reply must belong to the same tweet as its parent comment"
            )
