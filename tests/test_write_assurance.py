from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from write_assurance import build_statement, build_summary, artifact_from_component_file


def test_build_statement_for_partial_review():
    stmt = build_statement(
        artifact={"kind": "connector", "name": "slack-interactivity", "version": "1.1.0"},
        result="ASK-Partial",
        review_scope="package-change",
        reviewer_type="automated",
    )
    assert stmt["statement_type"] == "ask_reviewed"
    assert stmt["result"] == "ASK-Partial"
    assert stmt["review_scope"] == "package-change"
    assert stmt["reviewer_type"] == "automated"
    assert stmt["artifact"]["kind"] == "connector"
    assert stmt["artifact"]["name"] == "slack-interactivity"


def test_build_summary_wraps_statements():
    stmt = build_statement(
        artifact={"kind": "connector", "name": "google-drive-admin", "version": "1.1.0"},
        result="ASK-Pass",
        review_scope="package-change",
        reviewer_type="automated",
    )
    summary = build_summary([stmt])
    assert summary["schema_version"] == 1
    assert len(summary["statements"]) == 1
    assert summary["statements"][0]["artifact"]["name"] == "google-drive-admin"


def test_artifact_from_component_file_reads_kind_name_and_version():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "connectors" / "google-drive-admin"
        path.mkdir(parents=True)
        component = path / "connector.yaml"
        component.write_text(
            "kind: connector\nname: google-drive-admin\nversion: '1.1.0'\nsource:\n  type: none\n",
            encoding="utf-8",
        )

        artifact = artifact_from_component_file(component)

    assert artifact == {"kind": "connector", "name": "google-drive-admin", "version": "1.1.0"}
