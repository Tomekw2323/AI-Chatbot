from django import forms
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from .models import User


class SignupForm(forms.Form):
    """Extra fields for allauth's signup form (``ACCOUNT_SIGNUP_FORM_CLASS``)."""

    first_name = forms.CharField(label=_("Imię"), max_length=150)
    last_name = forms.CharField(label=_("Nazwisko"), max_length=150)

    def signup(self, request: HttpRequest, user: User) -> None:
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save(update_fields=["first_name", "last_name"])


class UserNameForm(forms.ModelForm[User]):
    class Meta:
        model = User
        fields = ("first_name", "last_name")
        labels = {"first_name": _("Imię"), "last_name": _("Nazwisko")}
