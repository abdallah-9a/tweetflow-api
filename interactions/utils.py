from django.contrib.contenttypes.models import ContentType
from .models import Notification


def create_notification(sender, receiver, target, verb):

    if sender == receiver:  # Don't notify yourself
        return

    content_type = None
    content_id = None
    if target:
        content_type = ContentType.objects.get_for_model(target)
        content_id = target.id

    Notification.objects.create(
        sender=sender,
        receiver=receiver,
        verb=verb,
        content_type=content_type,
        content_id=content_id,
    )
