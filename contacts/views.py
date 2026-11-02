from rest_framework import generics

from .models import Contact
from .permissions import IsContactOwnerOrManager, is_contact_manager
from .serializers import ContactSerializer


class ContactListCreateView(generics.ListCreateAPIView):
    serializer_class = ContactSerializer
    permission_classes = (IsContactOwnerOrManager,)

    def get_queryset(self):
        if is_contact_manager(self.request.user):
            return Contact.objects.all()
        return Contact.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ContactSerializer
    permission_classes = (IsContactOwnerOrManager,)

    def get_queryset(self):
        if is_contact_manager(self.request.user):
            return Contact.objects.all()
        return Contact.objects.filter(owner=self.request.user)
