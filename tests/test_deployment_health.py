from sqlalchemy.exc import OperationalError

from contacts.db import get_db
from contacts.main import app


def test_liveness_check_reports_running_process(client):
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check_reports_available_database(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_check_returns_503_when_database_is_unavailable(client):
    class UnavailableSession:
        def execute(self, _statement):
            raise OperationalError("SELECT 1", {}, Exception("database unavailable"))

    def unavailable_db():
        yield UnavailableSession()

    app.dependency_overrides[get_db] = unavailable_db

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Service temporairement indisponible."}
