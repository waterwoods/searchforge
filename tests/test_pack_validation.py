from services.fiqa_api.inbox_triage.pack_validation import validate_client_pack_layout


def test_pack_validation_known_client():
    assert validate_client_pack_layout("chen_kui") == []


def test_pack_validation_missing():
    issues = validate_client_pack_layout("__definitely_missing_client__")
    assert issues and "missing" in issues[0]


def test_pack_validation_empty_id():
    assert validate_client_pack_layout("") == ["client_id is empty"]
