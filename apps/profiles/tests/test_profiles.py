import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.core.tests.factories import CityFactory, SpecializationFactory
from apps.profiles.filters import SpecialistProfileFilter
from apps.profiles.models import SpecialistProfile

from .factories import SpecialistProfileFactory

pytestmark = pytest.mark.django_db


def test_slug_and_display_name_from_user() -> None:
    user = UserFactory.create(first_name="Anna", last_name="Łęcka")
    profile = SpecialistProfileFactory.create(user=user, academic_title="dr")
    assert profile.slug == "anna-lecka"
    assert profile.display_name == "dr Anna Łęcka"


def test_new_profiles_are_not_exposed_to_patients() -> None:
    assert SpecialistProfileFactory.create().visible_to_patients is False


def test_public_queryset_excludes_hidden_blocked_and_inactive_users() -> None:
    visible = SpecialistProfileFactory.create()
    SpecialistProfileFactory.create(is_public=False)
    SpecialistProfileFactory.create(is_blocked=True)
    SpecialistProfileFactory.create(user=UserFactory.create(is_active=False))
    assert list(SpecialistProfile.objects.public()) == [visible]


def test_filter_by_city_specialization_and_open_to_work() -> None:
    wroclaw = CityFactory.create(slug="wroclaw", name="Wrocław")
    cbt = SpecializationFactory.create(slug="cbt")
    match = SpecialistProfileFactory.create(city=wroclaw, open_to_work=True)
    match.specializations.add(cbt)
    SpecialistProfileFactory.create(city=wroclaw)
    SpecialistProfileFactory.create(open_to_work=True)

    qs = SpecialistProfileFilter(
        {"city": "wroclaw", "specialization": "cbt", "open_to_work": "true"},
        queryset=SpecialistProfile.objects.all(),
    ).qs
    assert list(qs) == [match]


def test_edit_own_profile_creates_profile(client) -> None:
    user = UserFactory.create()
    city = CityFactory.create()
    client.force_login(user)
    response = client.post(
        reverse("profiles:edit"),
        {
            "first_name": "Ewa",
            "last_name": "Nowak",
            "profession": "psychotherapist",
            "headline": "Psychoterapeutka",
            "city": city.pk,
            "is_public": "on",
        },
    )
    assert response.status_code == 302
    profile = SpecialistProfile.objects.get(user=user)
    assert profile.slug == "ewa-nowak"


def test_edit_requires_login(client) -> None:
    response = client.get(reverse("profiles:edit"))
    assert response.status_code == 302
    assert reverse("account_login") in response["Location"]


def test_hidden_profile_detail_is_404(client) -> None:
    profile = SpecialistProfileFactory.create(is_public=False)
    assert client.get(profile.get_absolute_url()).status_code == 404


def test_list_and_htmx_partial(client) -> None:
    SpecialistProfileFactory.create(headline="Terapia par")
    full = client.get(reverse("profiles:list"))
    partial = client.get(reverse("profiles:list"), HTTP_HX_REQUEST="true")
    assert b"Terapia par" in full.content
    assert b"<html" in full.content
    assert b"<html" not in partial.content


def test_detail_shows_edit_link_only_to_owner(client) -> None:
    profile = SpecialistProfileFactory.create()
    edit_url = reverse("profiles:edit")
    assert edit_url not in client.get(profile.get_absolute_url()).content.decode()
    client.force_login(profile.user)
    assert edit_url in client.get(profile.get_absolute_url()).content.decode()


def test_invalid_profile_form_is_redisplayed(client) -> None:
    user = UserFactory.create()
    client.force_login(user)
    response = client.post(
        reverse("profiles:edit"), {"first_name": "Ewa", "website": "javascript:alert(1)"}
    )
    assert response.status_code == 200
    assert "website" in response.context["form"].errors
    assert not SpecialistProfile.objects.filter(user=user).exists()


def test_unverified_user_cannot_create_profile(client) -> None:
    user = UserFactory.create(verified=False)
    client.force_login(user)
    client.post(
        reverse("profiles:edit"),
        {"first_name": "A", "last_name": "B", "profession": "psychologist", "headline": "x"},
    )
    assert not SpecialistProfile.objects.filter(user=user).exists()


def test_bio_is_escaped(client) -> None:
    profile = SpecialistProfileFactory.create(bio="<script>alert(1)</script>")
    content = client.get(profile.get_absolute_url()).content.decode()
    assert "<script>alert(1)" not in content
    assert "&lt;script&gt;" in content


def test_text_search() -> None:
    match = SpecialistProfileFactory.create(headline="Terapia uzależnień")
    SpecialistProfileFactory.create(headline="Psychologia dziecięca")
    qs = SpecialistProfileFilter({"q": "uzależ"}, queryset=SpecialistProfile.objects.all()).qs
    assert list(qs) == [match]


def test_edit_page_is_prefilled_for_existing_profile(client) -> None:
    profile = SpecialistProfileFactory.create(headline="Mój nagłówek")
    client.force_login(profile.user)
    response = client.get(reverse("profiles:edit"))
    assert response.status_code == 200
    assert response.context["form"].instance == profile
    assert "Mój nagłówek" in response.content.decode()
