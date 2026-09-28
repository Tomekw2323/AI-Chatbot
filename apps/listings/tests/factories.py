from datetime import timedelta
from decimal import Decimal

import factory
from django.utils import timezone

from apps.accounts.tests.factories import UserFactory
from apps.core.tests.factories import CityFactory
from apps.listings.models import Listing


class ListingFactory(factory.django.DjangoModelFactory[Listing]):
    """A draft job offer by default; use the traits for other states/kinds."""

    class Meta:
        model = Listing

    kind = Listing.Kind.JOB
    title = factory.Sequence(lambda n: f"Psycholog – oferta {n}")
    description = "Opis oferty."
    author = factory.SubFactory(UserFactory)
    city = factory.SubFactory(CityFactory)

    class Params:
        published = factory.Trait(
            status=Listing.Status.PUBLISHED,
            published_at=factory.LazyFunction(timezone.now),
            expires_at=factory.LazyFunction(lambda: timezone.now() + timedelta(days=30)),
        )
        room = factory.Trait(
            kind=Listing.Kind.ROOM_RENTAL,
            price_amount=Decimal("50.00"),
            price_unit=Listing.PriceUnit.HOUR,
        )
