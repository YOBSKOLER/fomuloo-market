import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from .models import Contact


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def member():
    return get_user_model().objects.create_user(
        username="alice",
        email="alice@example.com",
        password="Strong-pass-123",
    )


@pytest.fixture
def other_member():
    return get_user_model().objects.create_user(
        username="bob",
        email="bob@example.com",
        password="Strong-pass-123",
    )


@pytest.fixture
def authenticated_client(api_client, member):
    api_client.force_authenticate(user=member)
    return api_client


@pytest.fixture
def contact(member):
    return Contact.objects.create(
        owner=member,
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
    )


@pytest.fixture
def manager():
    user = get_user_model().objects.create_user(
        username="manager",
        email="manager@example.com",
        password="Strong-pass-123",
    )
    group, _ = Group.objects.get_or_create(name="contact_managers")
    user.groups.add(group)
    return user


@pytest.mark.django_db
def test_anonymous_user_cannot_list_contacts(api_client):
    response = api_client.get(reverse("contact-list"))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["error"]["code"] == "not_authenticated"


@pytest.mark.django_db
def test_anonymous_user_cannot_create_contact(api_client):
    response = api_client.post(
        reverse("contact-list"),
        {"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert Contact.objects.count() == 0


@pytest.mark.django_db
def test_member_can_create_contact_and_is_assigned_as_owner(authenticated_client, member):
    response = authenticated_client.post(
        reverse("contact-list"),
        {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "owner": 9999,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    created = Contact.objects.get()
    assert created.owner == member
    assert "owner" not in response.data


@pytest.mark.django_db
def test_member_lists_only_their_own_contacts(authenticated_client, member, other_member):
    Contact.objects.create(
        owner=member, first_name="Ada", last_name="Lovelace", email="ada@example.com"
    )
    Contact.objects.create(
        owner=other_member, first_name="Grace", last_name="Hopper", email="grace@example.com"
    )

    response = authenticated_client.get(reverse("contact-list"))

    assert response.status_code == status.HTTP_200_OK
    assert [item["email"] for item in response.data] == ["ada@example.com"]


@pytest.mark.django_db
def test_member_can_retrieve_their_contact(authenticated_client, contact):
    response = authenticated_client.get(reverse("contact-detail", args=[contact.pk]))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == contact.pk
    assert response.data["first_name"] == "Ada"


@pytest.mark.django_db
def test_member_can_partially_update_their_contact(authenticated_client, contact):
    response = authenticated_client.patch(
        reverse("contact-detail", args=[contact.pk]),
        {"company": "Analytical Engines"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    contact.refresh_from_db()
    assert contact.company == "Analytical Engines"


@pytest.mark.django_db
def test_member_can_fully_update_their_contact(authenticated_client, contact):
    response = authenticated_client.put(
        reverse("contact-detail", args=[contact.pk]),
        {
            "first_name": "Augusta",
            "last_name": "King",
            "email": "augusta@example.com",
            "phone": "+33123456789",
            "company": "Babbage Engines",
            "notes": "Updated profile",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    contact.refresh_from_db()
    assert contact.first_name == "Augusta"
    assert contact.email == "augusta@example.com"


@pytest.mark.django_db
def test_member_can_delete_their_contact(authenticated_client, contact):
    response = authenticated_client.delete(reverse("contact-detail", args=[contact.pk]))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Contact.objects.filter(pk=contact.pk).exists()


@pytest.mark.django_db
def test_member_cannot_retrieve_another_members_contact(api_client, member, other_member):
    contact = Contact.objects.create(
        owner=other_member, first_name="Grace", last_name="Hopper", email="grace@example.com"
    )
    api_client.force_authenticate(user=member)

    response = api_client.get(reverse("contact-detail", args=[contact.pk]))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["error"]["code"] == "not_found"


@pytest.mark.django_db
def test_member_cannot_update_another_members_contact(api_client, member, other_member):
    contact = Contact.objects.create(
        owner=other_member, first_name="Grace", last_name="Hopper", email="grace@example.com"
    )
    api_client.force_authenticate(user=member)

    response = api_client.patch(
        reverse("contact-detail", args=[contact.pk]), {"first_name": "Changed"}, format="json"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    contact.refresh_from_db()
    assert contact.first_name == "Grace"


@pytest.mark.django_db
def test_member_cannot_delete_another_members_contact(api_client, member, other_member):
    contact = Contact.objects.create(
        owner=other_member, first_name="Grace", last_name="Hopper", email="grace@example.com"
    )
    api_client.force_authenticate(user=member)

    response = api_client.delete(reverse("contact-detail", args=[contact.pk]))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert Contact.objects.filter(pk=contact.pk).exists()


@pytest.mark.django_db
def test_contact_rejects_an_invalid_email(authenticated_client):
    response = authenticated_client.post(
        reverse("contact-list"),
        {"first_name": "Ada", "last_name": "Lovelace", "email": "not-an-email"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"]["code"] == "validation_error"
    assert "email" in response.data["error"]["details"]


@pytest.mark.django_db
@pytest.mark.usefixtures("contact")
def test_contact_rejects_case_insensitive_duplicate_for_same_owner(authenticated_client):
    response = authenticated_client.post(
        reverse("contact-list"),
        {"first_name": "Another", "last_name": "Person", "email": "ADA@example.com"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Contact.objects.count() == 1


@pytest.mark.django_db
def test_different_members_may_use_the_same_contact_email(api_client, other_member, contact):
    api_client.force_authenticate(user=other_member)

    response = api_client.post(
        reverse("contact-list"),
        {"first_name": "Ada", "last_name": "Lovelace", "email": contact.email},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert Contact.objects.filter(email__iexact=contact.email).count() == 2


@pytest.mark.django_db
def test_contact_requires_first_and_last_names(authenticated_client):
    response = authenticated_client.post(
        reverse("contact-list"), {"email": "ada@example.com"}, format="json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "first_name" in response.data["error"]["details"]
    assert "last_name" in response.data["error"]["details"]


@pytest.mark.django_db
def test_contact_optional_fields_can_be_blank(authenticated_client):
    response = authenticated_client.post(
        reverse("contact-list"),
        {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "phone": "",
            "company": "",
            "notes": "",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["phone"] == ""
    assert response.data["company"] == ""
    assert response.data["notes"] == ""


@pytest.mark.django_db
def test_contact_id_and_timestamps_are_read_only(authenticated_client):
    response = authenticated_client.post(
        reverse("contact-list"),
        {
            "id": 9876,
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "created_at": "2000-01-01T00:00:00Z",
            "updated_at": "2000-01-01T00:00:00Z",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["id"] != 9876
    assert response.data["created_at"].startswith("2000") is False


@pytest.mark.django_db
def test_contacts_are_ordered_by_last_name_and_first_name(authenticated_client, member):
    Contact.objects.create(
        owner=member, first_name="Grace", last_name="Hopper", email="grace@example.com"
    )
    Contact.objects.create(
        owner=member, first_name="Ada", last_name="Byron", email="ada@example.com"
    )

    response = authenticated_client.get(reverse("contact-list"))

    assert [item["last_name"] for item in response.data] == ["Byron", "Hopper"]


@pytest.mark.django_db
def test_contact_manager_can_list_all_contacts(api_client, manager, member, other_member):
    Contact.objects.create(
        owner=member, first_name="Ada", last_name="Lovelace", email="ada@example.com"
    )
    Contact.objects.create(
        owner=other_member, first_name="Grace", last_name="Hopper", email="grace@example.com"
    )
    api_client.force_authenticate(user=manager)

    response = api_client.get(reverse("contact-list"))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2


@pytest.mark.django_db
def test_contact_manager_can_retrieve_another_members_contact(api_client, manager, contact):
    api_client.force_authenticate(user=manager)

    response = api_client.get(reverse("contact-detail", args=[contact.pk]))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_registration_creates_a_member_with_a_hashed_password(api_client):
    password = "K4#fJ9!pZ2@r"
    response = api_client.post(
        reverse("register"),
        {
            "username": "new-member",
            "email": "new-member@example.com",
            "password": password,
            "password_confirm": password,
        },
        format="json",
    )

    user = get_user_model().objects.get(username="new-member")
    assert response.status_code == status.HTTP_201_CREATED
    assert user.check_password(password)
    assert response.data["role"] == "member"
    assert "password" not in response.data


@pytest.mark.django_db
def test_registration_rejects_mismatched_passwords(api_client):
    response = api_client.post(
        reverse("register"),
        {
            "username": "new-member",
            "email": "new-member@example.com",
            "password": "K4#fJ9!pZ2@r",
            "password_confirm": "different",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password_confirm" in response.data["error"]["details"]
    assert not get_user_model().objects.filter(username="new-member").exists()


@pytest.mark.django_db
def test_registration_rejects_weak_passwords(api_client):
    response = api_client.post(
        reverse("register"),
        {
            "username": "new-member",
            "email": "new-member@example.com",
            "password": "password",
            "password_confirm": "password",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in response.data["error"]["details"]


@pytest.mark.django_db
@pytest.mark.usefixtures("member")
def test_registration_rejects_case_insensitive_duplicate_email(api_client):
    response = api_client.post(
        reverse("register"),
        {
            "username": "new-member",
            "email": "ALICE@example.com",
            "password": "K4#fJ9!pZ2@r",
            "password_confirm": "K4#fJ9!pZ2@r",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data["error"]["details"]


@pytest.mark.django_db
def test_registration_rejects_duplicate_username(api_client, member):
    response = api_client.post(
        reverse("register"),
        {
            "username": member.username,
            "email": "another@example.com",
            "password": "K4#fJ9!pZ2@r",
            "password_confirm": "K4#fJ9!pZ2@r",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_login_rejects_invalid_password(api_client, member):
    response = api_client.post(
        reverse("token_obtain_pair"),
        {"username": member.username, "password": "incorrect"},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_login_returns_member_role_in_jwt(api_client, member):
    response = api_client.post(
        reverse("token_obtain_pair"),
        {"username": member.username, "password": "Strong-pass-123"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert AccessToken(response.data["access"])["role"] == "member"
    assert "refresh" in response.data


@pytest.mark.django_db
def test_login_returns_contact_manager_role_in_jwt(api_client, manager):
    response = api_client.post(
        reverse("token_obtain_pair"),
        {"username": manager.username, "password": "Strong-pass-123"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert AccessToken(response.data["access"])["role"] == "contact_manager"


@pytest.mark.django_db
def test_current_user_requires_authentication(api_client):
    response = api_client.get(reverse("current-user"))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_current_user_returns_authenticated_profile(authenticated_client, member):
    response = authenticated_client.get(reverse("current-user"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "id": member.pk,
        "username": "alice",
        "email": "alice@example.com",
        "role": "member",
    }


@pytest.mark.django_db
def test_access_token_authenticates_api_requests(api_client, member):
    token_response = api_client.post(
        reverse("token_obtain_pair"),
        {"username": member.username, "password": "Strong-pass-123"},
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}")

    response = api_client.get(reverse("contact-list"))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_refresh_endpoint_returns_new_access_token(api_client, member):
    token_response = api_client.post(
        reverse("token_obtain_pair"),
        {"username": member.username, "password": "Strong-pass-123"},
        format="json",
    )

    response = api_client.post(
        reverse("token_refresh"),
        {"refresh": token_response.data["refresh"]},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
