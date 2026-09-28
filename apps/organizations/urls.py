from django.urls import path

from . import views

app_name = "organizations"

urlpatterns = [
    path("dodaj/", views.OrganizationCreateView.as_view(), name="create"),
    path("<slug:slug>/", views.OrganizationDetailView.as_view(), name="detail"),
    path("<slug:slug>/edytuj/", views.OrganizationUpdateView.as_view(), name="update"),
]
