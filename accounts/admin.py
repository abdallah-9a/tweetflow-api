from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile

# Register your models here.


class useradmin(UserAdmin):
    list_display = ["id", "username", "email", "is_staff"]


class ProfileAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "status"]


admin.site.register(User, useradmin)
admin.site.register(Profile, ProfileAdmin)
