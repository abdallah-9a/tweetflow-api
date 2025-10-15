from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from tweets.models import Retweet
from interactions.models import Mention
import re


User = get_user_model()


@receiver(post_save, sender=Retweet)
def handle_retweet_mentions(sender, instance, created, **kwargs):
    if not created or not instance.quote:
        return

    pattern = r"@(\w+)"
    usernames = re.findall(pattern, instance.quote)

    if not usernames:
        return

    content_type = ContentType.objects.get_for_model(Retweet)

    for username in usernames:
        mentioned_user = User.objects.filter(username=username).first()
        if mentioned_user and mentioned_user != instance.user:
            Mention.objects.create(
                actor=instance.user,
                mentioned_user=mentioned_user,
                content_type=content_type,
                content_id=instance.id,
            )
