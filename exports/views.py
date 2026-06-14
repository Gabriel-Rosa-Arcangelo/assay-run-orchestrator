from rest_framework import mixins, viewsets

from accounts.permissions import MANAGER_ROLES, organization_ids_for_user, require_organization_role
from audit.services import record_audit_event
from .models import ExportJob
from .serializers import ExportJobSerializer
from .tasks import generate_run_manifest


class ExportJobViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ExportJobSerializer

    def get_queryset(self):
        return ExportJob.objects.filter(
            organization_id__in=organization_ids_for_user(self.request.user)
        ).select_related("organization", "requested_by")

    def perform_create(self, serializer):
        organization = serializer.validated_data["organization"]
        require_organization_role(self.request.user, organization, MANAGER_ROLES)
        job = serializer.save(requested_by=self.request.user)
        record_audit_event(
            organization=organization,
            actor=self.request.user,
            instance=job,
            action="EXPORT_REQUESTED",
        )
        generate_run_manifest.delay(str(job.id))
