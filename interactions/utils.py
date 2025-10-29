from django.contrib.contenttypes.models import ContentType
from .models import Notification


def create_notification(sender=None, receiver=None, target=None, verb=None):
    """
     Create a Notification for an action performed by one user on another, optionally tied to a target object.

    This helper is intended to be called from signal handlers (e.g., on like, comment, retweet, follow, mention).
    It is a no-op when the sender and receiver are the same user.

    Args:
        sender (User): The user who performed the action.
        receiver (User): The user who should receive the notification.
        target (Model | None): The object the action relates to (e.g., Tweet, Comment, Retweet, Follow).
            When provided, it's resolved to (content_type, content_id) using ContentType.get_for_model(target).
        verb (str): The action verb. Must match one of Notification.VERB_CHOICES

    """
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
