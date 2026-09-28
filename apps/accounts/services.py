from allauth.account.models import EmailAddress
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest

from .models import User


def require_user(request: HttpRequest) -> User:
    """Return the signed-in ``User`` (narrowed for type checkers) or deny access.

    Use in views already protected by ``login_required``.
    """
    user = request.user
    if not isinstance(user, User):
        raise PermissionDenied
    return user


def has_verified_email(user: AbstractBaseUser | AnonymousUser) -> bool:
    """Publishing content and contacting others require a verified address (ADR 0012)."""
    if not user.is_authenticated:
        return False
    return bool(EmailAddress.objects.filter(user_id=user.pk, verified=True).exists())
