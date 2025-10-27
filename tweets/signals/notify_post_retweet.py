from django.dispatch import receiver
from django.db.models.signals import post_save
from tweets.models import Retweet
from interactions.utils import create_notification


@receiver(post_save, sender=Retweet)
def on_retweet(sender, instance, created, **kwargs):
    if created:
        create_notification(
            sender=instance.user,
            receiver=instance.tweet.user,
            verb="retweeted",
            target=instance,
        )
