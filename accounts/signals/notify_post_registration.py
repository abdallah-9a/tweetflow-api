from django.dispatch import receiver
from django.db.models.signals import post_save
from accounts.models import Profile
from interactions.utils import create_notification


@receiver(post_save, sender=Profile)
def on_registration(sender, instance, created, **kwargs):
    if created:
        create_notification(receiver=instance.user, verb="welcome")
