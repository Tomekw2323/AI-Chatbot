from django.urls import path

from . import views

app_name = "listings"

urlpatterns = [
    path("", views.listing_list, name="list"),
    path("dodaj/", views.listing_create, name="create"),
    path("<int:pk>/edytuj/", views.listing_update, name="update"),
    path("<int:pk>/<str:action>/zmien-status/", views.listing_transition, name="transition"),
    path("<int:pk>/usun/", views.listing_delete, name="delete"),
    path("<int:pk>/wiadomosc/", views.inquiry_create, name="inquiry"),
    path("<int:pk>/zglos/", views.listing_report, name="report"),
    path("<int:pk>/<slug:slug>/", views.listing_detail, name="detail"),
    path("<slug:kind_slug>/", views.listing_list, name="list_by_kind"),
    path("<slug:kind_slug>/<slug:city_slug>/", views.listing_list, name="list_by_kind_city"),
]
