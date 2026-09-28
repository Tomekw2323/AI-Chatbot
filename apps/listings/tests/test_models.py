from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.listings.models import InvalidTransitionError, Listing, RoomAvailabilityBlock
from apps.listings.services import expire_due_listings
from apps.organizations.tests.factories import OrganizationFactory

from .factories import ListingFactory

pytestmark = pytest.mark.django_db


def test_slug_and_absolute_url() -> None:
    listing = ListingFactory.create(title="Gabinet na godziny – Wrocław Śródmieście")
    assert listing.slug == "gabinet-na-godziny-wroclaw-srodmiescie"
    assert listing.get_absolute_url() == f"/ogloszenia/{listing.pk}/{listing.slug}/"


class TestLifecycle:
    def test_new_listing_is_draft_and_not_public(self) -> None:
        listing = ListingFactory.create()
        assert listing.status == Listing.Status.DRAFT
        assert not listing.is_publicly_visible
        assert listing not in Listing.objects.public()

    def test_publish_sets_dates(self, settings) -> None:
        settings.LISTING_DEFAULT_LIFETIME_DAYS = 10
        listing = ListingFactory.create()
        listing.publish()
        listing.save()
        assert listing.status == Listing.Status.PUBLISHED
        assert listing.published_at is not None
        assert listing.expires_at is not None
        assert listing.expires_at - listing.published_at == timedelta(days=10)
        assert listing in Listing.objects.public()

    def test_archived_is_final(self) -> None:
        listing = ListingFactory.create()
        listing.archive()
        with pytest.raises(InvalidTransitionError):
            listing.publish()

    def test_published_cannot_be_published_again(self) -> None:
        listing = ListingFactory.create(published=True)
        with pytest.raises(InvalidTransitionError):
            listing.publish()

    def test_expired_can_be_republished(self) -> None:
        listing = ListingFactory.create(published=True)
        listing.expire()
        listing.publish()
        assert listing.status == Listing.Status.PUBLISHED

    def test_expire_due_listings(self) -> None:
        past = timezone.now() - timedelta(minutes=1)
        due = ListingFactory.create(published=True, expires_at=past)
        fresh = ListingFactory.create(published=True)
        assert expire_due_listings() == 1
        due.refresh_from_db()
        fresh.refresh_from_db()
        assert due.status == Listing.Status.EXPIRED
        assert fresh.status == Listing.Status.PUBLISHED


class TestPublicVisibility:
    def test_past_expiry_hidden_even_before_command_runs(self) -> None:
        listing = ListingFactory.create(
            published=True, expires_at=timezone.now() - timedelta(seconds=1)
        )
        assert listing not in Listing.objects.public()
        assert not listing.is_publicly_visible

    def test_flagged_listing_hidden(self) -> None:
        listing = ListingFactory.create(published=True, is_flagged=True)
        assert listing not in Listing.objects.public()
        assert not listing.is_publicly_visible

    def test_blocked_organization_hides_its_listings(self) -> None:
        listing = ListingFactory.create(
            published=True, organization=OrganizationFactory.create(is_blocked=True)
        )
        assert listing not in Listing.objects.public()
        assert not listing.is_publicly_visible


class TestValidation:
    def test_room_rental_requires_price(self) -> None:
        listing = ListingFactory.build(kind=Listing.Kind.ROOM_RENTAL)
        with pytest.raises(ValidationError) as exc:
            listing.full_clean()
        assert {"price_amount", "price_unit"} <= set(exc.value.message_dict)

    def test_room_rental_with_price_is_valid(self) -> None:
        listing = ListingFactory.create(room=True)
        listing.full_clean()
        assert listing.price_amount == Decimal("50.00")

    def test_job_seeking_cannot_belong_to_organization(self) -> None:
        listing = ListingFactory.create(
            kind=Listing.Kind.JOB_SEEKING, organization=OrganizationFactory.create()
        )
        with pytest.raises(ValidationError) as exc:
            listing.full_clean()
        assert "organization" in exc.value.message_dict

    def test_salary_range_validated_and_constrained(self) -> None:
        listing = ListingFactory.build(salary_min=9000, salary_max=5000)
        with pytest.raises(ValidationError):
            listing.clean()
        with pytest.raises(IntegrityError):
            ListingFactory.create(salary_min=9000, salary_max=5000)

    def test_availability_block_end_after_start(self) -> None:
        from datetime import time

        listing = ListingFactory.create(room=True)
        with pytest.raises(IntegrityError):
            RoomAvailabilityBlock.objects.create(
                listing=listing, weekday=0, start_time=time(18), end_time=time(10)
            )
