def valid_contact_payload(**overrides) -> dict:
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "contact_type": "business",
        "owner": "owner-1",
        "created_by": "admin-1",
        "email": "jane@example.com",
        "phone": "12345678901",
        "attributes": {"source": "test"},
        "list_of_profile_ids": [],
    }
    payload.update(overrides)
    return payload


def minimal_contact_payload(**overrides) -> dict:
    payload = {
        "first_name": "Mini",
        "last_name": "User",
        "contact_type": "private",
        "owner": "owner-min",
        "created_by": "admin-min",
        "phone": "19876543210",  # only phone, no email
    }
    payload.update(overrides)
    return payload


def invalid_email_payload(**overrides) -> dict:
    payload = valid_contact_payload(email="not-an-email")
    payload.update(overrides)
    return payload


def missing_contact_fields(**overrides) -> dict:
    payload = {
        "first_name": "NoLast",
        "owner": "missing-fields",
        # missing last_name, created_by, etc.
    }
    payload.update(overrides)
    return payload


def duplicate_contact_payload() -> list[dict]:
    return [
        valid_contact_payload(email="duplicate@example.com", phone=None),
        valid_contact_payload(email=None, phone="12345678901"),
    ]
