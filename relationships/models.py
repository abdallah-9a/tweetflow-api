from django.db import models
from django.conf import settings

# Create your models here.


class Follow(models.Model):
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers"
    )
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("follower", "following")

    def __str__(self):
        return f"{self.follower} follow {self.following}"

    def save(self, *args, **kwargs):
        if self.follower == self.following:
            raise ValueError("Users can't follow themselves")

        return super().save(*args, **kwargs)
