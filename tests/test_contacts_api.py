from uuid import UUID

import pytest


def contact_payload(**overrides):
    payload = {
        "nom": "Lovelace",
        "prenom": "Ada",
        "email": "ada@example.com",
        "telephone": "+33123456789",
        "entreprise": "Analytical Engines",
        "groupe": "CLIENT",
        "notes": "Premier contact",
    }
    return payload | overrides


def create_contact(client, **overrides):
    return client.post("/contacts", json=contact_payload(**overrides))


def test_root_openapi_documents_contact_endpoints(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/contacts" in response.json()["paths"]
    assert "/contacts/search" in response.json()["paths"]


def test_docs_page_is_available(client):
    response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text


def test_create_contact_returns_201_and_generated_fields(client):
    response = create_contact(client)

    assert response.status_code == 201
    body = response.json()
    assert body["nom"] == "Lovelace"
    assert body["groupe"] == "CLIENT"
    assert UUID(body["id"])
    assert body["created_at"]
    assert body["updated_at"]


def test_create_contact_rejects_null_group(client):
    response = create_contact(client, groupe=None)

    assert response.status_code == 422


def test_create_contact_defaults_group_when_omitted(client):
    response = client.post(
        "/contacts",
        json={"nom": "Hopper", "email": "grace@example.com"},
    )

    assert response.status_code == 201
    assert response.json()["groupe"] == "AUTRE"


def test_create_contact_rejects_missing_name(client):
    response = client.post(
        "/contacts",
        json={"email": "ada@example.com"},
    )

    assert response.status_code == 422
    assert any(error["loc"][-1] == "nom" for error in response.json()["detail"])


def test_create_contact_rejects_blank_name(client):
    response = create_contact(client, nom="")

    assert response.status_code == 422


def test_create_contact_rejects_invalid_email(client):
    response = create_contact(client, email="not-an-email")

    assert response.status_code == 422


def test_create_contact_rejects_unknown_group(client):
    response = create_contact(client, groupe="PROSPECT")

    assert response.status_code == 422


def test_create_contact_rejects_name_over_maximum_length(client):
    response = create_contact(client, nom="x" * 101)

    assert response.status_code == 422


def test_duplicate_email_returns_400(client):
    create_contact(client)

    response = create_contact(client, nom="Autre", prenom="Personne")

    assert response.status_code == 400
    assert response.json()["detail"] == "Un contact utilise déjà cette adresse e-mail."


def test_list_contacts_returns_empty_page_for_empty_database(client):
    response = client.get("/contacts")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "limit": 10, "pages": 0}


def test_list_contacts_returns_paginated_contacts(client):
    create_contact(client, nom="Alpha", email="alpha@example.com")
    create_contact(client, nom="Bravo", email="bravo@example.com")
    create_contact(client, nom="Charlie", email="charlie@example.com")

    response = client.get("/contacts?page=2&limit=2")

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert response.json()["pages"] == 2
    assert [item["nom"] for item in response.json()["items"]] == ["Charlie"]


@pytest.mark.parametrize(
    ("params", "invalid_field"),
    [
        ("page=0", "page"),
        ("limit=0", "limit"),
        ("limit=101", "limit"),
    ],
)
def test_list_contacts_rejects_invalid_pagination(client, params, invalid_field):
    response = client.get(f"/contacts?{params}")

    assert response.status_code == 422
    assert any(error["loc"][-1] == invalid_field for error in response.json()["detail"])


def test_list_contacts_is_sorted_by_name(client):
    create_contact(client, nom="Zulu", email="zulu@example.com")
    create_contact(client, nom="Alpha", email="alpha@example.com")

    response = client.get("/contacts")

    assert [item["nom"] for item in response.json()["items"]] == ["Alpha", "Zulu"]


def test_search_finds_contact_by_name(client):
    create_contact(client)

    response = client.get("/contacts/search?q=love")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["nom"] == "Lovelace"


def test_search_finds_contact_by_first_name(client):
    create_contact(client)

    response = client.get("/contacts/search?q=ada")

    assert len(response.json()) == 1
    assert response.json()[0]["prenom"] == "Ada"


def test_search_finds_contact_by_email(client):
    create_contact(client)

    response = client.get("/contacts/search?q=example.com")

    assert len(response.json()) == 1
    assert response.json()[0]["email"] == "ada@example.com"


def test_search_finds_contact_by_group(client):
    create_contact(client, groupe="FOURNISSEUR")

    response = client.get("/contacts/search?q=fournisseur")

    assert len(response.json()) == 1
    assert response.json()[0]["groupe"] == "FOURNISSEUR"


def test_search_is_case_insensitive(client):
    create_contact(client)

    response = client.get("/contacts/search?q=LOVELACE")

    assert len(response.json()) == 1


def test_search_returns_empty_list_when_no_contact_matches(client):
    create_contact(client)

    response = client.get("/contacts/search?q=unknown")

    assert response.status_code == 200
    assert response.json() == []


def test_search_requires_query(client):
    response = client.get("/contacts/search")

    assert response.status_code == 422


def test_get_contact_returns_contact_by_uuid(client):
    created = create_contact(client).json()

    response = client.get(f"/contacts/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_contact_returns_404_for_unknown_uuid(client):
    response = client.get("/contacts/00000000-0000-0000-0000-000000000001")

    assert response.status_code == 404
    assert response.json()["detail"] == "Contact introuvable."


def test_get_contact_returns_422_for_invalid_uuid(client):
    response = client.get("/contacts/not-a-uuid")

    assert response.status_code == 422


def test_put_replaces_contact(client):
    created = create_contact(client).json()
    replacement = contact_payload(
        nom="King",
        prenom="Augusta",
        email="augusta@example.com",
    )

    response = client.put(f"/contacts/{created['id']}", json=replacement)

    assert response.status_code == 200
    assert response.json()["nom"] == "King"
    assert response.json()["email"] == "augusta@example.com"


def test_put_returns_404_for_unknown_contact(client):
    response = client.put(
        "/contacts/00000000-0000-0000-0000-000000000001",
        json=contact_payload(),
    )

    assert response.status_code == 404


def test_patch_updates_only_provided_fields(client):
    created = create_contact(client).json()

    response = client.patch(
        f"/contacts/{created['id']}",
        json={"telephone": "+33987654321"},
    )

    assert response.status_code == 200
    assert response.json()["telephone"] == "+33987654321"
    assert response.json()["nom"] == "Lovelace"


def test_patch_can_clear_optional_field(client):
    created = create_contact(client).json()

    response = client.patch(
        f"/contacts/{created['id']}",
        json={"telephone": None},
    )

    assert response.status_code == 200
    assert response.json()["telephone"] is None


def test_patch_rejects_empty_body(client):
    created = create_contact(client).json()

    response = client.patch(f"/contacts/{created['id']}", json={})

    assert response.status_code == 422


def test_patch_rejects_invalid_email(client):
    created = create_contact(client).json()

    response = client.patch(
        f"/contacts/{created['id']}",
        json={"email": "invalid"},
    )

    assert response.status_code == 422


def test_patch_returns_404_for_unknown_contact(client):
    response = client.patch(
        "/contacts/00000000-0000-0000-0000-000000000001",
        json={"nom": "Changed"},
    )

    assert response.status_code == 404


def test_delete_contact_returns_204_and_removes_record(client):
    created = create_contact(client).json()

    response = client.delete(f"/contacts/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/contacts/{created['id']}").status_code == 404


def test_delete_returns_404_for_unknown_contact(client):
    response = client.delete("/contacts/00000000-0000-0000-0000-000000000001")

    assert response.status_code == 404
