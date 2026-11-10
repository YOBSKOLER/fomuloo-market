from uuid import UUID


def payload():
    return {
        "nom": "Lovelace",
        "prenom": "Ada",
        "email": "ada@example.com",
        "groupe": "CLIENT",
    }


def test_openapi_lists_both_versioned_contracts(client):
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/contacts" in paths
    assert "/api/v2/contacts" in paths
    assert "/api/v1/contacts/search" in paths
    assert "/api/v2/contacts/search" in paths
    assert "/contacts" not in paths


def test_v1_create_keeps_stable_contact_response(client):
    response = client.post("/api/v1/contacts", json=payload())

    assert response.status_code == 201
    assert UUID(response.json()["id"])
    assert "nom_complet" not in response.json()


def test_v2_create_adds_computed_full_name(client):
    response = client.post("/api/v2/contacts", json=payload())

    assert response.status_code == 201
    assert response.json()["nom_complet"] == "Ada Lovelace"


def test_v2_pagination_includes_full_name(client):
    client.post("/api/v2/contacts", json=payload())

    response = client.get("/api/v2/contacts?page=1&limit=10")

    assert response.status_code == 200
    assert response.json()["items"][0]["nom_complet"] == "Ada Lovelace"


def test_v1_and_v2_read_the_same_contact(client):
    created = client.post("/api/v1/contacts", json=payload()).json()

    v1_response = client.get(f"/api/v1/contacts/{created['id']}")
    v2_response = client.get(f"/api/v2/contacts/{created['id']}")

    assert v1_response.status_code == 200
    assert v2_response.status_code == 200
    assert v1_response.json()["id"] == v2_response.json()["id"]
    assert v2_response.json()["nom_complet"] == "Ada Lovelace"


def test_legacy_route_remains_available_but_is_not_in_openapi(client):
    response = client.post("/contacts", json=payload())

    assert response.status_code == 201
    assert "/contacts" not in client.get("/openapi.json").json()["paths"]
