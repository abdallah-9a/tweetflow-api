from rest_framework import serializers
from .models import Mention, Notification


class ListUserMentionsSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source="actor.username", read_only=True)
    content_object = serializers.SerializerMethodField(read_only=True)
    content_preview = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Mention
        fields = [
            "actor",
            "content_object",
            "content_preview",
            "content_id",
            "created_at",
        ]

    def get_content_object(self, obj):
        return obj.content_type.model

    def get_content_preview(self, obj):
        if hasattr(obj.content_object, "content"):
            return obj.content_object.content[:20]

        elif hasattr(obj.content_object, "quote"):
            return obj.content_object.quote[:20]

        return


class ListNotificationsSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField(read_only=True)
    content = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "sender", "content", "is_read", "created_at"]

    def get_sender(self, obj):
        if obj.sender:
            return obj.sender.profile.name

        return "System"

    def get_content(self, obj):
        templates = {
            "followed": lambda: f"{obj.sender} followed you",
            "liked": lambda: f"{obj.sender} liked your {obj.content_type.model}",
            "retweeted": lambda: f"{obj.sender} retweeted your {obj.content_type.model}",
            "commented": lambda: f"{obj.sender} commented on your {obj.content_type.model}",
            "mentioned": lambda: f"{obj.sender} mentioned you in a {obj.content_type.model}",
            "welcome": lambda: "Welcome to Twitter 🎉",
            "changed": lambda: "your password has changed",
            "reset": lambda: "your password has reset",
        }
        return templates.get(obj.verb, lambda: "")()
