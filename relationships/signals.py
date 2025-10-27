from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Follow
from interactions.utils import create_notification


@receiver(post_save, sender=Follow)
def notify_post_followed(sender, instance, created, **kwargs):
    if created:
        create_notification(
            sender=instance.follower,
            receiver=instance.following,
            verb="followed",
            target=instance,
        )
