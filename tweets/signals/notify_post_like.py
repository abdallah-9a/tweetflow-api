from django.dispatch import receiver
from django.db.models.signals import post_save
from tweets.models import Like
from interactions.utils import create_notification


@receiver(post_save, sender=Like)
def on_like(sender, instance, created, **kwargs):
    if created:
        create_notification(
            sender=instance.user,
            receiver=instance.tweet.user,
            verb="liked",
            target=instance.tweet,
        )
