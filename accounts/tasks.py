from celery import shared_task
from django.contrib.auth import get_user_model
from .utils import Util
from interactions.utils import create_notification

User = get_user_model()

@shared_task
def send_email_task(data):
    Util.send_email(data)


@shared_task
def send_welcome_notification_task(user_id):
    try:
        user = User.objects.get(id=user_id)
        create_notification(receiver=user, verb="welcome")
    except User.DoesNotExist:
        pass
