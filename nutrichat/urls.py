from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("customers/", views.CustomersView.as_view(), name="customers"),
    path("customers/new/", views.CustomerCreateView.as_view(), name="customer-create"),
    path("customers/<int:pk>/", views.CustomerEditView.as_view(), name="customer-edit"),
    path("customers/<int:pk>/remove/", views.CustomerRemoveView.as_view(), name="customer-remove"),
]
