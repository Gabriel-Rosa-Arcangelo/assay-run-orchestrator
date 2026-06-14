from rest_framework import serializers

from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "organization",
            "actor",
            "object_type",
            "object_id",
            "action",
            "metadata",
            "created_at",
        ]
