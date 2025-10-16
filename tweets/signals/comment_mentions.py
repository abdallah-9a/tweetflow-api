from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from tweets.models import Comment
from interactions.models import Mention
import re


User = get_user_model()


@receiver(post_save, sender=Comment)
def handle_comment_mentions(sender, instance, created, **kwargs):
    if not created or not instance.content:
        return

    pattern = r"@(\w+)"
    usernames = re.findall(pattern, instance.content)

    if not usernames:
        return

    content_type = ContentType.objects.get_for_model(Comment)

    usernames = set(usernames)
    mentioned_users = User.objects.filter(username__in=usernames)
    for user in mentioned_users:
        if user != instance.user:
            Mention.objects.create(
                actor=instance.user,
                mentioned_user=user,
                content_type=content_type,
                content_id=instance.id,
            )
