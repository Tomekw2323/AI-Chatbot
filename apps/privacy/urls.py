from django.urls import path

from . import views

app_name = "privacy"

urlpatterns = [
    path("moje-dane/", views.my_data, name="my_data"),
    path("moje-dane/eksport/", views.export_data, name="export"),
    path("moje-dane/usun-konto/", views.delete_account_view, name="delete_account"),
    path("regulamin/", views.terms, name="terms"),
    path("polityka-prywatnosci/", views.privacy_policy, name="policy"),
]
