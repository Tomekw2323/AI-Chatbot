from django import forms

from .models import Organization


class OrganizationForm(forms.ModelForm[Organization]):
    class Meta:
        model = Organization
        fields = (
            "name",
            "kind",
            "city",
            "address",
            "description",
            "website",
            "contact_email",
            "contact_phone",
            "tax_id",
            "is_public",
        )
        widgets = {"description": forms.Textarea(attrs={"rows": 6})}
