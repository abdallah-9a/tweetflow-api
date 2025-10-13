from rest_framework import serializers
from .models import Mention


class ListUserMentionsSerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField(read_only=True)
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

    def get_actor(self, obj):
        return obj.actor.username

    def get_content_object(self, obj):
        return obj.content_type.model

    def get_content_preview(self, obj):
        if hasattr(obj.content_object, "content"):
            return obj.content_object.content[:20]

        elif hasattr(obj.content_object, "quote"):
            return obj.content_object.quote[:20]

        return
