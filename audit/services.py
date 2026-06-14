from .models import AuditEvent


def record_audit_event(*, organization, actor, instance, action, metadata=None):
    return AuditEvent.objects.create(
        organization=organization,
        actor=actor,
        object_type=instance.__class__.__name__,
        object_id=str(instance.pk),
        action=action,
        metadata=metadata or {},
    )
