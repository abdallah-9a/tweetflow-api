from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Mention
from .utils import create_notification


@receiver(post_save, sender=Mention)
def notify_post_mentioned(sender, instance, created, **kwargs):
    if created:
        create_notification(
            sender=instance.actor,
            receiver=instance.mentioned_user,
            verb="mentioned",
            target=instance.content_object,
        )
