from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import MANAGER_ROLES, organization_ids_for_user, require_organization_role
from audit.services import record_audit_event
from .models import AssayRun, QcMetric
from .serializers import AssayRunSerializer, QcMetricSerializer, TransitionSerializer
from .services import transition_assay_run


class AssayRunViewSet(viewsets.ModelViewSet):
    serializer_class = AssayRunSerializer

    def get_queryset(self):
        return (
            AssayRun.objects.filter(organization_id__in=organization_ids_for_user(self.request.user))
            .select_related("organization", "created_by")
            .prefetch_related("qc_metrics")
        )

    def perform_create(self, serializer):
        organization = serializer.validated_data["organization"]
        require_organization_role(self.request.user, organization, MANAGER_ROLES)
        run = serializer.save(created_by=self.request.user)
        record_audit_event(
            organization=organization,
            actor=self.request.user,
            instance=run,
            action="RUN_CREATED",
        )

    def perform_update(self, serializer):
        require_organization_role(self.request.user, serializer.instance.organization, MANAGER_ROLES)
        serializer.save()

    def perform_destroy(self, instance):
        require_organization_role(self.request.user, instance.organization, MANAGER_ROLES)
        instance.delete()

    @extend_schema(request=TransitionSerializer, responses=AssayRunSerializer)
    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        run = self.get_object()
        require_organization_role(request.user, run.organization, MANAGER_ROLES)
        serializer = TransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        run = transition_assay_run(
            run=run,
            target_status=serializer.validated_data["status"],
            actor=request.user,
            note=serializer.validated_data.get("note", ""),
        )
        return Response(AssayRunSerializer(run).data)


class QcMetricViewSet(viewsets.ModelViewSet):
    serializer_class = QcMetricSerializer

    def get_queryset(self):
        return QcMetric.objects.filter(
            run__organization_id__in=organization_ids_for_user(self.request.user)
        ).select_related("run", "run__organization")

    def perform_create(self, serializer):
        run = serializer.validated_data["run"]
        require_organization_role(self.request.user, run.organization, MANAGER_ROLES)
        metric = serializer.save()
        record_audit_event(
            organization=run.organization,
            actor=self.request.user,
            instance=metric,
            action="QC_METRIC_RECORDED",
            metadata={"run_id": str(run.id), "passed": metric.passed},
        )

    def perform_update(self, serializer):
        require_organization_role(self.request.user, serializer.instance.run.organization, MANAGER_ROLES)
        serializer.save()

    def perform_destroy(self, instance):
        require_organization_role(self.request.user, instance.run.organization, MANAGER_ROLES)
        instance.delete()
