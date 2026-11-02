from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, SimpleTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from .models import Contact


class ContactApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="alice",
            password="Strong-pass-123",
        )
        self.other_user = user_model.objects.create_user(
            username="bob",
            password="Other-pass-456",
        )
        self.list_url = reverse("contact-list")

    def test_contact_endpoints_require_authentication(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["error"]["code"],
            "not_authenticated",
        )

    def test_user_can_create_and_list_only_their_contacts(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.list_url,
            {
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "ada@example.com",
                "phone": "+33123456789",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Contact.objects.get().owner, self.owner)
        self.assertNotIn("owner", response.data)

        Contact.objects.create(
            owner=self.other_user,
            first_name="Grace",
            last_name="Hopper",
            email="grace@example.com",
        )
        listed = self.client.get(self.list_url)

        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listed.data), 1)
        self.assertEqual(listed.data[0]["email"], "ada@example.com")

    def test_user_cannot_read_or_update_another_users_contact(self):
        contact = Contact.objects.create(
            owner=self.other_user,
            first_name="Grace",
            last_name="Hopper",
            email="grace@example.com",
        )
        self.client.force_authenticate(user=self.owner)
        detail_url = reverse("contact-detail", args=[contact.pk])

        response = self.client.get(detail_url)
        update = self.client.patch(
            detail_url,
            {"first_name": "Changed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(update.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"]["code"], "not_found")
        contact.refresh_from_db()
        self.assertEqual(contact.first_name, "Grace")

    def test_invalid_email_and_duplicate_owner_email_are_rejected(self):
        self.client.force_authenticate(user=self.owner)
        invalid = self.client.post(
            self.list_url,
            {
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "not-an-email",
            },
            format="json",
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", invalid.data["error"]["details"])
        self.assertEqual(invalid.data["error"]["code"], "validation_error")

        Contact.objects.create(
            owner=self.owner,
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
        )
        duplicate = self.client.post(
            self.list_url,
            {
                "first_name": "Another",
                "last_name": "Person",
                "email": "ADA@example.com",
            },
            format="json",
        )

        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", duplicate.data["error"]["details"])

    def test_api_security_headers_and_orm_data_handling(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.list_url,
            {
                "first_name": "Alice'; DROP TABLE contacts_contact; --",
                "last_name": "<script>alert('xss')</script>",
                "email": "safe@example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(Contact.objects.count(), 1)
        stored_contact = Contact.objects.get()
        self.assertEqual(
            stored_contact.first_name,
            "Alice'; DROP TABLE contacts_contact; --",
        )
        self.assertEqual(stored_contact.last_name, "<script>alert('xss')</script>")

    def test_owner_can_update_and_delete_contact(self):
        contact = Contact.objects.create(
            owner=self.owner,
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
        )
        self.client.force_authenticate(user=self.owner)
        detail_url = reverse("contact-detail", args=[contact.pk])

        updated = self.client.patch(
            detail_url,
            {"company": "Analytical Engines"},
            format="json",
        )
        deleted = self.client.delete(detail_url)

        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["company"], "Analytical Engines")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Contact.objects.filter(pk=contact.pk).exists())


class JwtTokenTests(APITestCase):
    def test_user_can_obtain_jwt_access_and_refresh_tokens(self):
        user_model = get_user_model()
        user_model.objects.create_user(username="alice", password="Strong-pass-123")

        response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "alice", "password": "Strong-pass-123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )
        contacts_response = self.client.get(reverse("contact-list"))

        self.assertEqual(contacts_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            AccessToken(response.data["access"])["role"],
            "member",
        )

        profile = self.client.get(reverse("current-user"))
        self.assertEqual(profile.status_code, status.HTTP_200_OK)
        self.assertEqual(profile.data["role"], "member")

        refreshed = self.client.post(
            reverse("token_refresh"),
            {"refresh": response.data["refresh"]},
            format="json",
        )
        self.assertEqual(refreshed.status_code, status.HTTP_200_OK)
        self.assertIn("access", refreshed.data)


class RegistrationAndRoleTests(APITestCase):
    def test_registration_creates_member_with_hashed_password(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "new-member",
                "email": "new-member@example.com",
                "password": "K4#fJ9!pZ2@r",
                "password_confirm": "K4#fJ9!pZ2@r",
                "is_staff": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(username="new-member")
        self.assertTrue(user.check_password("K4#fJ9!pZ2@r"))
        self.assertFalse(user.is_staff)
        self.assertEqual(response.data["role"], "member")
        self.assertNotIn("password", response.data)

    def test_registration_rejects_mismatched_and_weak_passwords(self):
        mismatch = self.client.post(
            reverse("register"),
            {
                "username": "new-member",
                "email": "new-member@example.com",
                "password": "K4#fJ9!pZ2@r",
                "password_confirm": "different",
            },
            format="json",
        )
        weak_password = self.client.post(
            reverse("register"),
            {
                "username": "new-member",
                "email": "new-member@example.com",
                "password": "password",
                "password_confirm": "password",
            },
            format="json",
        )

        self.assertEqual(mismatch.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "password_confirm",
            mismatch.data["error"]["details"],
        )
        self.assertEqual(weak_password.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", weak_password.data["error"]["details"])
        self.assertFalse(get_user_model().objects.filter(username="new-member").exists())

    def test_contact_manager_group_can_access_all_contacts(self):
        user_model = get_user_model()
        manager = user_model.objects.create_user(
            username="manager",
            password="Strong-pass-123",
        )
        member = user_model.objects.create_user(
            username="member",
            password="Strong-pass-456",
        )
        manager_group, _ = Group.objects.get_or_create(name="contact_managers")
        manager.groups.add(manager_group)
        Contact.objects.create(
            owner=member,
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
        )
        self.client.force_authenticate(user=manager)

        response = self.client.get(reverse("contact-list"))
        profile = self.client.get(reverse("current-user"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(profile.data["role"], "contact_manager")

        token_response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "manager", "password": "Strong-pass-123"},
            format="json",
        )
        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            AccessToken(token_response.data["access"])["role"],
            "contact_manager",
        )


class CsrfMiddlewareTests(SimpleTestCase):
    def test_admin_login_post_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)

        response = client.post(
            reverse("admin:login"),
            {"username": "alice", "password": "invalid"},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
