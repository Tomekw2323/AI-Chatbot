from typing import Any

from django.core.management.base import BaseCommand

from apps.core.ratelimit import purge_old_windows
from apps.listings.services import expire_due_listings, purge_old_inquiries


class Command(BaseCommand):
    help = "Daily cron: expire listings, delete old inquiries and rate-limit counters."

    def handle(self, *args: Any, **options: Any) -> None:
        expired = expire_due_listings()
        inquiries = purge_old_inquiries()
        counters = purge_old_windows()
        self.stdout.write(
            self.style.SUCCESS(
                f"Expired {expired} listing(s), deleted {inquiries} inquiry(ies) "
                f"and {counters} rate-limit window(s)."
            )
        )
