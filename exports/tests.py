from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from accounts.models import Organization
from assays.models import AssayRun
from .models import ExportJob
from .tasks import generate_run_manifest


class GenerateRunManifestTests(TestCase):
    def test_generates_csv_for_organization_runs(self):
        user = get_user_model().objects.create_user(username="operator", password="test-pass")
        organization = Organization.objects.create(name="Synthetic Lab", slug="synthetic-lab")
        AssayRun.objects.create(
            organization=organization,
            external_id="RUN-001",
            assay_type="Synthetic Panel",
            created_by=user,
        )
        job = ExportJob.objects.create(organization=organization, requested_by=user)

        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            generate_run_manifest(str(job.id))
            job.refresh_from_db()
            content = job.file.read().decode("utf-8")

        self.assertEqual(job.status, ExportJob.Status.READY)
        self.assertIn("RUN-001", content)
