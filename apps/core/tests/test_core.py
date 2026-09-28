import pytest
from django.core.management import call_command

from apps.core.models import City, Specialization, TherapyApproach, Voivodeship
from apps.core.text import slugify_pl, unique_slug


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Wrocław", "wroclaw"),
        ("Łódź", "lodz"),
        ("Zielona Góra", "zielona-gora"),
        ("Gorzów Wielkopolski", "gorzow-wielkopolski"),
        ("Psychoterapia – dzieci i młodzież", "psychoterapia-dzieci-i-mlodziez"),
    ],
)
def test_slugify_pl_handles_polish_characters(value: str, expected: str) -> None:
    assert slugify_pl(value) == expected


def test_unique_slug_appends_counter() -> None:
    taken = {"anna-kowalska", "anna-kowalska-2"}
    assert unique_slug("Anna Kowalska", taken.__contains__) == "anna-kowalska-3"


def test_unique_slug_falls_back_for_empty_input() -> None:
    assert unique_slug("!!!", lambda s: False) == "item"


@pytest.mark.django_db
def test_reference_fixture_loads() -> None:
    call_command("loaddata", "reference_data", verbosity=0)
    assert Voivodeship.objects.count() == 16
    assert City.objects.get(slug="wroclaw").voivodeship.slug == "dolnoslaskie"
    assert City.objects.filter(is_featured=True).exists()
    assert Specialization.objects.filter(is_active=True).count() > 10
    assert TherapyApproach.objects.filter(slug="poznawczo-behawioralny-cbt").exists()
