from rest_framework import serializers

from .models import ExportJob


class ExportJobSerializer(serializers.ModelSerializer):
    requested_by = serializers.CharField(source="requested_by.username", read_only=True)

    class Meta:
        model = ExportJob
        fields = [
            "id",
            "organization",
            "requested_by",
            "status",
            "file",
            "error",
            "created_at",
            "completed_at",
        ]
        read_only_fields = [
            "id",
            "requested_by",
            "status",
            "file",
            "error",
            "created_at",
            "completed_at",
        ]
