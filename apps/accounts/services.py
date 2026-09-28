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
