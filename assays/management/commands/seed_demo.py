from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import Membership, Organization
from assays.models import AssayRun, QcMetric


class Command(BaseCommand):
    help = "Create a synthetic organization, users, assay runs, and QC metrics."

    def handle(self, *args, **options):
        organization, _ = Organization.objects.get_or_create(
            slug="synthetic-lab",
            defaults={"name": "Synthetic Lab"},
        )
        users = {}
        for username, role in [
            ("demo-admin", Membership.Role.ADMIN),
            ("demo-operator", Membership.Role.OPERATOR),
            ("demo-viewer", Membership.Role.VIEWER),
        ]:
            user, _ = get_user_model().objects.get_or_create(username=username)
            user.set_password("demo1234")
            user.save(update_fields=["password"])
            Membership.objects.update_or_create(
                organization=organization,
                user=user,
                defaults={"role": role},
            )
            users[role] = user

        run, _ = AssayRun.objects.get_or_create(
            organization=organization,
            external_id="SYNTH-RUN-001",
            defaults={
                "assay_type": "Synthetic Quality Panel",
                "created_by": users[Membership.Role.OPERATOR],
            },
        )
        QcMetric.objects.get_or_create(
            run=run,
            name="signal_quality",
            defaults={"value": "98.5000", "unit": "%", "lower_limit": "95.0000"},
        )
        self.stdout.write(self.style.SUCCESS("Synthetic demo data created."))
