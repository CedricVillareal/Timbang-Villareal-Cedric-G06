from django.urls import path

from . import views

app_name = "transactions"

urlpatterns = [
    path("sellers/", views.seller_list, name="seller_list"),
    path("sellers/new/", views.seller_create, name="seller_create"),
    path("transactions/", views.transaction_list, name="list"),
    path("transactions/new/", views.transaction_create, name="create"),
    path("transactions/<int:pk>/", views.transaction_detail, name="detail"),
    path("transactions/<int:pk>/void/", views.transaction_void, name="void"),
]