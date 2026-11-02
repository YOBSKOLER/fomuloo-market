from rest_framework.permissions import BasePermission


CONTACT_MANAGER_GROUP = "contact_managers"


def is_contact_manager(user):
    return bool(
        user.is_authenticated
        and (
            user.is_staff
            or user.groups.filter(name=CONTACT_MANAGER_GROUP).exists()
        )
    )


class IsContactOwnerOrManager(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return is_contact_manager(request.user) or obj.owner_id == request.user.pk
