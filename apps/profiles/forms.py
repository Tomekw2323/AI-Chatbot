from django import forms

from apps.core.models import Specialization, TherapyApproach

from .models import SpecialistProfile


class SpecialistProfileForm(forms.ModelForm[SpecialistProfile]):
    specializations = forms.ModelMultipleChoiceField(
        queryset=Specialization.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=SpecialistProfile._meta.get_field("specializations").verbose_name,
    )
    approaches = forms.ModelMultipleChoiceField(
        queryset=TherapyApproach.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=SpecialistProfile._meta.get_field("approaches").verbose_name,
    )

    class Meta:
        model = SpecialistProfile
        fields = (
            "academic_title",
            "profession",
            "headline",
            "bio",
            "city",
            "works_online",
            "specializations",
            "approaches",
            "languages",
            "license_number",
            "contact_email",
            "contact_phone",
            "website",
            "open_to_work",
            "is_public",
        )
        widgets = {"bio": forms.Textarea(attrs={"rows": 8})}
