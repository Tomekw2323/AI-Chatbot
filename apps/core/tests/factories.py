import factory

from apps.core.models import City, Specialization, TherapyApproach, Voivodeship


class VoivodeshipFactory(factory.django.DjangoModelFactory[Voivodeship]):
    class Meta:
        model = Voivodeship
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Województwo {n}")
    slug = factory.Sequence(lambda n: f"wojewodztwo-{n}")


class CityFactory(factory.django.DjangoModelFactory[City]):
    class Meta:
        model = City
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Miasto {n}")
    slug = factory.Sequence(lambda n: f"miasto-{n}")
    voivodeship = factory.SubFactory(VoivodeshipFactory)


class SpecializationFactory(factory.django.DjangoModelFactory[Specialization]):
    class Meta:
        model = Specialization
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Specjalizacja {n}")
    slug = factory.Sequence(lambda n: f"specjalizacja-{n}")


class TherapyApproachFactory(factory.django.DjangoModelFactory[TherapyApproach]):
    class Meta:
        model = TherapyApproach
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Nurt {n}")
    slug = factory.Sequence(lambda n: f"nurt-{n}")
