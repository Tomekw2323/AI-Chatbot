from decimal import Decimal

import pytest
from django.urls import reverse

from apps.core.tests.factories import CityFactory, SpecializationFactory, VoivodeshipFactory
from apps.listings.filters import ListingFilter
from apps.listings.models import Listing

from .factories import ListingFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def cities():
    dolnoslaskie = VoivodeshipFactory.create(slug="dolnoslaskie", name="dolnośląskie")
    return {
        "wroclaw": CityFactory.create(slug="wroclaw", name="Wrocław", voivodeship=dolnoslaskie),
        "legnica": CityFactory.create(slug="legnica", name="Legnica", voivodeship=dolnoslaskie),
        "krakow": CityFactory.create(slug="krakow", name="Kraków"),
    }


def run(data: dict[str, str]) -> list[Listing]:
    return list(ListingFilter(data, queryset=Listing.objects.public()).qs)


def test_filter_by_city(cities) -> None:
    wroclaw = ListingFactory.create(published=True, city=cities["wroclaw"])
    ListingFactory.create(published=True, city=cities["krakow"])
    assert run({"city": "wroclaw"}) == [wroclaw]


def test_filter_by_voivodeship(cities) -> None:
    a = ListingFactory.create(published=True, city=cities["wroclaw"])
    b = ListingFactory.create(published=True, city=cities["legnica"])
    ListingFactory.create(published=True, city=cities["krakow"])
    assert set(run({"voivodeship": "dolnoslaskie"})) == {a, b}


def test_filter_by_kind() -> None:
    room = ListingFactory.create(published=True, room=True)
    ListingFactory.create(published=True)
    assert run({"kind": Listing.Kind.ROOM_RENTAL}) == [room]


def test_filter_by_category() -> None:
    cbt = SpecializationFactory.create(slug="cbt")
    match = ListingFactory.create(published=True)
    match.specializations.add(cbt)
    ListingFactory.create(published=True)
    assert run({"specialization": "cbt"}) == [match]


def test_combined_filters_and_text_search(cities) -> None:
    match = ListingFactory.create(
        published=True, room=True, city=cities["wroclaw"], title="Gabinet z klimatyzacją"
    )
    ListingFactory.create(published=True, room=True, city=cities["wroclaw"], title="Inny gabinet")
    ListingFactory.create(published=True, city=cities["wroclaw"], title="Praca z klimatyzacją")
    assert run({"kind": "room_rental", "city": "wroclaw", "q": "klimatyzac"}) == [match]


def test_order_by_price() -> None:
    cheap = ListingFactory.create(published=True, room=True, price_amount=Decimal("30"))
    pricey = ListingFactory.create(published=True, room=True, price_amount=Decimal("90"))
    assert run({"ordering": "price"}) == [cheap, pricey]
    assert run({"ordering": "-price"}) == [pricey, cheap]


def test_unknown_city_slug_is_invalid_not_error() -> None:
    ListingFactory.create(published=True)
    assert not ListingFilter({"city": "atlantyda"}, queryset=Listing.objects.public()).is_valid()


class TestSeoUrls:
    def test_kind_url(self, client) -> None:
        room = ListingFactory.create(published=True, room=True, title="Gabinet A")
        ListingFactory.create(published=True, title="Praca B")
        response = client.get(reverse("listings:list_by_kind", kwargs={"kind_slug": "gabinety"}))
        assert response.status_code == 200
        assert list(response.context["page_obj"]) == [room]

    def test_kind_city_url(self, client, cities) -> None:
        match = ListingFactory.create(published=True, city=cities["wroclaw"])
        ListingFactory.create(published=True, city=cities["krakow"])
        url = reverse(
            "listings:list_by_kind_city", kwargs={"kind_slug": "praca", "city_slug": "wroclaw"}
        )
        response = client.get(url)
        assert list(response.context["page_obj"]) == [match]
        assert "Wrocław" in response.content.decode()

    def test_unknown_kind_or_city_is_404(self, client) -> None:
        assert client.get("/ogloszenia/nieistniejacy-typ/").status_code == 404
        assert client.get("/ogloszenia/praca/atlantyda/").status_code == 404

    def test_htmx_request_returns_partial(self, client) -> None:
        ListingFactory.create(published=True)
        response = client.get(reverse("listings:list"), HTTP_HX_REQUEST="true")
        assert response.status_code == 200
        assert b"<html" not in response.content
        assert b'id="results"' in response.content
