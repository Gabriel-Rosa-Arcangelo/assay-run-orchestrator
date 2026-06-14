from rest_framework import mixins, viewsets

from accounts.permissions import organization_ids_for_user
from .models import AuditEvent
from .serializers import AuditEventSerializer


class AuditEventViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = AuditEventSerializer

    def get_queryset(self):
        return AuditEvent.objects.filter(
            organization_id__in=organization_ids_for_user(self.request.user)
        ).select_related("organization", "actor")
