"""Listings: job / internship / volunteering offers, job-seeking posts, room rentals.

All kinds share one table (ADR 0006) so a single filterable list page and one
moderation queue cover the whole board. Kind-specific fields are nullable and
validated in ``Listing.clean``.

Lifecycle::

    draft ──publish──▶ published ──(expires_at passed)──▶ expired
      │                   │                                  │
      └──archive──▶ archived ◀──archive──────────────────────┘
                                   expired ──publish──▶ published

Moderation is orthogonal to the lifecycle: ``is_flagged`` hides a listing from
public pages regardless of its status.
"""

from datetime import timedelta
from typing import Any, ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_stubs_ext import StrOrPromise

from apps.core.models import City, Specialization, TimeStampedModel
from apps.core.text import slugify_pl
from apps.organizations.models import Organization


class InvalidTransitionError(Exception):
    pass


class ListingQuerySet(models.QuerySet["Listing"]):
    def public(self) -> "ListingQuerySet":
        """Listings anyone may see: published, not expired, not moderated away."""
        now = timezone.now()
        return self.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now),
            status=Listing.Status.PUBLISHED,
            is_flagged=False,
        ).exclude(organization__is_blocked=True)

    def due_to_expire(self) -> "ListingQuerySet":
        return self.filter(status=Listing.Status.PUBLISHED, expires_at__lte=timezone.now())


