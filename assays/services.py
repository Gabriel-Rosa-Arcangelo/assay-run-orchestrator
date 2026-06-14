from django.db import transaction
from rest_framework.exceptions import ValidationError

from audit.services import record_audit_event
from .models import AssayRun

ALLOWED_TRANSITIONS = {
    AssayRun.Status.CREATED: {AssayRun.Status.READY, AssayRun.Status.FAILED},
    AssayRun.Status.READY: {AssayRun.Status.RUNNING, AssayRun.Status.FAILED},
    AssayRun.Status.RUNNING: {AssayRun.Status.QC_REVIEW, AssayRun.Status.FAILED},
    AssayRun.Status.QC_REVIEW: {AssayRun.Status.RELEASED, AssayRun.Status.FAILED},
    AssayRun.Status.FAILED: {AssayRun.Status.READY},
    AssayRun.Status.RELEASED: set(),
}


@transaction.atomic
def transition_assay_run(*, run: AssayRun, target_status: str, actor, note: str = "") -> AssayRun:
    locked_run = AssayRun.objects.select_for_update().get(pk=run.pk)
    if target_status not in ALLOWED_TRANSITIONS[locked_run.status]:
        raise ValidationError(
            {"status": f"Cannot transition from {locked_run.status} to {target_status}."}
        )

    previous_status = locked_run.status
    locked_run.status = target_status
    locked_run.save(update_fields=["status", "updated_at"])
    record_audit_event(
        organization=locked_run.organization,
        actor=actor,
        instance=locked_run,
        action="STATUS_TRANSITION",
        metadata={"from": previous_status, "to": target_status, "note": note},
    )
    return locked_run
