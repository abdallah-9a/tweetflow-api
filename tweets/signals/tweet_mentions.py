from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import transaction
from tweets.models import Tweet
from tweets.tasks import parse_mentions_task


@receiver(post_save, sender=Tweet)
def handle_tweet_mentions(sender, instance, created, **kwargs):
    if not created or not instance.content:
        return

    transaction.on_commit(lambda: parse_mentions_task.delay(instance.id))
