import uuid

from django.conf import settings
from django.db import models

from accounts.models import Organization


class AssayRun(models.Model):
    class Status(models.TextChoices):
        CREATED = "CREATED", "Created"
        READY = "READY", "Ready"
        RUNNING = "RUNNING", "Running"
        QC_REVIEW = "QC_REVIEW", "QC review"
        RELEASED = "RELEASED", "Released"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="assay_runs")
    external_id = models.CharField(max_length=80)
    assay_type = models.CharField(max_length=80)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_assay_runs")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["organization", "external_id"], name="unique_assay_run_external_id")
        ]


class QcMetric(models.Model):
    run = models.ForeignKey(AssayRun, on_delete=models.CASCADE, related_name="qc_metrics")
    name = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=14, decimal_places=4)
    unit = models.CharField(max_length=30, blank=True)
    lower_limit = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    upper_limit = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    @property
    def passed(self) -> bool:
        if self.lower_limit is not None and self.value < self.lower_limit:
            return False
        if self.upper_limit is not None and self.value > self.upper_limit:
            return False
        return True
