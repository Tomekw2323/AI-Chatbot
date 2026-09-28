"""Use cases of the listings module (anything that is more than a single save)."""

import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import User

from .models import Inquiry, Listing

logger = logging.getLogger(__name__)


def expire_due_listings() -> int:
    """Move published listings past ``expires_at`` to ``expired``. Returns the count."""
    return Listing.objects.due_to_expire().update(
        status=Listing.Status.EXPIRED, updated_at=timezone.now()
    )


def recipient_email_for(listing: Listing) -> str:
    return listing.contact_email or listing.author.email


@transaction.atomic
def send_inquiry(listing: Listing, sender: User, message: str) -> Inquiry:
    """Store the inquiry and email it to the listing owner (reply-to: sender).

    Sending is synchronous for the MVP; move to a task queue when volume grows.
    """
    inquiry = Inquiry.objects.create(
        listing=listing,
        sender=sender,
        sender_email=sender.email,
        message=message,
        recipient_email=recipient_email_for(listing),
    )
    body = render_to_string(
        "listings/email/inquiry.txt",
        {"inquiry": inquiry, "listing": listing, "sender": sender, "site_url": settings.SITE_URL},
    )
    email = EmailMessage(
        subject=_("Nowa wiadomość do ogłoszenia: %(title)s") % {"title": listing.title},
        body=body,
        to=[inquiry.recipient_email],
        reply_to=[sender.email],
    )
    try:
        email.send()
    except Exception:
        logger.exception("Failed to send inquiry email", extra={"inquiry_id": inquiry.pk})
    else:
        inquiry.email_sent = True
        inquiry.save(update_fields=["email_sent", "updated_at"])
    return inquiry
