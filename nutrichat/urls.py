from django.urls import path
from . import chat_views, views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("customers/", views.CustomersView.as_view(), name="customers"),
    path("customers/new/", views.CustomerCreateView.as_view(), name="customer-create"),
    path("customers/<int:pk>/", views.CustomerEditView.as_view(), name="customer-edit"),
    path("customers/<int:pk>/remove/", views.CustomerRemoveView.as_view(), name="customer-remove"),
    path("chat/", chat_views.ChatView.as_view(), name="chat"),
    path("chat/<int:conv_id>/", chat_views.ChatView.as_view(), name="chat-conversation"),
    path("chat/send/", chat_views.ChatSendView.as_view(), name="chat-send"),
    path("chat/<int:conv_id>/send/", chat_views.ChatSendView.as_view(), name="chat-send-existing"),
    path("chat/<int:conv_id>/stream/", chat_views.ChatStreamView.as_view(), name="chat-stream"),
]
