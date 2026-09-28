"""Load a fresh public demo: schema, reference data, fake samples.

Free instances have an ephemeral disk, so this runs on every process start.
Refuses to run unless DEMO_MODE is on, so it cannot touch production Postgres.
"""

from typing import Any

from django.conf import settings
from django.core.management import CommandError, call_command
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Migrate and load fake demo data. Refuses to run outside demo mode."

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.DEMO_MODE:
            raise CommandError("prepare_demo runs only when DEMO_MODE is on.")
        call_command("migrate", "--noinput")
        # createcachetable fails when the table is already there (restart in one boot).
        if "django_cache" not in connection.introspection.table_names():
            call_command("createcachetable")
        call_command("loaddata", "reference_data")
        call_command("seed_demo")
