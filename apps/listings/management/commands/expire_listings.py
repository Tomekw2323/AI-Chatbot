from typing import Any

from django.core.management.base import BaseCommand

from apps.listings.services import expire_due_listings


class Command(BaseCommand):
    help = "Mark published listings whose expires_at has passed as expired (run daily via cron)."

    def handle(self, *args: Any, **options: Any) -> None:
        count = expire_due_listings()
        self.stdout.write(self.style.SUCCESS(f"Expired {count} listing(s)."))
