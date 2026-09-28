"""Clinics, practices, NGOs and public institutions, plus who can act for them."""

from typing import Any

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import City, TimeStampedModel
from apps.core.text import unique_slug


class OrganizationQuerySet(models.QuerySet["Organization"]):
    def public(self) -> "OrganizationQuerySet":
        return self.filter(is_public=True, is_blocked=False)


class Organization(TimeStampedModel):
    class Kind(models.TextChoices):
        CLINIC = "clinic", _("Poradnia / klinika")
        PRIVATE_PRACTICE = "private_practice", _("Gabinet prywatny")
        NGO = "ngo", _("Fundacja / stowarzyszenie")
        PUBLIC_INSTITUTION = "public_institution", _("Instytucja publiczna (np. OPS, PPP)")
        ROOM_PROVIDER = "room_provider", _("Wynajmujący gabinety")
        OTHER = "other", _("Inna")

    name = models.CharField(_("nazwa"), max_length=200)
    slug = models.SlugField(_("slug"), max_length=220, unique=True, blank=True)
    kind = models.CharField(_("rodzaj"), max_length=32, choices=Kind.choices, default=Kind.CLINIC)
    description = models.TextField(_("opis"), blank=True)
    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="organizations",
        verbose_name=_("miasto"),
    )
    address = models.CharField(_("adres"), max_length=255, blank=True)
    website = models.URLField(_("strona www"), blank=True)
    contact_email = models.EmailField(_("e-mail kontaktowy"), blank=True)
    contact_phone = models.CharField(_("telefon kontaktowy"), max_length=32, blank=True)
    tax_id = models.CharField(_("NIP"), max_length=16, blank=True)
    is_public = models.BooleanField(_("widoczna publicznie"), default=True)
    is_verified = models.BooleanField(
        _("zweryfikowana"),
        default=False,
        help_text=_("Ustawiane przez moderatora po weryfikacji organizacji."),
    )
    is_blocked = models.BooleanField(
        _("zablokowana przez moderację"),
        default=False,
        help_text=_("Zablokowana organizacja i jej ogłoszenia są ukryte."),
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="Membership",
        related_name="organizations",
        verbose_name=_("członkowie"),
    )

    objects = OrganizationQuerySet.as_manager()

    class Meta:
        verbose_name = _("organizacja")
        verbose_name_plural = _("organizacje")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = unique_slug(
                self.name,
                lambda s: Organization.objects.filter(slug=s).exclude(pk=self.pk).exists(),
                max_length=200,
            )
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("organizations:detail", kwargs={"slug": self.slug})


class Membership(TimeStampedModel):
    class Role(models.TextChoices):
        OWNER = "owner", _("Właściciel")
        ADMIN = "admin", _("Administrator")
        MEMBER = "member", _("Członek zespołu")

    MANAGER_ROLES = (Role.OWNER, Role.ADMIN)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name=_("organizacja"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name=_("użytkownik"),
    )
    role = models.CharField(_("rola"), max_length=16, choices=Role.choices, default=Role.MEMBER)
    job_title = models.CharField(_("stanowisko"), max_length=120, blank=True)

    class Meta:
        verbose_name = _("członkostwo")
        verbose_name_plural = _("członkostwa")
        constraints = [
            models.UniqueConstraint(fields=("organization", "user"), name="uniq_membership"),
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.organization} ({self.get_role_display()})"

    @property
    def can_manage(self) -> bool:
        return self.role in self.MANAGER_ROLES
