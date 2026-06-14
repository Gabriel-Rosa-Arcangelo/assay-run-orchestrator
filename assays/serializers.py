from rest_framework import serializers

from .models import AssayRun, QcMetric


class QcMetricSerializer(serializers.ModelSerializer):
    passed = serializers.BooleanField(read_only=True)

    class Meta:
        model = QcMetric
        fields = [
            "id",
            "run",
            "name",
            "value",
            "unit",
            "lower_limit",
            "upper_limit",
            "passed",
            "recorded_at",
        ]
        read_only_fields = ["id", "passed", "recorded_at"]


class AssayRunSerializer(serializers.ModelSerializer):
    qc_metrics = QcMetricSerializer(many=True, read_only=True)
    created_by = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = AssayRun
        fields = [
            "id",
            "organization",
            "external_id",
            "assay_type",
            "status",
            "created_by",
            "qc_metrics",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_by", "created_at", "updated_at"]


class TransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=AssayRun.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)
