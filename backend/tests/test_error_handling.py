"""Tests for global exception handlers in main.py (TDD — tests written before implementation)."""

from fastapi.testclient import TestClient


class TestValidationErrorHandler:
    def test_returns_422_with_code_and_fields(self, admin_client):
        # POST to /api/clients/ with empty body {} triggers RequestValidationError
        # because ClientCreate requires name (min_length=1) and industry_type
        resp = admin_client.post("/api/clients/", json={})
        assert resp.status_code == 422
        body = resp.json()
        assert body["code"] == "VALIDATION_ERROR"
        assert isinstance(body["fields"], list)
        assert len(body["fields"]) > 0
        for f in body["fields"]:
            assert "field" in f
            assert "message" in f

    def test_detail_key_present(self, admin_client):
        resp = admin_client.post("/api/clients/", json={})
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_field_names_have_body_stripped(self, admin_client):
        # The "body" prefix from the loc path should be stripped
        resp = admin_client.post("/api/clients/", json={})
        assert resp.status_code == 422
        fields = resp.json()["fields"]
        field_names = [f["field"] for f in fields]
        # None of the field names should start with "body."
        for name in field_names:
            assert not name.startswith("body."), (
                f"Field name '{name}' still has 'body.' prefix"
            )


class TestUnhandledExceptionHandler:
    def test_returns_500_no_stack_trace(self):
        # Build an isolated mini-app copying only the handlers
        from fastapi import FastAPI
        from fastapi.exceptions import RequestValidationError
        from fastapi.testclient import TestClient
        from app.main import validation_error_handler, unhandled_exception_handler

        mini = FastAPI()
        mini.add_exception_handler(RequestValidationError, validation_error_handler)
        mini.add_exception_handler(Exception, unhandled_exception_handler)

        @mini.get("/crash")
        async def crash():
            raise RuntimeError("intentional boom")

        client = TestClient(mini, raise_server_exceptions=False)
        resp = client.get("/crash")
        assert resp.status_code == 500
        assert resp.json() == {"detail": "Internal server error"}
        assert "traceback" not in resp.text.lower()
        assert "runtimeerror" not in resp.text.lower()
        assert "boom" not in resp.text.lower()

    def test_http_exception_passes_through(self, admin_client):
        resp = admin_client.get("/api/clients/nonexistent-uuid-that-does-not-exist")
        assert resp.status_code in (404, 422)

    def test_500_body_has_no_exception_message(self):
        from fastapi import FastAPI
        from fastapi.exceptions import RequestValidationError
        from fastapi.testclient import TestClient
        from app.main import validation_error_handler, unhandled_exception_handler

        mini = FastAPI()
        mini.add_exception_handler(RequestValidationError, validation_error_handler)
        mini.add_exception_handler(Exception, unhandled_exception_handler)

        @mini.get("/secret-error")
        async def secret_error():
            raise ValueError("secret DB password is abc123")

        client = TestClient(mini, raise_server_exceptions=False)
        resp = client.get("/secret-error")
        assert resp.status_code == 500
        # Sensitive information must NOT leak into response
        assert "secret" not in resp.text.lower()
        assert "abc123" not in resp.text
        assert "valueerror" not in resp.text.lower()


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_has_status_key(self, client):
        resp = client.get("/health")
        body = resp.json()
        assert "status" in body
        assert body["status"] in ("ok", "degraded")

    def test_health_has_db_key(self, client):
        resp = client.get("/health")
        body = resp.json()
        assert "db" in body
        assert body["db"] in ("ok", "error")

    def test_health_no_version_key(self, client):
        resp = client.get("/health")
        body = resp.json()
        assert "version" not in body

    def test_health_degrades_when_db_is_down(self, monkeypatch):
        """Health endpoint returns degraded (200) when DB probe raises."""
        import app.main as main_module

        class _FailSvc:
            def table(self, *a, **kw):
                raise RuntimeError("simulated DB failure")

        monkeypatch.setattr(main_module, "get_service_client", lambda: _FailSvc())
        client = TestClient(main_module.app)
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["db"] == "error"
