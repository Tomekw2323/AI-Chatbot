"""Shared base classes and reference data (locations, specializations, approaches).

Reference data is loaded from ``fixtures/reference_data.json`` and edited by
staff in the Django admin. Other apps only reference it via foreign keys.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(_("utworzono"), auto_now_add=True)
    updated_at = models.DateTimeField(_("zaktualizowano"), auto_now=True)

    class Meta:
        abstract = True


class ReferenceModel(models.Model):
    """Named, slugged dictionary entry that can be retired without deletion."""

    name = models.CharField(_("nazwa"), max_length=120, unique=True)
    slug = models.SlugField(_("slug"), max_length=120, unique=True)
    is_active = models.BooleanField(_("aktywny"), default=True)
    sort_order = models.PositiveSmallIntegerField(_("kolejność"), default=0)

    class Meta:
        abstract = True
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name


class Voivodeship(models.Model):
    name = models.CharField(_("nazwa"), max_length=60, unique=True)
    slug = models.SlugField(_("slug"), max_length=60, unique=True)

    class Meta:
        verbose_name = _("województwo")
        verbose_name_plural = _("województwa")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class City(models.Model):
    name = models.CharField(_("nazwa"), max_length=80)
    slug = models.SlugField(_("slug"), max_length=80, unique=True)
    voivodeship = models.ForeignKey(
        Voivodeship,
        on_delete=models.PROTECT,
        related_name="cities",
        verbose_name=_("województwo"),
    )
    is_featured = models.BooleanField(
        _("wyróżnione"), default=False, help_text=_("Pokazywane na stronie głównej.")
    )

    class Meta:
        verbose_name = _("miasto")
        verbose_name_plural = _("miasta")
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=("name", "voivodeship"), name="uniq_city_per_voivodeship"
            ),
        ]

    def __str__(self) -> str:
        return self.name


class Specialization(ReferenceModel):
    """Area of practice, e.g. child psychology, addiction therapy."""

    class Meta(ReferenceModel.Meta):
        verbose_name = _("specjalizacja")
        verbose_name_plural = _("specjalizacje")


class TherapyApproach(ReferenceModel):
    """Psychotherapy modality, e.g. CBT, psychodynamic, systemic."""

    class Meta(ReferenceModel.Meta):
        verbose_name = _("nurt terapeutyczny")
        verbose_name_plural = _("nurty terapeutyczne")


class RateLimitCounter(models.Model):
    """One fixed window of a rate limit (see ``core.ratelimit``)."""

    key = models.CharField(max_length=200)
    window_start = models.DateTimeField()
    period_seconds = models.PositiveIntegerField()
    count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("licznik limitu zapytań")
        verbose_name_plural = _("liczniki limitów zapytań")
        constraints = [
            models.UniqueConstraint(
                fields=("key", "window_start", "period_seconds"), name="uniq_rate_limit_window"
            ),
        ]
        indexes = [models.Index(fields=("window_start",))]

    def __str__(self) -> str:
        return f"{self.key} @ {self.window_start:%Y-%m-%d %H:%M} = {self.count}"
