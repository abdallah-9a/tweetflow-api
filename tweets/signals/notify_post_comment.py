from django.dispatch import receiver
from django.db.models.signals import post_save
from tweets.models import Comment
from interactions.utils import create_notification


@receiver(post_save, sender=Comment)
def on_comment(sender, instance, created, **kwargs):
    if created:
        create_notification(
            sender=instance.user,
            receiver=instance.tweet.user,
            verb="commented",
            target=instance,
        )
