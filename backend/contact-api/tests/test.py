import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.database.daos import ContactQuery, DatabaseCleanerQuery
from app.api.models import ContactCreate, ContactType
from app.api.services import DatabaseCleaner
from sqlalchemy.exc import SQLAlchemyError
from app.utils.config import Config, BasicConfig
from app.database.db import get_db, initialized_tenants
from app.main import app
from tests.payloads import (
    valid_contact_payload,
    minimal_contact_payload,
    invalid_email_payload,
    missing_contact_fields,
)

client = TestClient(app)
main_route_prefix = "/sales/contacts"
tenant_ids = ["dev"]
created_contact_id_full = {}
created_contact_id_minimal = {}
searchable_contact_id = {}


def test_health_check():
    response = client.get(f"{main_route_prefix}/health-check")
    assert response.status_code == 200
    assert response.json() == {"HEALTH": "OK"}


@pytest.mark.parametrize("tenant", tenant_ids)
class TestBasicCrudOperations:
    @staticmethod
    def test_get_contacts(tenant):
        response = client.get(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 200
        assert response.json() == {
            "offset": 0,
            "limit": 100,
            "count": 0,
            "contacts": []
        }

    @staticmethod
    def test_create_contact(tenant):
        payload = valid_contact_payload()
        response = client.post(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant}, json=payload)
        assert response.status_code == 201
        created_contact_id_full[tenant] = response.json()["contact_id"]

    @staticmethod
    def test_create_duplicate_contact(tenant):
        payload = valid_contact_payload()
        response = client.post(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant}, json=payload)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    @staticmethod
    def test_create_minimal_contact(tenant):
        payload = minimal_contact_payload()
        response = client.post(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant}, json=payload)
        assert response.status_code == 201
        created_contact_id_minimal[tenant] = response.json()["contact_id"]

    @staticmethod
    def test_create_searchable_contact(tenant):
        payload = valid_contact_payload(
            first_name="SearchFirst",
            last_name="SearchLast",
            email="search@example.com",
            phone="1234567890"
        )
        response = client.post(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant}, json=payload)
        assert response.status_code == 201
        searchable_contact_id[tenant] = response.json()["contact_id"]

    @staticmethod
    def test_get_all_contacts(tenant):
        response = client.get(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 200
        assert isinstance(response.json()["contacts"], list)

    @staticmethod
    def test_get_contact_by_id(tenant):
        contact_id = created_contact_id_full[tenant]
        response = client.get(f"{main_route_prefix}/{contact_id}", headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 200
        assert response.json()["contact_id"] == contact_id

    @staticmethod
    def test_update_contact(tenant):
        contact_id = created_contact_id_full[tenant]
        updated_payload = valid_contact_payload(first_name="UpdatedName")
        response = client.put(f"{main_route_prefix}/{contact_id}", headers={"Ts-Tenant-Id": tenant},
                              json=updated_payload)
        assert response.status_code == 200
        assert response.json()["first_name"] == "UpdatedName"


@pytest.mark.parametrize("tenant", tenant_ids)
class TestValidationScenarios:
    @staticmethod
    def test_create_invalid_email(tenant):
        payload = invalid_email_payload()
        response = client.post(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant}, json=payload)
        assert response.status_code == 422

    @staticmethod
    def test_create_missing_fields(tenant):
        payload = missing_contact_fields()
        response = client.post(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant}, json=payload)
        assert response.status_code == 422

    @staticmethod
    def test_fails_when_email_and_phone_missing(tenant):
        payload = valid_contact_payload(phone=None, email=None)
        response = client.post(
            f"{main_route_prefix}/",
            headers={"Ts-Tenant-Id": tenant},
            json=payload
        )
        assert response.status_code == 422
        assert "At least one of email or phone must be provided." in response.text

    @staticmethod
    def test_invalid_phone_format(tenant):
        payload = valid_contact_payload()
        payload["phone"] = "123"
        response = client.post(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant}, json=payload)
        assert response.status_code == 422

    @staticmethod
    def test_phone_missing_plus_prefix(tenant):
        payload = valid_contact_payload()
        payload["phone"] = "+123456789"
        response = client.post(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant}, json=payload)
        assert response.status_code == 422

    @staticmethod
    def test_name_too_long(tenant):
        payload = valid_contact_payload()
        payload["first_name"] = "a" * 101
        response = client.post(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant}, json=payload)
        assert response.status_code == 422

    @staticmethod
    def test_email_length_exceeded(tenant):
        payload = valid_contact_payload()
        payload["email"] = "a" * 246 + "@test.com"
        response = client.post(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant}, json=payload)
        assert response.status_code == 422

    @staticmethod
    def test_first_name_whitespace_rejected(tenant):
        payload = valid_contact_payload()
        payload["first_name"] = "   "
        response = client.post(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant}, json=payload)
        assert response.status_code == 422
        assert "must not be empty or whitespace" in response.text


