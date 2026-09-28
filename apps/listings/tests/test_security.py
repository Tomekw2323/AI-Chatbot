"""Security controls around listings (see docs/security.md)."""

import pytest
from django.core import mail
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.core import captcha
from apps.core.tests.factories import CityFactory
from apps.listings.models import Inquiry, Listing, ListingReport
from apps.organizations.models import Membership
from apps.organizations.tests.factories import MembershipFactory

from .factories import ListingFactory

pytestmark = pytest.mark.django_db


def listing_form(city_pk: int, **overrides: str) -> dict[str, str]:
    data = {
        "kind": "job",
        "title": "Oferta",
        "description": "Opis",
        "city": str(city_pk),
        "availability-TOTAL_FORMS": "0",
        "availability-INITIAL_FORMS": "0",
        "action": "save",
    }
    data.update(overrides)
    return data


class TestObjectLevelAuthorization:
    """IDOR: every state-changing endpoint checks ownership of the given pk."""

    @pytest.mark.parametrize(
        ("url_name", "kwargs", "method"),
        [
            ("listings:update", {}, "get"),
            ("listings:update", {}, "post"),
            ("listings:delete", {}, "post"),
            ("listings:transition", {"action": "publish"}, "post"),
            ("listings:transition", {"action": "archive"}, "post"),
        ],
    )
    def test_stranger_is_forbidden(self, client, url_name, kwargs, method) -> None:
        listing = ListingFactory.create(published=True, title="Nie ruszać")
        client.force_login(UserFactory.create())
        url = reverse(url_name, kwargs={"pk": listing.pk, **kwargs})
        response = getattr(client, method)(url, listing_form(listing.city_id, title="Hacked"))
        assert response.status_code == 403
        listing.refresh_from_db()
        assert listing.title == "Nie ruszać"
        assert listing.status == Listing.Status.PUBLISHED

    def test_plain_member_cannot_edit_organization_listing(self, client) -> None:
        membership = MembershipFactory.create(role=Membership.Role.MEMBER)
        listing = ListingFactory.create(organization=membership.organization)
        client.force_login(membership.user)
        url = reverse("listings:update", kwargs={"pk": listing.pk})
        assert client.get(url).status_code == 403

    def test_unknown_pk_is_404(self, client) -> None:
        client.force_login(UserFactory.create())
        assert client.post(reverse("listings:delete", kwargs={"pk": 999999})).status_code == 404


class TestMassAssignment:
    def test_moderation_and_ownership_fields_cannot_be_posted(self, client) -> None:
        listing = ListingFactory.create(is_flagged=True, moderation_note="spam")
        other = UserFactory.create()
        client.force_login(listing.author)
        data = listing_form(
            listing.city_id,
            is_flagged="",
            moderation_note="",
            status="published",
            author=str(other.pk),
            expires_at="2099-01-01",
        )
        client.post(reverse("listings:update", kwargs={"pk": listing.pk}), data)
        listing.refresh_from_db()
        assert listing.is_flagged is True
        assert listing.moderation_note == "spam"
        assert listing.status == Listing.Status.DRAFT
        assert listing.author != other

    def test_flagged_listing_stays_hidden_after_republish(self, client) -> None:
        listing = ListingFactory.create(is_flagged=True)
        client.force_login(listing.author)
        client.post(reverse("listings:transition", kwargs={"pk": listing.pk, "action": "publish"}))
        listing.refresh_from_db()
        assert listing.status == Listing.Status.PUBLISHED
        assert listing not in Listing.objects.public()


class TestXss:
    PAYLOAD = '<script>alert("x")</script><img src=x onerror=alert(1)>'

    def test_listing_content_is_escaped(self, client) -> None:
        listing = ListingFactory.create(
            published=True, title=self.PAYLOAD, description=self.PAYLOAD, address=self.PAYLOAD
        )
        for url in (listing.get_absolute_url(), reverse("listings:list"), reverse("home")):
            content = client.get(url).content.decode()
            assert "<script>alert" not in content
            assert "<img src=x" not in content
            assert "&lt;script&gt;" in content

    def test_inquiry_email_is_plain_text(self, client) -> None:
        listing = ListingFactory.create(published=True)
        client.force_login(UserFactory.create())
        client.post(reverse("listings:inquiry", kwargs={"pk": listing.pk}), {"message": "<b>x</b>"})
        message = mail.outbox[0]
        assert not isinstance(message, mail.EmailMultiAlternatives)
        assert message.content_subtype == "plain"


