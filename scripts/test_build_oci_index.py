#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_oci_index


class BuildOCIIndexTest(unittest.TestCase):
    def test_indexes_component_dirs_managed_routing_and_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "connectors" / "example").mkdir(parents=True)
            (root / "connectors" / "example" / "connector.yaml").write_text(
                'name: example\nversion: "1.2.3"\n',
                encoding="utf-8",
            )
            (root / "connectors" / "example" / "metadata.yaml").write_text(
                "reviewed_by: bot\n",
                encoding="utf-8",
            )
            (root / "skills" / "review").mkdir(parents=True)
            (root / "skills" / "review" / "SKILL.md").write_text(
                '---\nname: review\nversion: "2.0.0"\n---\n# Review\n',
                encoding="utf-8",
            )
            (root / "pricing").mkdir()
            (root / "pricing" / "routing.yaml").write_text(
                'version: "0.1"\nproviders: {}\n',
                encoding="utf-8",
            )

            components = build_oci_index.discover_components(root, "ghcr.io/acme/hub")

        by_kind = {component["kind"]: component for component in components}
        self.assertEqual(by_kind["connector"]["ref"], "ghcr.io/acme/hub/connector/example:1.2.3")
        self.assertEqual(by_kind["connector"]["metadata_path"], "connectors/example/metadata.yaml")
        self.assertEqual(by_kind["skill"]["path"], "skills/review/SKILL.md")
        self.assertEqual(by_kind["skill"]["media_type"], "application/vnd.agency.hub.skill.v1+markdown")
        self.assertEqual(by_kind["routing"]["path"], "pricing/routing.yaml")
        self.assertEqual(by_kind["routing"]["ref"], "ghcr.io/acme/hub/routing/routing:0.1")

    def test_publish_list_includes_media_type_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            publish_list = root / "oci-publish-list.tsv"
            build_oci_index.write_publish_list(
                publish_list,
                [
                    {
                        "kind": "skill",
                        "name": "review",
                        "version": "2.0.0",
                        "ref": "ghcr.io/acme/hub/skill/review:2.0.0",
                        "path": "skills/review/SKILL.md",
                        "media_type": "application/vnd.agency.hub.skill.v1+markdown",
                    }
                ],
            )

            row = publish_list.read_text(encoding="utf-8").strip().split("\t")

        self.assertEqual(len(row), 7)
        self.assertEqual(row[-1], "application/vnd.agency.hub.skill.v1+markdown")


if __name__ == "__main__":
    unittest.main()
