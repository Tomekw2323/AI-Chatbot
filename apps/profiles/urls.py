from django.urls import path

from . import views

app_name = "profiles"

urlpatterns = [
    path("", views.specialist_list, name="list"),
    path("moj-profil/", views.edit_own_profile, name="edit"),
    path("<slug:slug>/", views.SpecialistDetailView.as_view(), name="detail"),
]
