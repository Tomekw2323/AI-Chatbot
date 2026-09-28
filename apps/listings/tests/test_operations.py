"""Commands, admin moderation, template tags and service edge cases."""

from datetime import time, timedelta

import pytest
from django.core import mail
from django.core.management import CommandError, call_command
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.core.tests.factories import CityFactory
from apps.listings.forms import ListingForm
from apps.listings.models import Inquiry, Listing, ListingReport, RoomAvailabilityBlock
from apps.listings.services import purge_old_inquiries, send_inquiry
from apps.organizations.tests.factories import MembershipFactory, OrganizationFactory
from apps.profiles.tests.factories import SpecialistProfileFactory

from .factories import ListingFactory

pytestmark = pytest.mark.django_db


class TestCommands:
    def test_daily_maintenance(self, capsys, settings) -> None:
        settings.INQUIRY_RETENTION_DAYS = 30
        ListingFactory.create(published=True, expires_at=timezone.now() - timedelta(days=1))
        old = send_inquiry(
            ListingFactory.create(published=True), "x", sender=None, sender_email="a@example.com"
        )
        Inquiry.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=31))
        call_command("daily_maintenance")
        assert "Expired 1 listing(s), deleted 1 inquiry(ies)" in capsys.readouterr().out
        assert not Inquiry.objects.exists()

    def test_expire_listings(self, capsys) -> None:
        ListingFactory.create(published=True, expires_at=timezone.now() - timedelta(days=1))
        call_command("expire_listings")
        assert "Expired 1 listing(s)" in capsys.readouterr().out

    def test_seed_demo_is_idempotent(self, settings) -> None:
        settings.DEBUG = True
        call_command("seed_demo", stdout=None)
        counts = (User.objects.count(), Listing.objects.count())
        call_command("seed_demo", stdout=None)
        assert (User.objects.count(), Listing.objects.count()) == counts
        assert Listing.objects.public().count() == 7
        assert Listing.objects.filter(kind=Listing.Kind.JOB, city__slug="krakow").exists()
        assert Listing.objects.filter(kind=Listing.Kind.ROOM_RENTAL, city__slug="wroclaw").exists()
        assert RoomAvailabilityBlock.objects.count() == 3

    def test_seed_demo_refuses_without_debug(self, settings) -> None:
        settings.DEBUG = False
        settings.DEMO_MODE = False
        with pytest.raises(CommandError):
            call_command("seed_demo")


class TestServices:
    def test_purge_keeps_recent_inquiries(self, settings) -> None:
        settings.INQUIRY_RETENTION_DAYS = 30
        send_inquiry(ListingFactory.create(), "x", sender=None, sender_email="a@example.com")
        assert purge_old_inquiries() == 0

    def test_email_failure_keeps_inquiry(self, monkeypatch) -> None:
        def fail(*args: object, **kwargs: object) -> None:
            raise ConnectionError("SMTP down")

        monkeypatch.setattr("django.core.mail.EmailMessage.send", fail)
        inquiry = send_inquiry(
            ListingFactory.create(published=True), "x", sender=None, sender_email="a@example.com"
        )
        inquiry.refresh_from_db()
        assert inquiry.email_sent is False
        assert not mail.outbox


