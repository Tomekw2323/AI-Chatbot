import django_filters
from django import forms
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _

from apps.core.models import City, Specialization, Voivodeship

from .models import Listing


class ListingFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method="filter_q",
        label=_("Szukaj"),
        widget=forms.TextInput(attrs={"placeholder": _("Np. psycholog dziecięcy, gabinet")}),
    )
    kind = django_filters.ChoiceFilter(
        choices=Listing.Kind.choices, label=_("Rodzaj"), empty_label=_("Wszystkie rodzaje")
    )
    city = django_filters.ModelChoiceFilter(
        queryset=City.objects.all(),
        to_field_name="slug",
        label=_("Miasto"),
        empty_label=_("Cała Polska"),
    )
    voivodeship = django_filters.ModelChoiceFilter(
        field_name="city__voivodeship",
        queryset=Voivodeship.objects.all(),
        to_field_name="slug",
        label=_("Województwo"),
        empty_label=_("Wszystkie"),
    )
    specialization = django_filters.ModelChoiceFilter(
        field_name="specializations",
        queryset=Specialization.objects.filter(is_active=True),
        to_field_name="slug",
        label=_("Kategoria"),
        empty_label=_("Wszystkie"),
    )
    work_mode = django_filters.ChoiceFilter(choices=Listing.WorkMode.choices, label=_("Tryb pracy"))
    ordering = django_filters.OrderingFilter(
        fields=(("published_at", "published_at"), ("price_amount", "price")),
        field_labels={
            "-published_at": _("Najnowsze"),
            "price": _("Cena rosnąco"),
            "-price": _("Cena malejąco"),
        },
        label=_("Sortowanie"),
    )

    class Meta:
        model = Listing
        fields = ("q", "kind", "city", "voivodeship", "specialization", "work_mode")

    def filter_q(self, queryset: QuerySet[Listing], name: str, value: str) -> QuerySet[Listing]:
        return queryset.filter(Q(title__icontains=value) | Q(description__icontains=value))
