"""Use cases of the listings module (anything that is more than a single save)."""

import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import IntegrityError, transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import User

from .models import Inquiry, Listing, ListingReport

logger = logging.getLogger(__name__)


class DuplicateReportError(Exception):
    pass


def expire_due_listings() -> int:
    """Move published listings past ``expires_at`` to ``expired``. Returns the count."""
    return Listing.objects.due_to_expire().update(
        status=Listing.Status.EXPIRED, updated_at=timezone.now()
    )


def purge_old_inquiries() -> int:
    """Delete inquiries older than the retention period (GDPR storage limitation)."""
    cutoff = timezone.now() - timedelta(days=settings.INQUIRY_RETENTION_DAYS)
    deleted, _ = Inquiry.objects.filter(created_at__lt=cutoff).delete()
    return deleted


def recipient_email_for(listing: Listing) -> str:
    return listing.contact_email or listing.author.email


@transaction.atomic
def send_inquiry(
    listing: Listing,
    message: str,
    *,
    sender: User | None,
    sender_email: str,
    sender_name: str = "",
) -> Inquiry:
    """Store the inquiry and email it to the listing owner (reply-to: sender).

    ``sender`` is None for guests. Sending is synchronous for the MVP; move to a
    task queue when volume grows.
    """
    inquiry = Inquiry.objects.create(
        listing=listing,
        sender=sender,
        sender_name=sender_name or (sender.get_full_name() if sender else ""),
        sender_email=sender_email,
        message=message,
        recipient_email=recipient_email_for(listing),
    )
    body = render_to_string(
        "listings/email/inquiry.txt",
        {"inquiry": inquiry, "listing": listing, "site_url": settings.SITE_URL},
    )
    email = EmailMessage(
        subject=_("Nowa wiadomość do ogłoszenia: %(title)s") % {"title": listing.title},
        body=body,
        to=[inquiry.recipient_email],
        reply_to=[inquiry.sender_email],
    )
    try:
        email.send()
    except Exception:
        # Never log the message or addresses (personal data), only the id.
        logger.exception("Failed to send inquiry email", extra={"inquiry_id": inquiry.pk})
    else:
        inquiry.email_sent = True
        inquiry.save(update_fields=["email_sent", "updated_at"])
    return inquiry


def report_listing(listing: Listing, reporter: User, reason: str, message: str) -> ListingReport:
    """Record a report; enough distinct open reports hide the listing until reviewed."""
    try:
        with transaction.atomic():
            report = ListingReport.objects.create(
                listing=listing, reporter=reporter, reason=reason, message=message
            )
    except IntegrityError as exc:
        raise DuplicateReportError from exc

    open_reports = listing.reports.filter(is_resolved=False).count()
    if not listing.is_flagged and open_reports >= settings.LISTING_REPORTS_AUTO_FLAG:
        listing.is_flagged = True
        listing.moderation_note = (
            f"{listing.moderation_note}\n" if listing.moderation_note else ""
        ) + _("Ukryte automatycznie po %(n)d zgłoszeniach – do weryfikacji.") % {"n": open_reports}
        listing.save(update_fields=["is_flagged", "moderation_note", "updated_at"])
        logger.warning("Listing auto-flagged after reports", extra={"listing_id": listing.pk})
    return report
