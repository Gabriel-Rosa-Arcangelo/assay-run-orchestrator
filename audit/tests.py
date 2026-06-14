from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Membership, Organization
from .models import AuditEvent


class AuditEventApiTests(APITestCase):
    def test_scopes_events_by_membership(self):
        user = get_user_model().objects.create_user(username="viewer", password="test-pass")
        organization = Organization.objects.create(name="Synthetic Lab", slug="synthetic-lab")
        other_organization = Organization.objects.create(name="Other Lab", slug="other-lab")
        Membership.objects.create(organization=organization, user=user, role=Membership.Role.VIEWER)
        AuditEvent.objects.create(
            organization=organization,
            actor=user,
            object_type="AssayRun",
            object_id="run-1",
            action="RUN_CREATED",
        )
        AuditEvent.objects.create(
            organization=other_organization,
            object_type="AssayRun",
            object_id="run-2",
            action="RUN_CREATED",
        )
        self.client.force_authenticate(user)

        response = self.client.get("/api/audit-events/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["object_id"] for item in response.data["results"]], ["run-1"])