class TestAdminModeration:
    @pytest.fixture
    def staff_client(self, client):
        client.force_login(User.objects.create_superuser(email="mod@example.com", password="x"))
        return client

    def changelist(self, model: str) -> str:
        return reverse(f"admin:listings_{model}_changelist")

    def test_flag_and_unflag_actions(self, staff_client) -> None:
        listing = ListingFactory.create(published=True)
        data = {"action": "flag_listings", "_selected_action": [listing.pk]}
        staff_client.post(self.changelist("listing"), data)
        listing.refresh_from_db()
        assert listing.is_flagged
        staff_client.post(self.changelist("listing"), {**data, "action": "unflag_listings"})
        listing.refresh_from_db()
        assert not listing.is_flagged

    def test_resolve_reports_action(self, staff_client) -> None:
        report = ListingReport.objects.create(
            listing=ListingFactory.create(), reporter=UserFactory.create(), reason="spam"
        )
        staff_client.post(
            self.changelist("listingreport"),
            {"action": "mark_resolved", "_selected_action": [report.pk]},
        )
        report.refresh_from_db()
        assert report.is_resolved

    @pytest.mark.parametrize("model", ["listing", "inquiry", "listingreport"])
    def test_changelists_render(self, staff_client, model: str) -> None:
        ListingFactory.create(published=True)
        assert staff_client.get(self.changelist(model)).status_code == 200

    def test_inquiries_cannot_be_added_manually(self, staff_client) -> None:
        assert staff_client.get(reverse("admin:listings_inquiry_add")).status_code == 403

    def test_non_staff_cannot_access_admin(self, client) -> None:
        client.force_login(UserFactory.create())
        response = client.get(self.changelist("listing"))
        assert response.status_code == 302


class TestTemplateTagsOnPages:
    def test_organization_page_lists_only_public_listings(self, client) -> None:
        organization = OrganizationFactory.create()
        ListingFactory.create(published=True, organization=organization, title="Publiczne")
        ListingFactory.create(organization=organization, title="Szkic firmy")
        content = client.get(organization.get_absolute_url()).content.decode()
        assert "Publiczne" in content
        assert "Szkic firmy" not in content

    def test_profile_page_lists_personal_listings(self, client) -> None:
        profile = SpecialistProfileFactory.create()
        ListingFactory.create(
            published=True, author=profile.user, kind=Listing.Kind.JOB_SEEKING, title="Szukam"
        )
        ListingFactory.create(
            published=True,
            author=profile.user,
            organization=OrganizationFactory.create(),
            title="Firmowe",
        )
        content = client.get(profile.get_absolute_url()).content.decode()
        assert "Szukam" in content
        assert "Firmowe" not in content

    def test_pagination_keeps_filters(self, client, settings) -> None:
        settings.LISTINGS_PER_PAGE = 1
        city = CityFactory.create(slug="lodz")
        ListingFactory.create_batch(2, published=True, city=city)
        content = client.get(reverse("listings:list"), {"city": "lodz"}).content.decode()
        assert "?city=lodz&amp;page=2" in content


class TestEdgeCases:
    def test_job_seeking_form_drops_organization(self) -> None:
        membership = MembershipFactory.create()
        form = ListingForm(
            {
                "kind": "job_seeking",
                "title": "Szukam stażu",
                "description": "Opis",
                "city": CityFactory.create().pk,
                "organization": membership.organization.pk,
            },
            instance=Listing(author=membership.user),
            user=membership.user,
        )
        assert form.is_valid(), form.errors
        assert form.cleaned_data["organization"] is None

    def test_unknown_transition_action_is_404(self, client) -> None:
        listing = ListingFactory.create()
        client.force_login(listing.author)
        url = reverse("listings:transition", kwargs={"pk": listing.pk, "action": "expire"})
        assert client.post(url).status_code == 404

    def test_empty_member_inquiry_is_rejected(self, client) -> None:
        listing = ListingFactory.create(published=True)
        client.force_login(UserFactory.create())
        response = client.post(reverse("listings:inquiry", kwargs={"pk": listing.pk}), {})
        assert response.status_code == 400
        assert not Inquiry.objects.exists()

    def test_availability_block_validation_and_label(self) -> None:
        from django.core.exceptions import ValidationError

        block = RoomAvailabilityBlock(
            listing=ListingFactory.create(room=True),
            weekday=RoomAvailabilityBlock.Weekday.TUESDAY,
            start_time=time(16),
            end_time=time(21),
        )
        block.full_clean()
        assert str(block) == "Wtorek 16:00–21:00"
        block.end_time = time(15)
        with pytest.raises(ValidationError):
            block.clean()