class Listing(TimeStampedModel):
    class Kind(models.TextChoices):
        JOB = "job", _("Oferta pracy")
        INTERNSHIP = "internship", _("Staż / praktyki")
        VOLUNTEERING = "volunteering", _("Wolontariat")
        JOB_SEEKING = "job_seeking", _("Szukam pracy / stażu")
        ROOM_RENTAL = "room_rental", _("Wynajem gabinetu")

    class Status(models.TextChoices):
        DRAFT = "draft", _("Szkic")
        PUBLISHED = "published", _("Opublikowane")
        EXPIRED = "expired", _("Wygasłe")
        ARCHIVED = "archived", _("Zarchiwizowane")

    class EmploymentType(models.TextChoices):
        EMPLOYMENT_CONTRACT = "employment_contract", _("Umowa o pracę")
        B2B = "b2b", _("B2B")
        CIVIL_CONTRACT = "civil_contract", _("Umowa zlecenie / o dzieło")
        UNPAID = "unpaid", _("Bezpłatne")
        OTHER = "other", _("Inna")

    class WorkMode(models.TextChoices):
        ON_SITE = "on_site", _("Stacjonarnie")
        HYBRID = "hybrid", _("Hybrydowo")
        REMOTE = "remote", _("Zdalnie")

    class SalaryPeriod(models.TextChoices):
        HOUR = "hour", _("za godzinę")
        SESSION = "session", _("za sesję")
        MONTH = "month", _("miesięcznie")

    class PriceUnit(models.TextChoices):
        HOUR = "hour", _("za godzinę")
        DAY = "day", _("za dzień")
        MONTH = "month", _("za miesiąc")

    # Polish URL segments used for SEO-friendly list pages, e.g. /ogloszenia/praca/wroclaw/.
    KIND_URL_SLUGS: ClassVar[dict[str, str]] = {
        Kind.JOB: "praca",
        Kind.INTERNSHIP: "staze",
        Kind.VOLUNTEERING: "wolontariat",
        Kind.JOB_SEEKING: "szukam-pracy",
        Kind.ROOM_RENTAL: "gabinety",
    }
    OFFER_KINDS: ClassVar[set[str]] = {Kind.JOB, Kind.INTERNSHIP, Kind.VOLUNTEERING}
    ALLOWED_TRANSITIONS: ClassVar[dict[str, set[str]]] = {
        Status.DRAFT: {Status.PUBLISHED, Status.ARCHIVED},
        Status.PUBLISHED: {Status.EXPIRED, Status.ARCHIVED},
        Status.EXPIRED: {Status.PUBLISHED, Status.ARCHIVED},
        Status.ARCHIVED: set(),
    }

    kind = models.CharField(_("rodzaj ogłoszenia"), max_length=20, choices=Kind.choices)
    title = models.CharField(_("tytuł"), max_length=160)
    slug = models.SlugField(_("slug"), max_length=180, blank=True)
    description = models.TextField(_("opis"))
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listings",
        verbose_name=_("autor"),
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="listings",
        verbose_name=_("w imieniu organizacji"),
        help_text=_("Zostaw puste, aby dodać ogłoszenie jako osoba prywatna."),
    )
    city = models.ForeignKey(
        City, on_delete=models.PROTECT, related_name="listings", verbose_name=_("miasto")
    )
    address = models.CharField(_("adres / dzielnica"), max_length=255, blank=True)
    specializations = models.ManyToManyField(
        Specialization, blank=True, related_name="listings", verbose_name=_("kategorie")
    )
    contact_email = models.EmailField(
        _("e-mail do kontaktu"),
        blank=True,
        help_text=_("Na ten adres trafią wiadomości. Domyślnie e-mail autora."),
    )

    status = models.CharField(
        _("status"), max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    published_at = models.DateTimeField(_("opublikowano"), null=True, blank=True)
    expires_at = models.DateTimeField(_("wygasa"), null=True, blank=True, db_index=True)
    is_flagged = models.BooleanField(
        _("ukryte przez moderację"),
        default=False,
        help_text=_("Oflagowane ogłoszenie nie jest widoczne publicznie, niezależnie od statusu."),
    )
    moderation_note = models.TextField(_("notatka moderatora"), blank=True)

    # Offers and job-seeking posts
    employment_type = models.CharField(
        _("forma zatrudnienia"), max_length=32, choices=EmploymentType.choices, blank=True
    )
    work_mode = models.CharField(
        _("tryb pracy"), max_length=16, choices=WorkMode.choices, blank=True
    )
    salary_min = models.PositiveIntegerField(_("wynagrodzenie od (PLN)"), null=True, blank=True)
    salary_max = models.PositiveIntegerField(_("wynagrodzenie do (PLN)"), null=True, blank=True)
    salary_period = models.CharField(
        _("okres wynagrodzenia"), max_length=16, choices=SalaryPeriod.choices, blank=True
    )

    # Room rentals
    price_amount = models.DecimalField(
        _("cena (PLN)"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    price_unit = models.CharField(
        _("jednostka ceny"), max_length=16, choices=PriceUnit.choices, blank=True
    )
    room_area_m2 = models.PositiveSmallIntegerField(_("powierzchnia (m²)"), null=True, blank=True)
    amenities = models.CharField(
        _("wyposażenie"),
        max_length=255,
        blank=True,
        help_text=_("Np. fotele, kozetka, klimatyzacja, poczekalnia."),
    )
    availability_description = models.TextField(
        _("dostępność – opis"),
        blank=True,
        help_text=_("Np. „wtorki i czwartki po 16:00, soboty cały dzień”."),
    )

    objects = ListingQuerySet.as_manager()

    class Meta:
        verbose_name = _("ogłoszenie")
        verbose_name_plural = _("ogłoszenia")
        ordering = ("-published_at", "-created_at")
        indexes = [models.Index(fields=("status", "kind", "city"))]
        constraints = [
            models.CheckConstraint(
                condition=Q(salary_min__isnull=True)
                | Q(salary_max__isnull=True)
                | Q(salary_min__lte=models.F("salary_max")),
                name="listing_salary_range_valid",
            ),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.slug = slugify_pl(self.title)[:180] or "ogloszenie"
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("listings:detail", kwargs={"pk": self.pk, "slug": self.slug})

    def clean(self) -> None:
        errors: dict[str, StrOrPromise] = {}
        if self.kind == self.Kind.JOB_SEEKING and self.organization_id:
            errors["organization"] = _("Ogłoszenie „szukam pracy” dodaje się jako osoba prywatna.")
        if self.kind == self.Kind.ROOM_RENTAL:
            if self.price_amount is None:
                errors["price_amount"] = _("Podaj cenę wynajmu.")
            if not self.price_unit:
                errors["price_unit"] = _("Wybierz jednostkę ceny.")
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            errors["salary_max"] = _("Górna granica musi być większa lub równa dolnej.")
        if errors:
            raise ValidationError(errors)

    # -- lifecycle ---------------------------------------------------------

    @property
    def kind_url_slug(self) -> str:
        return self.KIND_URL_SLUGS[self.kind]

    @property
    def is_room_rental(self) -> bool:
        return self.kind == self.Kind.ROOM_RENTAL

    @property
    def is_publicly_visible(self) -> bool:
        return (
            self.status == self.Status.PUBLISHED
            and not self.is_flagged
            and (self.expires_at is None or self.expires_at > timezone.now())
            and not (self.organization is not None and self.organization.is_blocked)
        )

    def can_transition_to(self, status: str) -> bool:
        return status in self.ALLOWED_TRANSITIONS[self.status]

    def _transition(self, status: str) -> None:
        if not self.can_transition_to(status):
            raise InvalidTransitionError(f"{self.status} -> {status}")
        self.status = status

    def publish(self, lifetime_days: int | None = None) -> None:
        self._transition(self.Status.PUBLISHED)
        now = timezone.now()
        days = lifetime_days or settings.LISTING_DEFAULT_LIFETIME_DAYS
        self.published_at = now
        self.expires_at = now + timedelta(days=days)

    def archive(self) -> None:
        self._transition(self.Status.ARCHIVED)

    def expire(self) -> None:
        self._transition(self.Status.EXPIRED)


class RoomAvailabilityBlock(models.Model):
    """Recurring weekly time block when a room can be rented.

    A deliberately simple precursor of the Phase 2 booking calendar.
    """

    class Weekday(models.IntegerChoices):
        MONDAY = 0, _("Poniedziałek")
        TUESDAY = 1, _("Wtorek")
        WEDNESDAY = 2, _("Środa")
        THURSDAY = 3, _("Czwartek")
        FRIDAY = 4, _("Piątek")
        SATURDAY = 5, _("Sobota")
        SUNDAY = 6, _("Niedziela")

    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="availability_blocks",
        verbose_name=_("ogłoszenie"),
    )
    weekday = models.PositiveSmallIntegerField(_("dzień tygodnia"), choices=Weekday.choices)
    start_time = models.TimeField(_("od"))
    end_time = models.TimeField(_("do"))

    class Meta:
        verbose_name = _("blok dostępności")
        verbose_name_plural = _("bloki dostępności")
        ordering = ("weekday", "start_time")
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=models.F("start_time")),
                name="availability_block_end_after_start",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_weekday_display()} {self.start_time:%H:%M}–{self.end_time:%H:%M}"

    def clean(self) -> None:
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError(
                {"end_time": _("Godzina końca musi być późniejsza niż początku.")}
            )


class Inquiry(TimeStampedModel):
    """Message sent through a listing's contact form (delivered by email).

    ``sender`` is empty for guests (Turnstile-protected form) and for senders who
    deleted their account.
    """

    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="inquiries", verbose_name=_("ogłoszenie")
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_inquiries",
        verbose_name=_("nadawca"),
    )
    sender_name = models.CharField(_("imię i nazwisko nadawcy"), max_length=150, blank=True)
    sender_email = models.EmailField(_("e-mail nadawcy"))
    message = models.TextField(_("wiadomość"), max_length=5000)
    recipient_email = models.EmailField(_("e-mail odbiorcy"))
    email_sent = models.BooleanField(_("e-mail wysłany"), default=False)

    class Meta:
        verbose_name = _("zapytanie")
        verbose_name_plural = _("zapytania")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.sender_email} → {self.listing}"


class ListingReport(TimeStampedModel):
    """A user's report that a listing breaks the rules (post-moderation, ADR 0012)."""

    class Reason(models.TextChoices):
        SPAM = "spam", _("Spam lub reklama")
        FRAUD = "fraud", _("Podejrzenie oszustwa")
        INAPPROPRIATE = "inappropriate", _("Treści nieodpowiednie lub nieetyczne")
        OUTDATED = "outdated", _("Nieaktualne ogłoszenie")
        OTHER = "other", _("Inny powód")

    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="reports", verbose_name=_("ogłoszenie")
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="listing_reports",
        verbose_name=_("zgłaszający"),
    )
    reason = models.CharField(_("powód"), max_length=20, choices=Reason.choices)
    message = models.TextField(_("szczegóły"), max_length=1000, blank=True)
    is_resolved = models.BooleanField(_("rozpatrzone"), default=False)

    class Meta:
        verbose_name = _("zgłoszenie ogłoszenia")
        verbose_name_plural = _("zgłoszenia ogłoszeń")
        ordering = ("is_resolved", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("listing", "reporter"),
                condition=Q(reporter__isnull=False),
                name="uniq_report_per_user",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_reason_display()}: {self.listing}"
