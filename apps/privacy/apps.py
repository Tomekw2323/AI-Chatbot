from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PrivacyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.privacy"
    label = "privacy"
    verbose_name = _("Prywatność (RODO)")