@pytest.mark.parametrize("tenant", tenant_ids)
class TestNotFoundAndEdgeCases:
    @staticmethod
    def test_get_nonexistent_contact(tenant):
        response = client.get(f"{main_route_prefix}/00000000-0000-0000-0000-000000000000",
                              headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 404

    @staticmethod
    def test_update_nonexistent_contact(tenant):
        payload = valid_contact_payload()
        response = client.put(f"{main_route_prefix}/00000000-0000-0000-0000-000000000000",
                              headers={"Ts-Tenant-Id": tenant}, json=payload)
        assert response.status_code == 404

    @staticmethod
    def test_delete_nonexistent_contact(tenant):
        response = client.delete(f"{main_route_prefix}/00000000-0000-0000-0000-000000000000",
                                 headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 404

    @staticmethod
    def test_internal_server_error(tenant):
        with patch("app.api.services.ContactLogic.get_contacts", side_effect=Exception("Boom")):
            response = client.get(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant})
            assert response.status_code == 500


class TestContactQueryErrorHandling:
    @staticmethod
    def test_create_contact_db_error():
        db = MagicMock()
        db.add.side_effect = SQLAlchemyError("DB failure")

        contact_data = ContactCreate(**valid_contact_payload())

        with pytest.raises(SQLAlchemyError):
            ContactQuery().create(db=db, contact_data=contact_data)

    @staticmethod
    def test_update_nonexistent_contact():
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = ContactQuery().update(db=db, contact_id="nonexistent", contact_data=valid_contact_payload())
        assert result is None

    @staticmethod
    def test_update_contact_db_error():
        db = MagicMock()
        mock_contact = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_contact
        db.commit.side_effect = SQLAlchemyError("DB failure")

        contact_data = ContactCreate(**valid_contact_payload())

        with pytest.raises(SQLAlchemyError):
            ContactQuery().update(db=db, contact_id="some-id", contact_data=contact_data)

    @staticmethod
    def test_delete_nonexistent_contact():
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = ContactQuery().delete(db=db, contact_id="nonexistent")
        assert result is None

    @staticmethod
    def test_delete_contact_db_error():
        db = MagicMock()
        mock_contact = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_contact
        db.delete.side_effect = SQLAlchemyError("DB failure")

        with pytest.raises(SQLAlchemyError):
            ContactQuery().delete(db=db, contact_id="some-id")

    @staticmethod
    def test_get_db_creates_missing_database():
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None  # Simulate DB not existing

        mock_conn.execute.return_value = mock_result

        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_engine = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            mock_create_engine.return_value = mock_engine

            # You must exhaust the generator to trigger execution
            db_gen = get_db("testtenant")
            next(db_gen)


class TestTenantNonRequired:
    @staticmethod
    def test_get_contacts_without_tenant():
        response = client.get(f"{main_route_prefix}/")
        assert response.status_code == 422
        assert "Ts-Tenant-Id" in response.json()["detail"][0]["loc"]

    @staticmethod
    def test_create_contact_without_tenant():
        payload = valid_contact_payload()
        response = client.post(f"{main_route_prefix}/", json=payload)
        assert response.status_code == 422
        assert "Ts-Tenant-Id" in response.json()["detail"][0]["loc"]

    @staticmethod
    def test_valid_contact_type():
        assert ContactType.validate("private") == ContactType.private
        assert ContactType.validate("business") == ContactType.business

    @staticmethod
    def test_invalid_contact_type():
        with pytest.raises(ValueError) as exc_info:
            ContactType.validate("invalid-type")
        assert "Invalid contact type" in str(exc_info.value)

    @staticmethod
    def test_missing_tenant_header():
        response = client.get(f"{main_route_prefix}/")
        assert response.status_code == 422

    @staticmethod
    def test_invalid_tenant_id_format():
        tenant = "invalid-tenant-id"
        response = client.get(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 422


@pytest.mark.parametrize("tenant", tenant_ids)
class TestRouteServiceErrors:
    @staticmethod
    @patch("app.api.services.ContactLogic.get_contacts")
    def test_get_contacts_logic_error(mock_logic, tenant):
        mock_logic.return_value = (404, "Not Found")
        response = client.get(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 404
        assert "Not Found" in response.text

    @staticmethod
    @patch("app.api.services.ContactLogic.create_contact")
    def test_create_contact_logic_error(mock_logic, tenant):
        mock_logic.return_value = (500, "Internal server error")
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "contact_type": "private",
            "owner": "owner",
            "created_by": "creator",
            "email": "user@example.com"
        }
        response = client.post(f"{main_route_prefix}/", headers={"Ts-Tenant-Id": tenant}, json=payload)
        assert response.status_code == 500
        assert "Internal server error" in response.text

    @staticmethod
    @patch("app.api.services.ContactLogic.get_contact")
    def test_get_contact_logic_error(mock_logic, tenant):
        mock_logic.return_value = (404, "Missing")
        response = client.get(f"{main_route_prefix}/00000000-0000-0000-0000-000000000000",
                              headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 404
        assert "Missing" in response.text

    @staticmethod
    @patch("app.api.services.ContactLogic.update_contact")
    def test_update_contact_logic_error(mock_logic, tenant):
        mock_logic.return_value = (404, "No such contact")
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "contact_type": "business",
            "owner": "owner",
            "created_by": "creator",
            "email": "user@example.com"
        }
        response = client.put(f"{main_route_prefix}/00000000-0000-0000-0000-000000000000",
                              headers={"Ts-Tenant-Id": tenant}, json=payload)
        assert response.status_code == 404
        assert "No such contact" in response.text

    @staticmethod
    @patch("app.api.services.ContactLogic.delete_contact")
    def test_delete_contact_logic_error(mock_logic, tenant):
        mock_logic.return_value = (404, "Can't delete")
        response = client.delete(f"{main_route_prefix}/00000000-0000-0000-0000-000000000000",
                                 headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 404
        assert "Can't delete" in response.text

    @staticmethod
    @patch("app.api.services.DatabaseCleaner.recreate_all_tables")
    def test_recreate_tables_non_200(mock_cleaner, tenant):
        mock_cleaner.return_value = (400, "Bad input")

        response = client.delete(
            f"{main_route_prefix}/recreate-tables?recreate=true",
            headers={"Ts-Tenant-Id": tenant},
        )

        assert response.status_code == 400
        assert "Bad input" in response.text

    @staticmethod
    @patch("app.routers.routes.ContactLogic.search_contacts")
    def test_search_contacts_internal_error(mock_logic, tenant):
        mock_logic.return_value = (404, "Not Found")
        response = client.get(f"{main_route_prefix}/search?query=John", headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 404
        assert "Not Found" in response.text


class TestConfigUtils:
    @staticmethod
    def test_get_property_existing_key():
        config = Config()
        assert config.get_property("POSTGRES_DB_USER") is not None

    @staticmethod
    def test_get_property_missing_key():
        config = Config()
        assert config.get_property("NON_EXISTENT_KEY") is None  # Covers line 19

    @staticmethod
    def test_basic_config_property_passthrough(monkeypatch):
        monkeypatch.setitem(Config()._config, "POSTGRES_DB_PORT", "1234")
        basic_config = BasicConfig()
        assert basic_config.db_port == "1234"


class TestRecreateTablesEndpoint:
    @staticmethod
    @pytest.mark.parametrize("tenant", tenant_ids)
    def test_recreate_tables_without_flag(tenant):
        response = client.delete(
            f"{main_route_prefix}/recreate-tables",
            headers={"Ts-Tenant-Id": tenant},
            params={"recreate": False},
        )
        assert response.status_code == 400
        assert "recreate=True" in response.json()["detail"]

    @staticmethod
    @pytest.mark.parametrize("tenant", tenant_ids)
    def test_recreate_tables_success(tenant):
        with patch("app.database.daos.DatabaseCleanerQuery.recreate_all_tables") as mocked_recreate:
            mocked_recreate.return_value = {"detail": f"Tables recreated for tenant: {tenant}"}
            response = client.delete(
                f"{main_route_prefix}/recreate-tables",
                headers={"Ts-Tenant-Id": tenant},
                params={"recreate": True},
            )
            assert response.status_code == 200
            assert "Tables recreated for tenant" in response.json()["detail"]

    @staticmethod
    @pytest.mark.parametrize("tenant", tenant_ids)
    def test_recreate_tables_success_full_coverage(tenant):
        with patch("app.database.daos.initialized_tenants", {f"{tenant}db"}), \
                patch("app.database.daos.tenant_sessions_postgres",
                      {f"{tenant}db": lambda: MagicMock(close=MagicMock())}), \
                patch("app.database.daos.create_engine") as mock_engine, \
                patch("app.database.daos.Base.metadata.drop_all") as mock_drop_all, \
                patch("app.database.daos.Base.metadata.create_all") as mock_create_all:
            mock_engine.return_value = MagicMock()
            mock_drop_all.return_value = None
            mock_create_all.return_value = None

            response = client.delete(
                f"{main_route_prefix}/recreate-tables",
                headers={"Ts-Tenant-Id": tenant},
                params={"recreate": True},
            )

            assert response.status_code == 200
            assert "Tables recreated for tenant" in response.json()["detail"]

    @staticmethod
    @patch("sqlalchemy.schema.MetaData.drop_all", side_effect=SQLAlchemyError("DB error"))
    def test_sqlalchemy_error_in_recreate_tables(mock_drop_all):
        tenant_id = "testtenant2"
        initialized_tenants.add(tenant_id + "db")

        with pytest.raises(Exception, match="Database error for tenant"):
            DatabaseCleanerQuery.recreate_all_tables(tenant_id=tenant_id, recreate=True)

    @staticmethod
    def test_generic_exception_triggers_500():
        cleaner = DatabaseCleaner()

        def boom(*args, **kwargs):
            raise Exception("boom!")

        cleaner.cleaner.recreate_all_tables = boom

        with pytest.raises(Exception) as exc_info:
            cleaner.recreate_all_tables(tenant_id="some_tenant", recreate=True)

        assert "Internal server error while recreating tables" in str(exc_info.value)

    @staticmethod
    @patch("sqlalchemy.engine.Engine.connect")
    def test_unexpected_error_in_recreate_tables(mock_connect):
        tenant_id = "testtenant"
        initialized_tenants.add(tenant_id + "db")

        mock_connect.side_effect = Exception("Unexpected error")

        with pytest.raises(Exception, match="Unexpected error for tenant"):
            DatabaseCleanerQuery.recreate_all_tables(tenant_id=tenant_id, recreate=True)


@pytest.mark.parametrize("tenant", tenant_ids)
class TestSearchEndpoint:

    def test_search_by_first_name(self, tenant):
        response = client.get(f"{main_route_prefix}/search?query=SearchFirst", headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 200
        assert any(contact["first_name"] == "SearchFirst" for contact in response.json()["contacts"])

    def test_search_by_partial_email(self, tenant):
        response = client.get(f"{main_route_prefix}/search?query=search@", headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 200
        assert any("search@" in contact["email"] for contact in response.json()["contacts"])

    def test_search_by_full_name(self, tenant):
        response = client.get(
            f"{main_route_prefix}/search?query=SearchFirst&query=SearchLast",
            headers={"Ts-Tenant-Id": tenant}
        )
        assert response.status_code == 200
        assert any(
            contact["first_name"] == "SearchFirst" and contact["last_name"] == "SearchLast"
            for contact in response.json()["contacts"]
        )

    def test_search_by_phone(self, tenant):
        response = client.get(f"{main_route_prefix}/search?query=123456", headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 200
        assert any("123456" in contact["phone"] for contact in response.json()["contacts"])


@pytest.mark.parametrize("tenant", tenant_ids)
class TestDeleteContacts:
    @staticmethod
    def test_delete_contact(tenant):
        contact_id = created_contact_id_full[tenant]
        response = client.delete(f"{main_route_prefix}/{contact_id}", headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 200
        assert "successfully deleted" in response.json()["detail"]

        confirm = client.get(f"{main_route_prefix}/{contact_id}", headers={"Ts-Tenant-Id": tenant})
        assert confirm.status_code == 404

    @staticmethod
    def test_cleanup_all_created_contacts(tenant):
        contact_id = created_contact_id_minimal[tenant]
        response = client.delete(f"{main_route_prefix}/{contact_id}", headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 200

        search_contact = searchable_contact_id[tenant]
        response = client.delete(f"{main_route_prefix}/{search_contact}", headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 200

    @staticmethod
    def test_delete_nonexistent_contact(tenant):
        response = client.delete(f"{main_route_prefix}/00000000-0000-0000-0000-000000000000",
                                 headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 404
        assert "not found for deletion" in response.json()["detail"]

    @staticmethod
    def test_search_after_deletion(tenant):
        response = client.get(f"{main_route_prefix}/search?query=123", headers={"Ts-Tenant-Id": tenant})
        assert response.status_code == 200
        assert len(response.json()["contacts"]) == 0