class TestOpenRedirect:
    def post(self, client, next_url: str):
        listing = ListingFactory.create()
        client.force_login(listing.author)
        url = reverse("listings:transition", kwargs={"pk": listing.pk, "action": "publish"})
        return client.post(url, {"next": next_url})

    @pytest.mark.parametrize("target", ["https://evil.example/", "//evil.example/", "javascript:x"])
    def test_external_next_is_ignored(self, client, target: str) -> None:
        assert self.post(client, target)["Location"] == reverse("dashboard")

    def test_local_next_is_followed(self, client) -> None:
        assert self.post(client, "/ogloszenia/")["Location"] == "/ogloszenia/"


class TestVerifiedEmailRequired:
    @pytest.fixture
    def unverified(self, client):
        user = UserFactory.create(verified=False)
        client.force_login(user)
        return user

    def test_cannot_create_listing(self, client, unverified) -> None:
        response = client.post(reverse("listings:create"), listing_form(CityFactory.create().pk))
        assert response.status_code == 200
        assert "account/verified_email_required.html" in [t.name for t in response.templates]
        assert not Listing.objects.exists()
        assert len(mail.outbox) == 1, "a new verification email is sent"

    def test_cannot_publish(self, client, unverified) -> None:
        listing = ListingFactory.create(author=unverified)
        client.post(reverse("listings:transition", kwargs={"pk": listing.pk, "action": "publish"}))
        listing.refresh_from_db()
        assert listing.status == Listing.Status.DRAFT

    def test_cannot_send_inquiry(self, client, unverified) -> None:
        listing = ListingFactory.create(published=True)
        client.post(reverse("listings:inquiry", kwargs={"pk": listing.pk}), {"message": "Hej"})
        assert not Inquiry.objects.exists()

    def test_cannot_report(self, client, unverified) -> None:
        listing = ListingFactory.create(published=True)
        client.post(reverse("listings:report", kwargs={"pk": listing.pk}), {"reason": "spam"})
        assert not ListingReport.objects.exists()


class TestRateLimits:
    def test_listing_creation(self, client, settings) -> None:
        settings.RATE_LIMITS = {**settings.RATE_LIMITS, "listing_create": "2/h/user"}
        client.force_login(UserFactory.create())
        city = CityFactory.create()
        codes = [
            client.post(reverse("listings:create"), listing_form(city.pk)).status_code
            for _ in range(3)
        ]
        assert codes == [302, 302, 429]
        assert Listing.objects.count() == 2

    def test_member_inquiries(self, client, settings) -> None:
        settings.RATE_LIMITS = {**settings.RATE_LIMITS, "inquiry": "1/h/user"}
        listing = ListingFactory.create(published=True)
        client.force_login(UserFactory.create())
        url = reverse("listings:inquiry", kwargs={"pk": listing.pk})
        assert client.post(url, {"message": "1"}).status_code == 302
        assert client.post(url, {"message": "2"}).status_code == 429
        assert Inquiry.objects.count() == 1


@pytest.fixture
def turnstile(settings, monkeypatch):
    """Enable guest contact and make the Turnstile check pass unless told otherwise."""
    settings.TURNSTILE_SITE_KEY = "site-key"
    settings.TURNSTILE_SECRET_KEY = "secret"
    state = {"valid": True}
    monkeypatch.setattr(captcha, "verify", lambda token, ip=None: state["valid"] and bool(token))
    return state


