import csv
from io import StringIO

from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone

from assays.models import AssayRun
from .models import ExportJob


@shared_task
def generate_run_manifest(export_job_id: str):
    job = ExportJob.objects.get(pk=export_job_id)
    job.status = ExportJob.Status.PROCESSING
    job.save(update_fields=["status"])

    try:
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["run_id", "external_id", "assay_type", "status", "created_at"])
        for run in AssayRun.objects.filter(organization=job.organization).order_by("created_at"):
            writer.writerow([run.id, run.external_id, run.assay_type, run.status, run.created_at.isoformat()])

        job.file.save(f"assay-run-manifest-{job.id}.csv", ContentFile(buffer.getvalue()))
        job.status = ExportJob.Status.READY
        job.completed_at = timezone.now()
        job.save(update_fields=["file", "status", "completed_at"])
    except Exception as exc:
        job.status = ExportJob.Status.FAILED
        job.error = str(exc)
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error", "completed_at"])
        raise
