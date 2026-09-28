from typing import Any

from django import forms
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import User


class SignupForm(forms.Form):
    """Extra fields for allauth's signup form (``ACCOUNT_SIGNUP_FORM_CLASS``)."""

    first_name = forms.CharField(label=_("Imię"), max_length=150)
    last_name = forms.CharField(label=_("Nazwisko"), max_length=150)
    accept_terms = forms.BooleanField(required=True)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Built here, not at import time: reversing URLs while settings load is circular.
        self.fields["accept_terms"].label = format_html(
            '{} <a href="{}" target="_blank" class="link">{}</a> {} '
            '<a href="{}" target="_blank" class="link">{}</a>.',
            _("Akceptuję"),
            reverse("privacy:terms"),
            _("regulamin"),
            _("i zapoznałem(-am) się z"),
            reverse("privacy:policy"),
            _("polityką prywatności"),
        )

    def signup(self, request: HttpRequest, user: User) -> None:
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.terms_accepted_at = timezone.now()
        user.save(update_fields=["first_name", "last_name", "terms_accepted_at"])


class UserNameForm(forms.ModelForm[User]):
    class Meta:
        model = User
        fields = ("first_name", "last_name")
        labels = {"first_name": _("Imię"), "last_name": _("Nazwisko")}
