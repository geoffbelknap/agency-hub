#!/usr/bin/env python3
"""Stamp metadata.yaml for merged hub components.

Reads connector/pack/preset YAML files, extracts version and provenance,
writes metadata.yaml alongside each component. Run post-merge by CI.

Usage:
  python scripts/stamp_metadata.py --ref abc1234
"""

import argparse
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml


COMPONENT_DIRS = ["connectors", "packs", "presets", "ontology", "skills"]


def get_short_sha(ref: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", ref],
        capture_output=True, text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ref[:7]


def stamp_component(component_dir: Path, ref: str, now: str):
    """Read component YAML and write/update metadata.yaml."""
    # Find the main YAML file (connector.yaml, pack.yaml, preset.yaml, etc.)
    main_yaml = None
    for candidate in ["connector.yaml", "pack.yaml", "preset.yaml", "ontology.yaml", "skill.yaml"]:
        if (component_dir / candidate).exists():
            main_yaml = component_dir / candidate
            break

    if main_yaml is None:
        return

    with open(main_yaml) as f:
        data = yaml.safe_load(f)

    if not data or "name" not in data:
        return

    metadata_path = component_dir / "metadata.yaml"

    # Load existing metadata if present
    existing = {}
    if metadata_path.exists():
        with open(metadata_path) as f:
            existing = yaml.safe_load(f) or {}

    metadata = {
        "name": data["name"],
        "kind": data.get("kind", "unknown"),
        "version": data.get("version", "0.0.0"),
        "build": get_short_sha(ref),
        "published_at": now,
        "reviewed_by": existing.get("reviewed_by", "bot"),
    }

    with open(metadata_path, "w") as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

    print(f"  Stamped: {metadata_path} (v{metadata['version']} build {metadata['build']})")


def main():
    parser = argparse.ArgumentParser(description="Stamp metadata for hub components")
    parser.add_argument("--ref", default="HEAD", help="Git ref for build hash")
    args = parser.parse_args()

    now = datetime.now(timezone.utc).isoformat()

    for component_type in COMPONENT_DIRS:
        type_dir = Path(component_type)
        if not type_dir.exists():
            continue
        for component_dir in sorted(type_dir.iterdir()):
            if component_dir.is_dir():
                stamp_component(component_dir, args.ref, now)


if __name__ == "__main__":
    main()
