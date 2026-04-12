from pathlib import Path
import json


def load_publisher(publisher_id: str) -> dict:
    return json.loads(Path("publishers", f"{publisher_id}.json").read_text())


def test_verified_org_publisher_record_exists():
    doc = load_publisher("agency-platform")
    assert doc["verification"]["status"] == "verified"
    assert doc["kind"] == "organization"


def test_verified_individual_publisher_record_exists():
    doc = load_publisher("geoffbelknap")
    assert doc["verification"]["status"] == "verified"
    assert doc["kind"] == "individual"
