from django.urls import path

from .auth_views import CurrentUserView, RegisterView
from .views import ContactDetailView, ContactListCreateView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/me/", CurrentUserView.as_view(), name="current-user"),
    path("contacts/", ContactListCreateView.as_view(), name="contact-list"),
    path("contacts/<int:pk>/", ContactDetailView.as_view(), name="contact-detail"),
]
