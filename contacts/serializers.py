from rest_framework import serializers

from .models import Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "company",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_email(self, value):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return value

        duplicate = Contact.objects.filter(owner=request.user, email__iexact=value)
        if self.instance is not None:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError(
                "Vous possédez déjà un contact avec cette adresse e-mail."
            )
        return value