class TestGuestInquiry:
    DATA = {
        "sender_name": "Gość",
        "sender_email": "gosc@example.com",
        "message": "Czy gabinet jest wolny w soboty?",
        captcha.TOKEN_FIELD: "token",
    }

    def test_disabled_without_captcha_keys(self, client) -> None:
        listing = ListingFactory.create(published=True)
        response = client.post(reverse("listings:inquiry", kwargs={"pk": listing.pk}), self.DATA)
        assert response.status_code == 302
        assert reverse("account_login") in response["Location"]
        assert not Inquiry.objects.exists()

    def test_detail_shows_widget_when_enabled(self, client, turnstile) -> None:
        listing = ListingFactory.create(published=True)
        content = client.get(listing.get_absolute_url()).content.decode()
        assert 'class="cf-turnstile" data-sitekey="site-key"' in content
        assert "challenges.cloudflare.com/turnstile" in content

    def test_sends_with_valid_captcha(self, client, turnstile) -> None:
        listing = ListingFactory.create(published=True, contact_email="gabinet@example.com")
        response = client.post(reverse("listings:inquiry", kwargs={"pk": listing.pk}), self.DATA)
        assert response.status_code == 302
        inquiry = Inquiry.objects.get()
        assert inquiry.sender is None
        assert inquiry.sender_name == "Gość"
        assert mail.outbox[0].to == ["gabinet@example.com"]
        assert mail.outbox[0].reply_to == ["gosc@example.com"]
        assert "niezweryfikowany" in mail.outbox[0].body

    def test_rejected_with_invalid_captcha(self, client, turnstile) -> None:
        turnstile["valid"] = False
        listing = ListingFactory.create(published=True)
        response = client.post(reverse("listings:inquiry", kwargs={"pk": listing.pk}), self.DATA)
        assert response.status_code == 400
        assert "nie jesteś robotem" in response.content.decode()
        assert not Inquiry.objects.exists()
        assert not mail.outbox

    def test_rejected_without_token(self, client, turnstile) -> None:
        listing = ListingFactory.create(published=True)
        data = {k: v for k, v in self.DATA.items() if k != captcha.TOKEN_FIELD}
        response = client.post(reverse("listings:inquiry", kwargs={"pk": listing.pk}), data)
        assert response.status_code == 400
        assert not Inquiry.objects.exists()

    def test_guest_rate_limit_per_ip(self, client, settings, turnstile) -> None:
        settings.RATE_LIMITS = {**settings.RATE_LIMITS, "inquiry_guest": "2/h/ip"}
        listing = ListingFactory.create(published=True)
        url = reverse("listings:inquiry", kwargs={"pk": listing.pk})
        codes = [client.post(url, self.DATA).status_code for _ in range(3)]
        assert codes == [302, 302, 429]

    def test_not_for_unpublished_listing(self, client, turnstile) -> None:
        listing = ListingFactory.create()
        response = client.post(reverse("listings:inquiry", kwargs={"pk": listing.pk}), self.DATA)
        assert response.status_code == 403


class TestReports:
    def report(self, client, listing: Listing, **data: str):
        return client.post(
            reverse("listings:report", kwargs={"pk": listing.pk}), {"reason": "spam", **data}
        )

    def test_creates_report(self, client) -> None:
        listing = ListingFactory.create(published=True)
        reporter = UserFactory.create()
        client.force_login(reporter)
        assert self.report(client, listing, message="Podejrzane").status_code == 302
        report = ListingReport.objects.get()
        assert (report.reporter, report.reason, report.message) == (reporter, "spam", "Podejrzane")

    def test_duplicate_report_is_ignored(self, client) -> None:
        listing = ListingFactory.create(published=True)
        client.force_login(UserFactory.create())
        self.report(client, listing)
        self.report(client, listing)
        assert ListingReport.objects.count() == 1

    def test_invalid_reason(self, client) -> None:
        listing = ListingFactory.create(published=True)
        client.force_login(UserFactory.create())
        self.report(client, listing, reason="nonsense")
        assert not ListingReport.objects.exists()

    def test_auto_flag_after_threshold(self, client, settings) -> None:
        settings.LISTING_REPORTS_AUTO_FLAG = 2
        listing = ListingFactory.create(published=True)
        for _ in range(2):
            client.force_login(UserFactory.create())
            self.report(client, listing)
        listing.refresh_from_db()
        assert listing.is_flagged
        assert "automatycznie" in listing.moderation_note
        assert listing not in Listing.objects.public()

    def test_author_and_anonymous_cannot_report(self, client) -> None:
        listing = ListingFactory.create(published=True)
        assert self.report(client, listing).status_code == 302  # to login
        client.force_login(listing.author)
        assert self.report(client, listing).status_code == 403
        assert not ListingReport.objects.exists()

    def test_rate_limited(self, client, settings) -> None:
        settings.RATE_LIMITS = {**settings.RATE_LIMITS, "listing_report": "1/h/user"}
        client.force_login(UserFactory.create())
        self.report(client, ListingFactory.create(published=True))
        assert self.report(client, ListingFactory.create(published=True)).status_code == 429


class TestDelete:
    def test_author_can_delete(self, client) -> None:
        listing = ListingFactory.create()
        client.force_login(listing.author)
        response = client.post(reverse("listings:delete", kwargs={"pk": listing.pk}))
        assert response.status_code == 302
        assert not Listing.objects.exists()

    def test_organization_admin_can_delete(self, client) -> None:
        membership = MembershipFactory.create(role=Membership.Role.ADMIN)
        listing = ListingFactory.create(organization=membership.organization)
        client.force_login(membership.user)
        client.post(reverse("listings:delete", kwargs={"pk": listing.pk}))
        assert not Listing.objects.exists()

    def test_get_not_allowed(self, client) -> None:
        listing = ListingFactory.create()
        client.force_login(listing.author)
        assert client.get(reverse("listings:delete", kwargs={"pk": listing.pk})).status_code == 405
        assert Listing.objects.exists()
