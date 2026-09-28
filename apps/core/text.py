"""Text helpers that are aware of Polish characters."""

from collections.abc import Callable

from django.utils.text import slugify

# NFKD normalisation (used by ``slugify``) does not decompose "ł", so without
# this mapping "Wrocław" would become "wrocaw".
_POLISH_TRANSLATION = str.maketrans({"ł": "l", "Ł": "L"})


def slugify_pl(value: str) -> str:
    return slugify(value.translate(_POLISH_TRANSLATION))


def unique_slug(value: str, exists: Callable[[str], bool], max_length: int = 80) -> str:
    """Return a slug for ``value`` that ``exists`` reports as free.

    ``exists`` is a callback so callers can scope uniqueness (e.g. exclude the
    instance being edited) without this helper knowing about models.
    """
    base = slugify_pl(value)[:max_length].strip("-") or "item"
    candidate = base
    counter = 2
    while exists(candidate):
        suffix = f"-{counter}"
        candidate = f"{base[: max_length - len(suffix)]}{suffix}"
        counter += 1
    return candidate
