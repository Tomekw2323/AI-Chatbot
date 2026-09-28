import factory

from apps.accounts.tests.factories import UserFactory
from apps.core.tests.factories import CityFactory
from apps.profiles.models import SpecialistProfile


class SpecialistProfileFactory(factory.django.DjangoModelFactory[SpecialistProfile]):
    class Meta:
        model = SpecialistProfile

    user = factory.SubFactory(UserFactory)
    profession = SpecialistProfile.Profession.PSYCHOLOGIST
    headline = "Psycholog kliniczny"
    city = factory.SubFactory(CityFactory)
