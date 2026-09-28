import django_filters
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _

from apps.core.models import City, Specialization, TherapyApproach

from .models import SpecialistProfile


class SpecialistProfileFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="filter_q", label=_("Szukaj"))
    city = django_filters.ModelChoiceFilter(
        queryset=City.objects.all(),
        to_field_name="slug",
        label=_("Miasto"),
        empty_label=_("Cała Polska"),
    )
    profession = django_filters.ChoiceFilter(
        choices=SpecialistProfile.Profession.choices, label=_("Zawód")
    )
    specialization = django_filters.ModelChoiceFilter(
        field_name="specializations",
        queryset=Specialization.objects.filter(is_active=True),
        to_field_name="slug",
        label=_("Specjalizacja"),
    )
    approach = django_filters.ModelChoiceFilter(
        field_name="approaches",
        queryset=TherapyApproach.objects.filter(is_active=True),
        to_field_name="slug",
        label=_("Nurt"),
    )
    open_to_work = django_filters.BooleanFilter(
        widget=django_filters.widgets.BooleanWidget(), label=_("Szuka pracy")
    )

    class Meta:
        model = SpecialistProfile
        fields = ("q", "city", "profession", "specialization", "approach", "open_to_work")

    def filter_q(
        self, queryset: QuerySet[SpecialistProfile], name: str, value: str
    ) -> QuerySet[SpecialistProfile]:
        return queryset.filter(
            Q(headline__icontains=value)
            | Q(bio__icontains=value)
            | Q(user__first_name__icontains=value)
            | Q(user__last_name__icontains=value)
        )
