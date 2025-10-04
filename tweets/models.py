from django.db import models
from django.contrib.auth import get_user_model

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
