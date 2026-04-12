#!/usr/bin/env python3
"""Write machine-readable assurance statements for reviewed hub artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import uuid
import yaml


POLICY_VERSION = "2026-04-12"
HUB_ID = "hub:official:agency"


def build_statement(*, artifact: dict, result: str, review_scope: str, reviewer_type: str) -> dict:
    return {
        "artifact": artifact,
        "issuer": {
            "hub_id": HUB_ID,
            "statement_id": str(uuid.uuid4()),
        },
        "statement_type": "ask_reviewed",
        "result": result,
        "review_scope": review_scope,
        "reviewer_type": reviewer_type,
        "policy_version": POLICY_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "evidence": {},
    }


def build_summary(statements: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "hub_id": HUB_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "statements": statements,
    }


def artifact_from_component_file(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {
        "kind": data.get("kind") or path.parent.parent.name.rstrip("s"),
        "name": data.get("name") or path.parent.name,
        "version": data.get("version") or "0.0.0",
    }


def write_statements_tree(root: Path, statements: list[dict]) -> None:
    for statement in statements:
        artifact = statement["artifact"]
        target = root / artifact["kind"] / artifact["name"] / f'{artifact["version"]}.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(statement, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Write Agency Hub assurance statement")
    parser.add_argument("--artifact-kind")
    parser.add_argument("--artifact-name")
    parser.add_argument("--artifact-version")
    parser.add_argument("--component-file", action="append", default=[])
    parser.add_argument("--result", required=True)
    parser.add_argument("--review-scope", default="package-change")
    parser.add_argument("--reviewer-type", default="automated")
    parser.add_argument("--output", default="-")
    parser.add_argument("--assurance-dir")
    args = parser.parse_args()

    artifacts = []
    for component_file in args.component_file:
        artifacts.append(artifact_from_component_file(Path(component_file)))
    if not artifacts:
        if not (args.artifact_kind and args.artifact_name and args.artifact_version):
            raise SystemExit("either --component-file or explicit artifact fields are required")
        artifacts.append(
            {
                "kind": args.artifact_kind,
                "name": args.artifact_name,
                "version": args.artifact_version,
            }
        )

    statements = [
        build_statement(
            artifact=artifact,
            result=args.result,
            review_scope=args.review_scope,
            reviewer_type=args.reviewer_type,
        )
        for artifact in artifacts
    ]

    if args.assurance_dir:
        write_statements_tree(Path(args.assurance_dir), statements)

    encoded = json.dumps(build_summary(statements), indent=2, sort_keys=True) + "\n"
    if args.output == "-":
        print(encoded, end="")
        return
    Path(args.output).write_text(encoded, encoding="utf-8")


if __name__ == "__main__":
    main()
