"""Specialist profile ("wizytówka").

The profile is deliberately separate from ``accounts.User``: it holds only
professional, publishable data. Phase 3 (patient booking) will expose the same
profile to patients, gated by ``visible_to_patients``; no patient data is ever
stored here (see docs/domain-model.md and ADR 0009).
"""

from typing import Any

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import City, Specialization, TherapyApproach, TimeStampedModel
from apps.core.text import unique_slug


class SpecialistProfileQuerySet(models.QuerySet["SpecialistProfile"]):
    def public(self) -> "SpecialistProfileQuerySet":
        return self.filter(is_public=True, is_blocked=False, user__is_active=True)


class SpecialistProfile(TimeStampedModel):
    class Profession(models.TextChoices):
        PSYCHOLOGIST = "psychologist", _("Psycholog")
        PSYCHOTHERAPIST = "psychotherapist", _("Psychoterapeuta")
        PSYCHOTHERAPIST_IN_TRAINING = (
            "psychotherapist_in_training",
            _("Psychoterapeuta w trakcie szkolenia"),
        )
        PSYCHIATRIST = "psychiatrist", _("Psychiatra")
        SEXOLOGIST = "sexologist", _("Seksuolog")
        COACH = "coach", _("Coach / trener")
        STUDENT = "student", _("Student(ka) psychologii")
        OTHER = "other", _("Inny zawód")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="specialist_profile",
        verbose_name=_("użytkownik"),
    )
    slug = models.SlugField(_("slug"), max_length=120, unique=True, blank=True)
    academic_title = models.CharField(
        _("tytuł"), max_length=40, blank=True, help_text=_("Np. mgr, dr, dr hab.")
    )
    profession = models.CharField(_("zawód"), max_length=40, choices=Profession.choices)
    headline = models.CharField(
        _("nagłówek"), max_length=160, help_text=_("Jedno zdanie o sobie, widoczne na liście.")
    )
    bio = models.TextField(_("o mnie"), blank=True)
    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="specialists",
        verbose_name=_("miasto"),
    )
    works_online = models.BooleanField(_("pracuję online"), default=False)
    specializations = models.ManyToManyField(
        Specialization, blank=True, related_name="specialists", verbose_name=_("specjalizacje")
    )
    approaches = models.ManyToManyField(
        TherapyApproach, blank=True, related_name="specialists", verbose_name=_("nurty")
    )
    languages = models.CharField(
        _("języki"), max_length=200, blank=True, help_text=_("Np. polski, angielski.")
    )
    license_number = models.CharField(
        _("numer prawa wykonywania zawodu / certyfikatu"), max_length=64, blank=True
    )
    contact_email = models.EmailField(_("publiczny e-mail"), blank=True)
    contact_phone = models.CharField(_("publiczny telefon"), max_length=32, blank=True)
    website = models.URLField(_("strona www"), blank=True)
    open_to_work = models.BooleanField(
        _("szukam pracy / współpracy"), default=False, help_text=_("Wyróżnia profil dla klinik.")
    )
    is_public = models.BooleanField(_("profil widoczny publicznie"), default=True)
    is_blocked = models.BooleanField(_("zablokowany przez moderację"), default=False)
    # Reserved for Phase 3 (patient-facing directory). Not used by any view yet.
    visible_to_patients = models.BooleanField(_("widoczny dla pacjentów"), default=False)

    objects = SpecialistProfileQuerySet.as_manager()

    class Meta:
        verbose_name = _("profil specjalisty")
        verbose_name_plural = _("profile specjalistów")
        ordering = ("-updated_at",)

    def __str__(self) -> str:
        return self.display_name

    @property
    def display_name(self) -> str:
        name = self.user.get_full_name() or self.user.email.split("@")[0]
        return f"{self.academic_title} {name}".strip()

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.slug:
            self.slug = unique_slug(
                self.user.get_full_name() or "specjalista",
                lambda s: SpecialistProfile.objects.filter(slug=s).exclude(pk=self.pk).exists(),
                max_length=100,
            )
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("profiles:detail", kwargs={"slug": self.slug})
