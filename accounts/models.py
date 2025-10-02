from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.


class User(AbstractUser):
    email = models.EmailField(max_length=225, unique=True)
    username = models.CharField(max_length=225, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    REQUIRED_FIELDS = ["email"]

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()

        return super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Profile(models.Model):
    STATUS_CHOICES = [
        ("Active", "active"),
        ("Deactive", "deactive"),
        ("Suspended", "suspended"),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    name = models.CharField(max_length=100)  # Display Name
    bio = models.TextField(max_length=350, blank=True)
    profile_image = models.ImageField(
        upload_to="profile_images/",
        default="profile_images/blank.jpg",
    )
    cover_image = models.ImageField(
        upload_to="cover_images/", default="cover_images/blank.jpg"
    )
    website = models.URLField(blank=True, null=True)
    status = models.CharField(choices=STATUS_CHOICES, default="active")
    location = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.user.username
        return super().save(*args, **kwargs)
