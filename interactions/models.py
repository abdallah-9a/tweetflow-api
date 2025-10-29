from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

# Create your models here.


class Mention(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mentions_made"
    )
    mentioned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mentions_received",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    content_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "content_id")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("mentioned_user", "content_type", "content_id")

    def __str__(self):
        return (
            f"{self.actor} mentioned {self.mentioned_user} in {self.content_type_name}"
        )

    @property
    def content_type_name(self):
        return self.content_type.model


class Notification(models.Model):
    VERB_CHOICES = [
        ("followed", "Followed"),
        ("commented", "Commented"),
        ("mentioned", "Mentioned"),
        ("retweeted", "Retweeted"),
        ("liked", "Liked"),
        # System notification
        ("welcome", "Welcome"),
        ("reset", "Reset"),
        ("changed", "Changed"),
    ]
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_notifications",
        null=True,
        blank=True,
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_notifications",
    )

    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    content_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey("content_type", "content_id")

    verb = models.CharField(choices=VERB_CHOICES, max_length=10)
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("sender", "receiver", "verb", "content_type", "content_id")

    def __str__(self):
        templates = {
            "followed": lambda: f"{self.sender} followed {self.receiver}",
            "liked": lambda: f"{self.sender} liked {self.receiver}'s {self.content_type.model}",
            "retweeted": lambda: f"{self.sender} retweeted {self.receiver}'s {self.content_type.model}",
            "commented": lambda: f"{self.sender} commented on {self.receiver}'s {self.content_type.model}",
            "mentioned": lambda: f"{self.sender} mentioned {self.receiver} in a {self.content_type.model}",
            "welcome": lambda: f"{self.receiver} has registered",
            "changed": lambda: f"{self.receiver}'s password has changed",
            "reset": lambda: f"{self.receiver}'s password has reset",
        }

        return templates.get(self.verb, lambda: "")()
