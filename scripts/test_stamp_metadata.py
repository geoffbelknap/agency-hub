#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stamp_metadata


class StampMetadataTest(unittest.TestCase):
    def test_preserves_existing_preset_kind_and_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            component_dir = root / "presets" / "community-administrator"
            component_dir.mkdir(parents=True)
            (component_dir / "preset.yaml").write_text(
                "name: community-administrator\ntype: coordinator\ndescription: test preset\n",
                encoding="utf-8",
            )
            (component_dir / "metadata.yaml").write_text(
                "name: community-administrator\n"
                "kind: preset\n"
                "version: 0.1.0\n"
                "build: local\n"
                "published_at: '2026-04-11T00:00:00Z'\n"
                "reviewed_by: codex\n",
                encoding="utf-8",
            )

            stamp_metadata.stamp_component(component_dir, "cebe952", "2026-04-12T21:49:17.988389+00:00")

            metadata = yaml.safe_load((component_dir / "metadata.yaml").read_text(encoding="utf-8"))

        self.assertEqual(metadata["name"], "community-administrator")
        self.assertEqual(metadata["kind"], "preset")
        self.assertEqual(metadata["version"], "0.1.0")
        self.assertEqual(metadata["build"], "cebe952")
        self.assertEqual(metadata["reviewed_by"], "codex")

    def test_infers_kind_for_new_preset_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            component_dir = root / "presets" / "fleet-manager"
            component_dir.mkdir(parents=True)
            (component_dir / "preset.yaml").write_text(
                "name: fleet-manager\ntype: coordinator\ndescription: test preset\n",
                encoding="utf-8",
            )

            stamp_metadata.stamp_component(component_dir, "cebe952", "2026-04-12T21:49:17.988389+00:00")

            metadata = yaml.safe_load((component_dir / "metadata.yaml").read_text(encoding="utf-8"))

        self.assertEqual(metadata["name"], "fleet-manager")
        self.assertEqual(metadata["kind"], "preset")
        self.assertEqual(metadata["version"], "0.0.0")
        self.assertEqual(metadata["build"], "cebe952")
        self.assertEqual(metadata["reviewed_by"], "bot")

    def test_connector_uses_source_kind_and_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            component_dir = root / "connectors" / "google-drive-admin"
            component_dir.mkdir(parents=True)
            (component_dir / "connector.yaml").write_text(
                "kind: connector\nname: google-drive-admin\nversion: '1.1.0'\nsource:\n  type: none\n",
                encoding="utf-8",
            )
            (component_dir / "metadata.yaml").write_text(
                "name: google-drive-admin\n"
                "kind: connector\n"
                "version: 1.0.0\n"
                "build: local\n"
                "published_at: '2026-04-11T00:00:00Z'\n"
                "reviewed_by: codex\n",
                encoding="utf-8",
            )

            stamp_metadata.stamp_component(component_dir, "cebe952", "2026-04-12T21:49:17.988389+00:00")

            metadata = yaml.safe_load((component_dir / "metadata.yaml").read_text(encoding="utf-8"))

        self.assertEqual(metadata["kind"], "connector")
        self.assertEqual(metadata["version"], "1.1.0")
        self.assertEqual(metadata["reviewed_by"], "codex")


if __name__ == "__main__":
    unittest.main()
