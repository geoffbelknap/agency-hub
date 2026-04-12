from pathlib import Path
import json


def load_schema(name: str) -> dict:
    return json.loads(Path("schemas", name).read_text())


def validate_required_fields(doc: dict, required: list[str]) -> None:
    missing = [field for field in required if field not in doc]
    assert not missing, f"missing required fields: {missing}"


def test_publisher_schema_accepts_verified_org():
    schema = load_schema("publisher.schema.json")
    validate_required_fields(schema, ["title", "type", "required", "properties"])
    doc = {
        "publisher_id": "org:agency-platform",
        "kind": "organization",
        "display_name": "Agency Platform",
        "verification": {
            "status": "verified",
            "method": "oidc_repository_binding",
            "verified_at": "2026-04-12T00:00:00Z",
        },
    }
    validate_required_fields(doc, schema["required"])
    assert doc["kind"] in schema["properties"]["kind"]["enum"]
    assert doc["verification"]["status"] in schema["properties"]["verification"]["properties"]["status"]["enum"]


def test_assurance_schema_accepts_ask_partial():
    schema = load_schema("assurance.schema.json")
    validate_required_fields(schema, ["title", "type", "required", "properties"])
    doc = {
        "artifact": {"kind": "connector", "name": "slack-interactivity", "version": "1.0.0"},
        "issuer": {"hub_id": "hub:official:agency", "statement_id": "stmt-123"},
        "statement_type": "ask_reviewed",
        "result": "ASK-Partial",
        "review_scope": "artifact-definition",
        "reviewer_type": "combined",
        "policy_version": "2026-04-12",
        "timestamp": "2026-04-12T00:00:00Z",
        "evidence": {"pull_request": "https://github.com/geoffbelknap/agency-hub/pull/47"},
    }
    validate_required_fields(doc, schema["required"])
    assert doc["result"] in schema["properties"]["result"]["enum"]
    assert doc["reviewer_type"] in schema["properties"]["reviewer_type"]["enum"]
