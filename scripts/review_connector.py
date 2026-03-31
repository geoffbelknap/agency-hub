#!/usr/bin/env python3
"""Hub review bot — validates connector PRs and decides auto-approve vs flag.

Reads changed connector YAML files from a PR diff, validates schema,
and checks whether changes expand the security surface.

Exit codes:
  0 — auto-approve (routine changes only)
  1 — validation failure (block PR)
  2 — needs human review (security surface changed)

Usage:
  python scripts/review_connector.py --base main --head feature-branch
  python scripts/review_connector.py --files connectors/limacharlie/connector.yaml
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import yaml


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

REQUIRED_TOP_LEVEL = {"kind", "name", "version", "source"}
VALID_SOURCE_TYPES = {"webhook", "poll", "schedule", "channel-watch"}
VALID_PRIORITIES = {"high", "normal", "low"}
SECURITY_SURFACE_FIELDS = {"requires", "mcp"}

REQUIRED_PRESET_FIELDS = {"name", "description", "type"}
REQUIRED_PACK_FIELDS = {"name", "description"}

SUSPICIOUS_IDENTITY_PATTERNS = [
    r"ignore\s+previous",
    r"you\s+are\s+now",
    r"disregard\s+(all\s+)?prior",
    r"forget\s+(all\s+)?previous",
    r"new\s+instructions?\s*:",
]


# ---------------------------------------------------------------------------
# Semver helpers
# ---------------------------------------------------------------------------

def parse_version(v: str) -> tuple:
    """Parse semver string into comparable tuple. Returns (0, 0, 0) on failure."""
    try:
        return tuple(int(x) for x in str(v).split("."))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def validate_connector(data: dict, path: str) -> list[str]:
    """Validate a connector YAML against the schema. Returns list of errors."""
    errors = []

    # Required fields
    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"{path}: missing required field '{field}'")

    if data.get("kind") != "connector":
        errors.append(f"{path}: kind must be 'connector', got '{data.get('kind')}'")

    # Version
    version = data.get("version", "")
    if not version:
        errors.append(f"{path}: version is required")

    # Source
    source = data.get("source", {})
    if source.get("type") not in VALID_SOURCE_TYPES:
        errors.append(f"{path}: source.type must be one of {VALID_SOURCE_TYPES}")

    if source.get("type") == "poll":
        if not source.get("url"):
            errors.append(f"{path}: poll source requires 'url'")
        if not source.get("interval") and not source.get("cron"):
            errors.append(f"{path}: poll source requires 'interval' or 'cron'")

    # Routes
    for i, route in enumerate(data.get("routes", [])):
        if "match" not in route:
            errors.append(f"{path}: routes[{i}] missing 'match'")
        if "target" not in route and "relay" not in route:
            errors.append(f"{path}: routes[{i}] needs 'target' or 'relay'")
        if route.get("priority") and route["priority"] not in VALID_PRIORITIES:
            errors.append(f"{path}: routes[{i}].priority must be one of {VALID_PRIORITIES}")

    # Graph ingest
    for i, rule in enumerate(data.get("graph_ingest", [])):
        for j, node in enumerate(rule.get("nodes", [])):
            if "kind" not in node:
                errors.append(f"{path}: graph_ingest[{i}].nodes[{j}] missing 'kind'")
            if "label" not in node:
                errors.append(f"{path}: graph_ingest[{i}].nodes[{j}] missing 'label'")

    # MCP tools
    mcp = data.get("mcp")
    if mcp:
        if "name" not in mcp:
            errors.append(f"{path}: mcp missing 'name'")
        for i, tool in enumerate(mcp.get("tools", [])):
            if "name" not in tool:
                errors.append(f"{path}: mcp.tools[{i}] missing 'name'")

    # Template safety — check for dunder access attempts
    _check_templates_recursive(data, path, errors)

    return errors


def _check_templates_recursive(obj, path: str, errors: list[str]):
    """Recursively scan for dangerous template patterns."""
    if isinstance(obj, str):
        if "__" in obj and "{{" in obj:
            errors.append(f"{path}: template contains dunder access pattern: {obj[:80]}")
        if "{%" in obj:
            errors.append(f"{path}: template contains control flow ({{% %}}) which is not allowed: {obj[:80]}")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            _check_templates_recursive(v, f"{path}.{k}", errors)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _check_templates_recursive(v, f"{path}[{i}]", errors)


# ---------------------------------------------------------------------------
# Preset validation
# ---------------------------------------------------------------------------

def validate_preset(data: dict, path: str) -> tuple:
    """Validate a preset YAML. Returns (errors, security_flags).

    security_flags are issues that require human review (exit 2) rather than
    hard validation failures (exit 1).
    """
    errors = []
    security_flags = []

    # Required fields
    for field in REQUIRED_PRESET_FIELDS:
        if field not in data:
            errors.append(f"{path}: missing required field '{field}'")

    # Template safety
    _check_templates_recursive(data, path, errors)

    # hard_limits is a security surface — changes need human review
    if "hard_limits" in data:
        security_flags.append(
            f"{path}: preset defines 'hard_limits' (agent security constraints) — "
            "requires human review"
        )

    # Suspicious patterns in identity.body (XPIA / prompt-injection defence)
    identity_body = data.get("identity", {}).get("body", "")
    if identity_body:
        for pattern in SUSPICIOUS_IDENTITY_PATTERNS:
            if re.search(pattern, identity_body, re.IGNORECASE):
                security_flags.append(
                    f"{path}: identity.body contains suspicious pattern "
                    f"'{pattern}' — possible prompt injection attempt"
                )

    return errors, security_flags


# ---------------------------------------------------------------------------
# Pack validation
# ---------------------------------------------------------------------------

def validate_pack(data: dict, path: str, known_connector_names: set) -> tuple:
    """Validate a pack YAML. Returns (errors, warnings).

    warnings are non-fatal issues printed but do not block or flag the PR.
    """
    errors = []
    warnings = []

    # Required fields
    for field in REQUIRED_PACK_FIELDS:
        if field not in data:
            errors.append(f"{path}: missing required field '{field}'")

    # Template safety
    _check_templates_recursive(data, path, errors)

    # Check that referenced connectors exist in the hub
    for ref in data.get("connectors", []):
        connector_name = ref if isinstance(ref, str) else ref.get("name", "")
        if connector_name and connector_name not in known_connector_names:
            warnings.append(
                f"{path}: references connector '{connector_name}' "
                "which is not present in the hub"
            )

    return errors, warnings


# ---------------------------------------------------------------------------
# Security surface diff
# ---------------------------------------------------------------------------

def diff_security_surface(old: Optional[dict], new: dict, path: str) -> list[str]:
    """Compare old and new connector for security surface changes.
    Returns list of change descriptions that need human review.
    """
    flags = []

    if old is None:
        # New connector — always flag for human review
        flags.append(f"{path}: new connector submission — requires human review")
        return flags

    # Credential changes
    old_creds = _extract_credential_names(old)
    new_creds = _extract_credential_names(new)
    added_creds = new_creds - old_creds
    if added_creds:
        flags.append(f"{path}: new credentials required: {added_creds}")

    # Egress domain changes
    old_domains, _ = _extract_domains(old)
    new_domains, new_dynamic_urls = _extract_domains(new)
    added_domains = new_domains - old_domains
    if added_domains:
        flags.append(f"{path}: new egress domains: {added_domains}")
    if new_dynamic_urls:
        flags.append(
            f"{path}: egress destination is operator-controlled (dynamic host) — "
            f"requires human review: {new_dynamic_urls}"
        )

    # MCP tool changes
    old_tools = _extract_tool_names(old)
    new_tools = _extract_tool_names(new)
    added_tools = new_tools - old_tools
    removed_tools = old_tools - new_tools
    if added_tools:
        flags.append(f"{path}: new MCP tools added: {added_tools}")
    if removed_tools:
        flags.append(f"{path}: MCP tools removed: {removed_tools}")

    # MCP tool definition changes (same name, different definition)
    old_tool_defs = _extract_tool_defs(old)
    new_tool_defs = _extract_tool_defs(new)
    for name in old_tools & new_tools:
        if old_tool_defs.get(name) != new_tool_defs.get(name):
            flags.append(f"{path}: MCP tool '{name}' definition changed")

    # Version — must be bumped
    old_ver = old.get("version", "0.0.0")
    new_ver = new.get("version", "0.0.0")
    if parse_version(new_ver) <= parse_version(old_ver):
        flags.append(f"{path}: version not bumped ({old_ver} -> {new_ver})")

    return flags


def _extract_credential_names(data: dict) -> set[str]:
    creds = set()
    for c in data.get("requires", {}).get("credentials", []):
        creds.add(c.get("name", ""))
    for c in data.get("requires", {}).get("services", []):
        creds.add(c if isinstance(c, str) else c.get("name", ""))
    return creds - {""}


def _extract_domains(data: dict) -> tuple:
    """Return (domains: set[str], dynamic_host_urls: list[str]).

    Domains is the set of resolved hostnames.  dynamic_host_urls collects any
    URLs whose host portion contained ${VAR} placeholders — these need human
    review because the egress destination is operator-controlled at runtime.
    """
    domains = set()
    dynamic_host_urls = []
    url = data.get("source", {}).get("url", "")
    if url:
        domain, has_dynamic = _domain_from_url(url)
        if domain:
            domains.add(domain)
        if has_dynamic:
            dynamic_host_urls.append(url)
    mcp = data.get("mcp", {})
    if mcp.get("api_base"):
        domain, has_dynamic = _domain_from_url(mcp["api_base"])
        if domain:
            domains.add(domain)
        if has_dynamic:
            dynamic_host_urls.append(mcp["api_base"])
    return domains, dynamic_host_urls


def _domain_from_url(url: str) -> tuple:
    """Extract domain from URL. Returns (domain, has_dynamic_host).

    If the host portion contains ${VAR} placeholders the raw template is
    returned as the domain and has_dynamic_host is True so callers can flag
    the egress destination as operator-controlled and requiring human review.
    """
    host_part = url.split("://", 1)[1] if "://" in url else url
    host_part = host_part.split("/")[0]
    has_dynamic = bool(re.search(r"\$\{[^}]+\}", host_part))
    cleaned = url.replace("${", "").replace("}", "")
    if "://" in cleaned:
        cleaned = cleaned.split("://", 1)[1]
    domain = cleaned.split("/")[0].split(":")[0]
    return domain, has_dynamic


def _extract_tool_names(data: dict) -> set[str]:
    mcp = data.get("mcp", {})
    return {t.get("name", "") for t in mcp.get("tools", [])} - {""}


def _extract_tool_defs(data: dict) -> dict:
    mcp = data.get("mcp", {})
    return {t["name"]: t for t in mcp.get("tools", []) if "name" in t}


# ---------------------------------------------------------------------------
# Git diff helpers
# ---------------------------------------------------------------------------

def get_changed_component_files(base: str, head: str) -> list[str]:
    """Get list of changed connector, preset, and pack YAML files between base and head."""
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        capture_output=True, text=True,
    )
    files = result.stdout.strip().split("\n")
    changed = []
    for f in files:
        if not f.endswith(".yaml"):
            continue
        if f.startswith("connectors/"):
            changed.append(f)
        elif f.startswith("presets/") and f.endswith("/preset.yaml"):
            changed.append(f)
        elif f.startswith("packs/") and f.endswith("/pack.yaml"):
            changed.append(f)
    return changed


def _discover_known_connectors(repo_root: str = ".") -> set:
    """Return connector names (directory names) present in the hub."""
    connectors_dir = Path(repo_root) / "connectors"
    if not connectors_dir.is_dir():
        return set()
    return {p.name for p in connectors_dir.iterdir() if p.is_dir()}


def load_file_at_ref(ref: str, path: str) -> Optional[dict]:
    """Load a YAML file at a specific git ref. Returns None if file doesn't exist."""
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    return yaml.safe_load(result.stdout)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Hub connector review bot")
    parser.add_argument("--base", default="main", help="Base branch/ref")
    parser.add_argument("--head", default="HEAD", help="Head branch/ref")
    parser.add_argument("--files", nargs="*", help="Specific files to validate (skip git diff)")
    args = parser.parse_args()

    if args.files:
        changed_files = args.files
    else:
        changed_files = get_changed_component_files(args.base, args.head)

    if not changed_files:
        print("No connector/preset/pack files changed.")
        sys.exit(0)

    known_connectors = _discover_known_connectors()

    all_errors = []
    all_flags = []
    all_warnings = []

    for filepath in changed_files:
        print(f"\nReviewing: {filepath}")

        # Load new version
        if args.files:
            with open(filepath) as f:
                new_data = yaml.safe_load(f)
        else:
            new_data = load_file_at_ref(args.head, filepath)

        if new_data is None:
            print(f"  SKIP: file removed or unreadable")
            continue

        # Route to the appropriate validator
        if filepath.startswith("presets/"):
            errors, sec_flags = validate_preset(new_data, filepath)
            if errors:
                for e in errors:
                    print(f"  ERROR: {e}")
                all_errors.extend(errors)
            else:
                print(f"  Schema: PASS")
            if sec_flags:
                for sf in sec_flags:
                    print(f"  FLAG: {sf}")
                all_flags.extend(sec_flags)
            elif not errors:
                print(f"  Security surface: unchanged")
            continue

        if filepath.startswith("packs/"):
            errors, warnings = validate_pack(new_data, filepath, known_connectors)
            if errors:
                for e in errors:
                    print(f"  ERROR: {e}")
                all_errors.extend(errors)
            else:
                print(f"  Schema: PASS")
            if warnings:
                for w in warnings:
                    print(f"  WARN: {w}")
                all_warnings.extend(warnings)
            elif not errors:
                print(f"  Pack references: OK")
            continue

        # --- connector ---
        # Schema validation
        errors = validate_connector(new_data, filepath)
        if errors:
            for e in errors:
                print(f"  ERROR: {e}")
            all_errors.extend(errors)
            continue

        print(f"  Schema: PASS")

        # Security surface diff
        if not args.files:
            old_data = load_file_at_ref(args.base, filepath)
        else:
            old_data = None  # No baseline for direct file validation

        flags = diff_security_surface(old_data, new_data, filepath)
        if flags:
            for f in flags:
                print(f"  FLAG: {f}")
            all_flags.extend(flags)
        else:
            print(f"  Security surface: unchanged")

    # Summary
    print("\n" + "=" * 60)
    if all_warnings:
        print(f"WARNINGS: {len(all_warnings)} non-fatal issue(s)")
        for w in all_warnings:
            print(f"  - {w}")
    if all_errors:
        print(f"BLOCKED: {len(all_errors)} validation error(s)")
        for e in all_errors:
            print(f"  - {e}")
        sys.exit(1)
    elif all_flags:
        print(f"NEEDS HUMAN REVIEW: {len(all_flags)} security surface change(s)")
        for f in all_flags:
            print(f"  - {f}")
        # Output for GitHub Actions
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
                fh.write("needs_review=true\n")
                fh.write(f"review_summary={json.dumps(all_flags)}\n")
        sys.exit(2)
    else:
        print("AUTO-APPROVE: all changes are routine")
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
                fh.write("needs_review=false\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
