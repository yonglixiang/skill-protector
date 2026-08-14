#!/usr/bin/env python3
"""Integration tests for skill_crypto.py."""

from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "skill-protector" / "scripts" / "skill_crypto.py"


class SkillCryptoIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="skill-protector-test-"))
        self.skill = self.root / "example-skill"
        (self.skill / "references").mkdir(parents=True)
        (self.skill / "SKILL.md").write_text(
            "---\nname: example-skill\ndescription: Secret example.\n---\n\n# Secret text\n",
            encoding="utf-8",
        )
        (self.skill / "references" / "secret.txt").write_text("classified phrase\n", encoding="utf-8")
        self.key = self.root / "key"
        self.key.write_text("correct horse battery staple", encoding="utf-8")
        os.chmod(self.key, 0o600)
        self.wrong_key = self.root / "wrong-key"
        self.wrong_key.write_text("this is definitely the wrong key", encoding="utf-8")
        os.chmod(self.wrong_key, 0o600)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def run_cli(self, *args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(expected, result.returncode, result.stderr)
        return result

    def test_round_trip_authentication_and_cleanup(self) -> None:
        package = self.root / "protected.skill.enc"
        unlocked = self.root / "unlocked"
        self.run_cli(
            "protect", str(self.skill), "--output", str(package),
            "--passphrase-file", str(self.key), "--iterations", "100000",
        )
        encrypted = package.read_bytes()
        self.assertNotIn(b"classified phrase", encrypted)
        self.assertNotIn(b"Secret text", encrypted)
        self.run_cli("inspect", str(package))
        self.run_cli(
            "unlock", str(package), "--output", str(unlocked),
            "--passphrase-file", str(self.key),
        )
        restored = unlocked / "example-skill"
        self.assertEqual(
            "classified phrase\n",
            (restored / "references" / "secret.txt").read_text(encoding="utf-8"),
        )
        self.run_cli("cleanup", str(unlocked))
        self.assertFalse(unlocked.exists())

    def test_wrong_key_and_tamper_are_rejected(self) -> None:
        package = self.root / "protected.skill.enc"
        self.run_cli(
            "protect", str(self.skill), "--output", str(package),
            "--passphrase-file", str(self.key), "--iterations", "100000",
        )
        result = self.run_cli(
            "unlock", str(package), "--passphrase-file", str(self.wrong_key), expected=2,
        )
        self.assertIn("incorrect passphrase or damaged package", result.stderr)
        damaged = bytearray(package.read_bytes())
        damaged[len(damaged) // 2] ^= 1
        package.write_bytes(damaged)
        result = self.run_cli(
            "unlock", str(package), "--passphrase-file", str(self.key), expected=2,
        )
        self.assertIn("incorrect passphrase or damaged package", result.stderr)

    def test_cleanup_refuses_unmarked_directory(self) -> None:
        ordinary = self.root / "ordinary"
        ordinary.mkdir()
        self.run_cli("cleanup", str(ordinary), expected=2)
        self.assertTrue(ordinary.exists())

    def test_private_directory_with_one_key_file(self) -> None:
        key_directory = self.root / "keys"
        key_directory.mkdir(mode=0o700)
        directory_key = key_directory / "demo.key"
        directory_key.write_text("correct horse battery staple", encoding="utf-8")
        os.chmod(directory_key, 0o600)
        package = self.root / "directory-key.skill.enc"
        unlocked = self.root / "directory-key-unlocked"
        self.run_cli(
            "protect", str(self.skill), "--output", str(package),
            "--passphrase-file", str(key_directory), "--iterations", "100000",
        )
        self.run_cli(
            "unlock", str(package), "--output", str(unlocked),
            "--passphrase-file", str(key_directory),
        )
        self.assertTrue((unlocked / "example-skill" / "SKILL.md").is_file())
        self.run_cli("cleanup", str(unlocked))

    def test_installable_bundle_is_self_unlocking(self) -> None:
        protected_skill = self.root / "example-protected"
        unlocked = self.root / "bundle-unlocked"
        self.run_cli(
            "bundle", str(self.skill), "--output", str(protected_skill),
            "--passphrase-file", str(self.key), "--iterations", "100000",
        )
        expected = {
            "SKILL.md",
            "agents/openai.yaml",
            "payload.skill.enc",
            "scripts/skill_crypto.py",
        }
        actual = {
            str(path.relative_to(protected_skill))
            for path in protected_skill.rglob("*")
            if path.is_file()
        }
        self.assertEqual(expected, actual)
        loader_text = (protected_skill / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: example-protected", loader_text)
        self.assertIn("Do not invoke `$skill-protector`", loader_text)
        for path in protected_skill.rglob("*"):
            if path.is_file() and path.name != "payload.skill.enc":
                content = path.read_bytes()
                self.assertNotIn(b"Secret example", content)
                self.assertNotIn(b"classified phrase", content)
        bundled_cli = protected_skill / "scripts" / "skill_crypto.py"
        result = subprocess.run(
            [
                sys.executable, str(bundled_cli), "unlock",
                str(protected_skill / "payload.skill.enc"),
                "--output", str(unlocked),
                "--passphrase-file", str(self.key),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            "classified phrase\n",
            (unlocked / "example-skill" / "references" / "secret.txt").read_text(
                encoding="utf-8"
            ),
        )
        result = subprocess.run(
            [sys.executable, str(bundled_cli), "cleanup", str(unlocked)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse(unlocked.exists())


if __name__ == "__main__":
    unittest.main()
