from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import transaction
from accounts.models import Profile
from accounts.tasks import send_welcome_notification_task


@receiver(post_save, sender=Profile)
def on_registration(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: send_welcome_notification_task.delay(instance.user.id))
