from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Membership, Organization


class MeApiTests(APITestCase):
    def test_returns_current_user_memberships(self):
        user = get_user_model().objects.create_user(username="operator", password="test-pass")
        organization = Organization.objects.create(name="Synthetic Lab", slug="synthetic-lab")
        Membership.objects.create(
            organization=organization,
            user=user,
            role=Membership.Role.OPERATOR,
        )
        self.client.force_authenticate(user)

        response = self.client.get("/api/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["memberships"][0]["organization_slug"], "synthetic-lab")
