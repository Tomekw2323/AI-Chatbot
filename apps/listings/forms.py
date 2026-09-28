from typing import Any

from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from apps.core.models import Specialization
from apps.organizations.services import AnyUser, managed_organizations

from .models import Inquiry, Listing, RoomAvailabilityBlock

OFFER_FIELDS = ("employment_type", "work_mode", "salary_min", "salary_max", "salary_period")
ROOM_FIELDS = (
    "price_amount",
    "price_unit",
    "room_area_m2",
    "amenities",
    "availability_description",
)
# Which kind-specific fields the form shows/keeps for each kind.
FIELDS_BY_KIND: dict[str, tuple[str, ...]] = {
    Listing.Kind.JOB: OFFER_FIELDS,
    Listing.Kind.INTERNSHIP: OFFER_FIELDS,
    Listing.Kind.VOLUNTEERING: ("work_mode",),
    Listing.Kind.JOB_SEEKING: ("employment_type", "work_mode"),
    Listing.Kind.ROOM_RENTAL: ROOM_FIELDS,
}
KIND_SPECIFIC_FIELDS = tuple(dict.fromkeys(OFFER_FIELDS + ROOM_FIELDS))


class ListingForm(forms.ModelForm[Listing]):
    specializations = forms.ModelMultipleChoiceField(
        queryset=Specialization.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=_("Kategorie"),
    )

    class Meta:
        model = Listing
        fields = (
            "kind",
            "organization",
            "title",
            "description",
            "city",
            "address",
            "specializations",
            "contact_email",
            *KIND_SPECIFIC_FIELDS,
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 10}),
            "availability_description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args: Any, user: AnyUser, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        organization_field = self.fields["organization"]
        if isinstance(organization_field, forms.ModelChoiceField):
            organization_field.queryset = managed_organizations(user)
        self.fields["kind"].widget.attrs["data-listing-kind"] = ""

    @staticmethod
    def fields_for_kind(kind: str) -> tuple[str, ...]:
        return FIELDS_BY_KIND.get(kind, ())

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean() or {}
        kind = cleaned.get("kind", "")
        if kind == Listing.Kind.JOB_SEEKING:
            cleaned["organization"] = None
        kept = self.fields_for_kind(kind)
        for name in KIND_SPECIFIC_FIELDS:
            if name not in kept:
                cleaned[name] = None if Listing._meta.get_field(name).null else ""
        return cleaned


AvailabilityFormSet = inlineformset_factory(
    Listing,
    RoomAvailabilityBlock,
    fields=("weekday", "start_time", "end_time"),
    widgets={
        "start_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        "end_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
    },
    extra=2,
    max_num=21,
    can_delete=True,
)


class InquiryForm(forms.ModelForm[Inquiry]):
    class Meta:
        model = Inquiry
        fields = ("message",)
        widgets = {
            "message": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": _("Przedstaw się i napisz, czego dotyczy wiadomość."),
                }
            )
        }
        labels = {"message": _("Twoja wiadomość")}
