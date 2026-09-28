"""A single account type for everyone.

Whether a user acts as a specialist or on behalf of a clinic is expressed by
related objects (``profiles.SpecialistProfile``, ``organizations.Membership``),
not by a role flag on the user, so one person can be both (ADR 0007).
"""

from typing import Any, ClassVar

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class EmailUserManager(UserManager["User"]):
    use_in_migrations = True

    def _create_user_with_email(
        self, email: str, password: str | None, **extra_fields: Any
    ) -> "User":
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(  # type: ignore[override]
        self, email: str, password: str | None = None, **extra_fields: Any
    ) -> "User":
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user_with_email(email, password, **extra_fields)

    def create_superuser(  # type: ignore[override]
        self, email: str, password: str | None = None, **extra_fields: Any
    ) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user_with_email(email, password, **extra_fields)


class User(AbstractUser):
    username = None  # type: ignore[assignment]
    email = models.EmailField(_("adres e-mail"), unique=True)
    terms_accepted_at = models.DateTimeField(
        _("akceptacja regulaminu i polityki prywatności"), null=True, blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    objects: ClassVar[EmailUserManager] = EmailUserManager()

    class Meta:
        verbose_name = _("użytkownik")
        verbose_name_plural = _("użytkownicy")
        ordering = ("email",)

    def __str__(self) -> str:
        return self.get_full_name() or self.email
