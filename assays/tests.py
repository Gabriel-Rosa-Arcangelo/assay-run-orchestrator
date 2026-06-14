from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Membership, Organization
from audit.models import AuditEvent
from .models import AssayRun, QcMetric


class QcMetricTests(APITestCase):
    def test_passed_reflects_configured_limits(self):
        self.assertTrue(QcMetric(value=Decimal("5"), lower_limit=Decimal("2"), upper_limit=Decimal("8")).passed)
        self.assertFalse(QcMetric(value=Decimal("9"), lower_limit=Decimal("2"), upper_limit=Decimal("8")).passed)


class AssayRunApiTests(APITestCase):
    def setUp(self):
        self.operator = get_user_model().objects.create_user(username="operator", password="test-pass")
        self.viewer = get_user_model().objects.create_user(username="viewer", password="test-pass")
        self.organization = Organization.objects.create(name="Synthetic Lab", slug="synthetic-lab")
        self.other_organization = Organization.objects.create(name="Other Lab", slug="other-lab")
        Membership.objects.create(
            organization=self.organization,
            user=self.operator,
            role=Membership.Role.OPERATOR,
        )
        Membership.objects.create(
            organization=self.organization,
            user=self.viewer,
            role=Membership.Role.VIEWER,
        )
        self.run = AssayRun.objects.create(
            organization=self.organization,
            external_id="RUN-001",
            assay_type="Synthetic Panel",
            created_by=self.operator,
        )
        AssayRun.objects.create(
            organization=self.other_organization,
            external_id="OTHER-001",
            assay_type="Other Panel",
            created_by=self.operator,
        )

    def test_lists_only_runs_from_member_organizations(self):
        self.client.force_authenticate(self.viewer)

        response = self.client.get("/api/runs/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["external_id"] for item in response.data["results"]], ["RUN-001"])

    def test_viewer_cannot_create_run(self):
        self.client.force_authenticate(self.viewer)

        response = self.client.post(
            "/api/runs/",
            {
                "organization": self.organization.id,
                "external_id": "RUN-002",
                "assay_type": "Synthetic Panel",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_cannot_update_run(self):
        self.client.force_authenticate(self.viewer)

        response = self.client.patch(
            f"/api/runs/{self.run.id}/",
            {"assay_type": "Changed Panel"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_operator_can_transition_run_and_creates_audit_event(self):
        self.client.force_authenticate(self.operator)

        response = self.client.post(
            f"/api/runs/{self.run.id}/transition/",
            {"status": AssayRun.Status.READY, "note": "Inputs validated"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.run.refresh_from_db()
        self.assertEqual(self.run.status, AssayRun.Status.READY)
        self.assertTrue(
            AuditEvent.objects.filter(object_id=str(self.run.id), action="STATUS_TRANSITION").exists()
        )

    def test_rejects_invalid_state_transition(self):
        self.client.force_authenticate(self.operator)

        response = self.client.post(
            f"/api/runs/{self.run.id}/transition/",
            {"status": AssayRun.Status.RELEASED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
