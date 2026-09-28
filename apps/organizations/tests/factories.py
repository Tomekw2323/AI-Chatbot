import factory

from apps.accounts.tests.factories import UserFactory
from apps.core.tests.factories import CityFactory
from apps.organizations.models import Membership, Organization


class OrganizationFactory(factory.django.DjangoModelFactory[Organization]):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Poradnia {n}")
    city = factory.SubFactory(CityFactory)


class MembershipFactory(factory.django.DjangoModelFactory[Membership]):
    class Meta:
        model = Membership

    organization = factory.SubFactory(OrganizationFactory)
    user = factory.SubFactory(UserFactory)
    role = Membership.Role.OWNER
