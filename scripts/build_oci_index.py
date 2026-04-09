#!/usr/bin/env python3
"""Build the Agency Hub OCI catalog index.

The publish workflow intentionally avoids a PyYAML dependency, so this script
only reads top-level scalar fields needed for catalog discovery.
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import re


DEFAULT_COMPONENT_MEDIA_TYPE = "application/vnd.agency.hub.component.v1+yaml"

COMPONENT_DIRS = {
    "connectors": ("connector", "connector.yaml", DEFAULT_COMPONENT_MEDIA_TYPE),
    "packs": ("pack", "pack.yaml", DEFAULT_COMPONENT_MEDIA_TYPE),
    "presets": ("preset", "preset.yaml", DEFAULT_COMPONENT_MEDIA_TYPE),
    "missions": ("mission", "mission.yaml", DEFAULT_COMPONENT_MEDIA_TYPE),
    "services": ("service", "service.yaml", DEFAULT_COMPONENT_MEDIA_TYPE),
    "providers": ("provider", "provider.yaml", DEFAULT_COMPONENT_MEDIA_TYPE),
    "setup": ("setup", "setup.yaml", DEFAULT_COMPONENT_MEDIA_TYPE),
    "skills": ("skill", "SKILL.md", "application/vnd.agency.hub.skill.v1+markdown"),
    "policies": ("policy", "policy.yaml", DEFAULT_COMPONENT_MEDIA_TYPE),
    "workspaces": ("workspace", "workspace.yaml", DEFAULT_COMPONENT_MEDIA_TYPE),
}

SCALAR_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*?)\s*$")


def quote_yaml(value: object) -> str:
    text = str(value)
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def read_top_level_scalars(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line[0].isspace() or line.lstrip().startswith("#"):
            continue
        match = SCALAR_RE.match(line)
        if not match:
            continue
        key, raw = match.groups()
        raw = raw.strip()
        if not raw or raw in {"|", ">"}:
            continue
        if raw.startswith(("'", '"')) and raw.endswith(("'", '"')) and len(raw) >= 2:
            raw = raw[1:-1]
        values[key] = raw
    return values


def component_name(kind: str, directory_name: str, values: dict[str, str]) -> str:
    for key in ("name", kind):
        value = values.get(key)
        if value:
            return value
    return directory_name


def component_version(values: dict[str, str]) -> str:
    return values.get("version") or "0.0.0"


def discover_components(root: Path, registry: str) -> list[dict[str, str]]:
    components: list[dict[str, str]] = []

    for plural, (kind, filename, media_type) in COMPONENT_DIRS.items():
        kind_root = root / plural
        if not kind_root.is_dir():
            continue
        for component_dir in sorted(p for p in kind_root.iterdir() if p.is_dir()):
            component_file = component_dir / filename
            if not component_file.exists():
                continue
            values = read_top_level_scalars(component_file)
            name = component_name(kind, component_dir.name, values)
            version = component_version(values)
            metadata_file = component_dir / "metadata.yaml"
            entry = {
                "kind": kind,
                "name": name,
                "version": version,
                "ref": f"{registry}/{kind}/{name}:{version}",
                "path": component_file.relative_to(root).as_posix(),
                "media_type": media_type,
            }
            if metadata_file.exists():
                entry["metadata_path"] = metadata_file.relative_to(root).as_posix()
            components.append(entry)

    routing_file = root / "pricing" / "routing.yaml"
    if routing_file.exists():
        values = read_top_level_scalars(routing_file)
        name = component_name("routing", "routing", values)
        version = component_version(values)
        components.append(
            {
                "kind": "routing",
                "name": name,
                "version": version,
                "ref": f"{registry}/routing/{name}:{version}",
                "path": routing_file.relative_to(root).as_posix(),
                "media_type": DEFAULT_COMPONENT_MEDIA_TYPE,
            }
        )

    ontology_root = root / "ontology"
    if ontology_root.is_dir():
        for component_file in sorted(ontology_root.glob("*.yaml")):
            values = read_top_level_scalars(component_file)
            name = component_name("ontology", component_file.stem, values)
            version = component_version(values)
            components.append(
                {
                    "kind": "ontology",
                    "name": name,
                    "version": version,
                    "ref": f"{registry}/ontology/{name}:{version}",
                    "path": component_file.relative_to(root).as_posix(),
                    "media_type": DEFAULT_COMPONENT_MEDIA_TYPE,
                }
            )

    return sorted(components, key=lambda c: (c["kind"], c["name"]))


def write_index(path: Path, registry: str, components: list[dict[str, str]]) -> None:
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    lines = [
        "schema_version: 1",
        f"generated_at: {quote_yaml(generated_at)}",
        f"registry: {quote_yaml(registry)}",
        "components:",
    ]
    for component in components:
        lines.extend(
            [
                f"  - kind: {quote_yaml(component['kind'])}",
                f"    name: {quote_yaml(component['name'])}",
                f"    version: {quote_yaml(component['version'])}",
                f"    ref: {quote_yaml(component['ref'])}",
                f"    path: {quote_yaml(component['path'])}",
                f"    media_type: {quote_yaml(component['media_type'])}",
            ]
        )
        if "metadata_path" in component:
            lines.append(f"    metadata_path: {quote_yaml(component['metadata_path'])}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_publish_list(path: Path, components: list[dict[str, str]]) -> None:
    rows = []
    for component in components:
        rows.append(
            "\t".join(
                [
                    component["kind"],
                    component["name"],
                    component["version"],
                    component["ref"],
                    component["path"],
                    component.get("metadata_path", ""),
                    component["media_type"],
                ]
            )
        )
    path.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True)
    parser.add_argument("--index", default="oci-index.yaml")
    parser.add_argument("--publish-list", default="oci-publish-list.tsv")
    args = parser.parse_args()

    root = Path.cwd()
    components = discover_components(root, args.registry.rstrip("/"))
    write_index(root / args.index, args.registry.rstrip("/"), components)
    write_publish_list(root / args.publish_list, components)
    print(f"indexed {len(components)} components")


if __name__ == "__main__":
    main()
