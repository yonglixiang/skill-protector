#!/usr/bin/env python3
"""Encrypt and temporarily unlock complete Codex skill folders."""

from __future__ import annotations

import argparse
import getpass
import hashlib
import hmac
import io
import re
import os
from pathlib import Path, PurePosixPath
import secrets
import shutil
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile


MAGIC = b"SKPROT1\0"
TAG_SIZE = 32
SALT_SIZE = 16
DEFAULT_ITERATIONS = 600_000
MIN_ITERATIONS = 100_000
MARKER = ".skill-protector-unlocked"
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ProtectorError(Exception):
    """A safe, user-facing failure."""


def _openssl() -> str:
    executable = shutil.which("openssl")
    if not executable:
        raise ProtectorError("OpenSSL is required but was not found on PATH")
    return executable


def _read_passphrase(path: Path | None, *, confirm: bool) -> bytes:
    if path is not None:
        expanded = path.expanduser()
        if expanded.is_symlink():
            raise ProtectorError("passphrase path must not be a symlink")
        resolved = expanded.resolve()
        try:
            info = resolved.stat()
        except OSError as exc:
            raise ProtectorError(f"cannot read passphrase path: {exc}") from exc
        if stat.S_ISDIR(info.st_mode):
            if os.name == "posix" and stat.S_IMODE(info.st_mode) & 0o077:
                raise ProtectorError("passphrase directory permissions must be 0700 or stricter")
            candidates = [
                item for item in resolved.iterdir()
                if item.is_file() and not item.is_symlink() and not item.name.startswith(".")
            ]
            if len(candidates) != 1:
                raise ProtectorError(
                    "passphrase directory must contain exactly one non-hidden regular file"
                )
            resolved = candidates[0]
            info = resolved.stat()
        if not stat.S_ISREG(info.st_mode):
            raise ProtectorError("passphrase path must resolve to a regular file")
        if os.name == "posix" and stat.S_IMODE(info.st_mode) & 0o077:
            raise ProtectorError("passphrase file permissions must be 0600 or stricter")
        data = resolved.read_bytes()
        if data.endswith(b"\r\n"):
            data = data[:-2]
        elif data.endswith(b"\n"):
            data = data[:-1]
    else:
        first = getpass.getpass("Passphrase: ").encode("utf-8")
        if confirm:
            second = getpass.getpass("Confirm passphrase: ").encode("utf-8")
            if not hmac.compare_digest(first, second):
                raise ProtectorError("passphrases do not match")
        data = first
    if b"\n" in data or b"\r" in data or b"\0" in data:
        raise ProtectorError("passphrase must not contain newline or NUL bytes")
    if len(data) < 12:
        raise ProtectorError("passphrase must contain at least 12 bytes")
    return data


def _resolve_skill(source: str) -> Path:
    candidate = Path(source).expanduser()
    if candidate.exists():
        if candidate.is_symlink():
            raise ProtectorError("source skill directory must not be a symlink")
        matches = [candidate]
    else:
        roots: list[Path] = []
        codex_home = os.environ.get("CODEX_HOME")
        if codex_home:
            roots.append(Path(codex_home).expanduser() / "skills")
        default = Path.home() / ".codex" / "skills"
        if default not in roots:
            roots.append(default)
        matches = [root / source for root in roots if (root / source).is_dir() and not (root / source).is_symlink()]
    if not matches:
        raise ProtectorError(f"skill not found: {source}")
    if len(matches) > 1:
        rendered = "\n".join(f"  {item}" for item in matches)
        raise ProtectorError(f"multiple installed skills match; use an explicit path:\n{rendered}")
    skill = matches[0].resolve()
    if not skill.is_dir() or not (skill / "SKILL.md").is_file():
        raise ProtectorError("source must be a skill directory containing a regular SKILL.md")
    for root, dirs, files in os.walk(skill, followlinks=False):
        for name in dirs + files:
            if (Path(root) / name).is_symlink():
                raise ProtectorError(f"source contains a forbidden symlink: {Path(root) / name}")
    return skill


def _archive_skill(skill: Path) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz", format=tarfile.PAX_FORMAT) as archive:
        archive.add(skill, arcname=skill.name, recursive=True)
    return buffer.getvalue()


def _openssl_crypt(data: bytes, passphrase: bytes, *, decrypt: bool, iterations: int) -> bytes:
    command = [
        _openssl(), "enc", "-aes-256-cbc", "-pbkdf2", "-md", "sha256",
        "-iter", str(iterations), "-pass", "stdin",
    ]
    command.append("-d" if decrypt else "-salt")
    process = subprocess.run(
        command,
        input=passphrase + b"\n" + data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode:
        raise ProtectorError("decryption failed" if decrypt else "encryption failed")
    return process.stdout


def _derive_mac_key(passphrase: bytes, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", passphrase, b"skill-protector-mac\0" + salt, iterations, 32)


def _encrypted_payload(skill: Path, passphrase: bytes, iterations: int) -> bytes:
    if iterations < MIN_ITERATIONS:
        raise ProtectorError(f"iterations must be at least {MIN_ITERATIONS}")
    plaintext = _archive_skill(skill)
    ciphertext = _openssl_crypt(plaintext, passphrase, decrypt=False, iterations=iterations)
    mac_salt = secrets.token_bytes(SALT_SIZE)
    header = MAGIC + struct.pack(">I", iterations) + mac_salt
    tag = hmac.new(
        _derive_mac_key(passphrase, mac_salt, iterations),
        header + ciphertext,
        hashlib.sha256,
    ).digest()
    return header + ciphertext + tag


def _write_private_file(path: Path, data: bytes, mode: int = 0o600) -> None:
    with path.open("xb") as handle:
        os.chmod(path, mode)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def protect(source: str, output: Path, passphrase_file: Path | None, iterations: int) -> None:
    skill = _resolve_skill(source)
    target = output.expanduser().resolve()
    if target.exists():
        raise ProtectorError(f"refusing to overwrite existing output: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    passphrase = _read_passphrase(passphrase_file, confirm=True)
    payload = _encrypted_payload(skill, passphrase, iterations)
    temporary = target.with_name(f".{target.name}.{secrets.token_hex(6)}.tmp")
    try:
        _write_private_file(temporary, payload)
        temporary.replace(target)
    finally:
        if temporary.exists():
            temporary.unlink()
    print(f"Protected package: {target}")
    print(f"Source unchanged: {skill}")


def _protected_loader_skill(name: str) -> str:
    return f'''---
name: {name}
description: Authorized loader for an encrypted Codex Skill payload. Use when the user explicitly invokes ${name}, attaches this protected Skill, or asks to use the protected Skill represented by this installed wrapper.
---

# Protected Skill Loader

Load the encrypted Skill contained in this wrapper. Do not invoke `$skill-protector`; this wrapper is self-contained.

## Authorization

- Require a passphrase of at least 12 UTF-8 bytes with no newline, carriage-return, or NUL bytes. Recommend 16+ characters or at least five random words because there is no recovery mechanism.
- Accept a passphrase already supplied in the conversation, a newly supplied conversational passphrase, a regular non-symlink mode-`0600` key file, or a non-symlink mode-`0700` directory containing exactly one non-hidden regular non-symlink key file. Require the contained file to use mode `0600` or stricter.
- If no credential or credential path is available, ask the user for one.
- Warn once before the user posts a new conversational passphrase because it remains in chat history. Do not ask them to resend a passphrase already supplied.
- Never place a passphrase in a command, argument, environment variable, source file, durable temporary file, or output.

## Unlock and execute

1. Resolve `PROTECTED_SKILL_DIR` as the directory containing this `SKILL.md`.
2. For a key file or directory, run:

   ```bash
   python3 "$PROTECTED_SKILL_DIR/scripts/skill_crypto.py" unlock \
     "$PROTECTED_SKILL_DIR/payload.skill.enc" \
     --passphrase-file /absolute/path/to/key-or-directory
   ```

   For a conversational passphrase, omit `--passphrase-file`, run in an interactive PTY, wait for the hidden prompt, and send the passphrase only through standard input.
3. Read the returned decrypted `SKILL.md` completely. Follow it for the user's request and resolve its resources from the returned decrypted Skill directory.
4. Keep these authorization and cleanup rules controlling while applying the decrypted Skill.
5. In a `finally`-style step, clean the exact returned cleanup root:

   ```bash
   python3 "$PROTECTED_SKILL_DIR/scripts/skill_crypto.py" cleanup TEMP_DIRECTORY
   ```

6. Confirm cleanup. If cleanup fails or execution is interrupted, report the exact marked temporary directory.
'''


def _protected_openai_yaml(name: str) -> str:
    display_name = " ".join(part.capitalize() for part in name.split("-"))
    return f'''interface:
  display_name: "{display_name}"
  short_description: "Unlock and use this protected Skill"
  default_prompt: "Use ${name} with my authorized key file."
policy:
  allow_implicit_invocation: false
'''


def bundle(source: str, output: Path, passphrase_file: Path | None, iterations: int) -> None:
    skill = _resolve_skill(source)
    target = output.expanduser().resolve()
    name = target.name
    if len(name) > 63 or not SKILL_NAME_PATTERN.fullmatch(name):
        raise ProtectorError(
            "output directory name must be a lowercase hyphen-case Skill name under 64 characters"
        )
    if target.exists():
        raise ProtectorError(f"refusing to overwrite existing output: {target}")
    try:
        target.relative_to(skill)
    except ValueError:
        pass
    else:
        raise ProtectorError("installable protected Skill must be created outside the source Skill")
    target.parent.mkdir(parents=True, exist_ok=True)
    passphrase = _read_passphrase(passphrase_file, confirm=True)
    payload = _encrypted_payload(skill, passphrase, iterations)
    temporary = target.with_name(f".{target.name}.{secrets.token_hex(6)}.tmp")
    try:
        temporary.mkdir(mode=0o700)
        (temporary / "agents").mkdir(mode=0o700)
        (temporary / "scripts").mkdir(mode=0o700)
        _write_private_file(temporary / "payload.skill.enc", payload)
        _write_private_file(
            temporary / "SKILL.md",
            _protected_loader_skill(name).encode("utf-8"),
        )
        _write_private_file(
            temporary / "agents" / "openai.yaml",
            _protected_openai_yaml(name).encode("utf-8"),
        )
        _write_private_file(
            temporary / "scripts" / "skill_crypto.py",
            Path(__file__).resolve().read_bytes(),
            mode=0o700,
        )
        temporary.replace(target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)
    print(f"Installable protected Skill: {target}")
    print(f"Invoke as: ${name}")
    print(f"Source unchanged: {skill}")


def _parse_package(package: Path) -> tuple[int, bytes, bytes, bytes]:
    try:
        payload = package.expanduser().resolve().read_bytes()
    except OSError as exc:
        raise ProtectorError(f"cannot read package: {exc}") from exc
    header_size = len(MAGIC) + 4 + SALT_SIZE
    if len(payload) < header_size + TAG_SIZE or payload[: len(MAGIC)] != MAGIC:
        raise ProtectorError("not a supported skill-protector package")
    iterations = struct.unpack(">I", payload[len(MAGIC) : len(MAGIC) + 4])[0]
    if iterations < MIN_ITERATIONS or iterations > 10_000_000:
        raise ProtectorError("package has an invalid iteration count")
    mac_salt = payload[len(MAGIC) + 4 : header_size]
    return iterations, mac_salt, payload[header_size:-TAG_SIZE], payload[-TAG_SIZE:]


def _safe_extract(archive_bytes: bytes, destination: Path) -> Path:
    try:
        archive = tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz")
    except tarfile.TarError as exc:
        raise ProtectorError("decrypted payload is not a valid skill archive") from exc
    with archive:
        members = archive.getmembers()
        roots: set[str] = set()
        for member in members:
            pure = PurePosixPath(member.name)
            if pure.is_absolute() or not pure.parts or ".." in pure.parts:
                raise ProtectorError("archive contains an unsafe path")
            if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                raise ProtectorError("archive contains a forbidden special entry")
            if not (member.isdir() or member.isfile()):
                raise ProtectorError("archive contains an unsupported entry")
            roots.add(pure.parts[0])
        if len(roots) != 1:
            raise ProtectorError("archive must contain exactly one top-level skill directory")
        for member in members:
            path = destination.joinpath(*PurePosixPath(member.name).parts)
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
                os.chmod(path, stat.S_IMODE(member.mode) & 0o700 or 0o700)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise ProtectorError("archive file could not be read")
                with path.open("xb") as target:
                    shutil.copyfileobj(source, target)
                os.chmod(path, stat.S_IMODE(member.mode) & 0o700 or 0o600)
    skill = destination / next(iter(roots))
    if not (skill / "SKILL.md").is_file():
        raise ProtectorError("unlocked archive does not contain SKILL.md")
    return skill


def unlock(package: Path, output: Path | None, passphrase_file: Path | None) -> None:
    iterations, mac_salt, ciphertext, expected_tag = _parse_package(package)
    passphrase = _read_passphrase(passphrase_file, confirm=False)
    header = MAGIC + struct.pack(">I", iterations) + mac_salt
    actual_tag = hmac.new(_derive_mac_key(passphrase, mac_salt, iterations), header + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(actual_tag, expected_tag):
        raise ProtectorError("incorrect passphrase or damaged package")
    plaintext = _openssl_crypt(ciphertext, passphrase, decrypt=True, iterations=iterations)
    if output is None:
        destination = Path(tempfile.mkdtemp(prefix="skill-protector-"))
    else:
        destination = output.expanduser().resolve()
        if destination.exists():
            raise ProtectorError(f"refusing to use existing output directory: {destination}")
        destination.mkdir(parents=True, mode=0o700)
    os.chmod(destination, 0o700)
    marker = destination / MARKER
    marker.write_text("Temporary plaintext created by skill-protector.\n", encoding="utf-8")
    os.chmod(marker, 0o600)
    try:
        skill = _safe_extract(plaintext, destination)
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    print(f"Unlocked skill: {skill}")
    print(f"Cleanup root: {destination}")


def cleanup(directory: Path) -> None:
    target = directory.expanduser().resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if target == temp_root or target == Path(target.anchor):
        raise ProtectorError("refusing to clean a broad directory")
    if not (target / MARKER).is_file():
        raise ProtectorError(f"refusing to remove unmarked directory: {target}")
    shutil.rmtree(target)
    print(f"Removed temporary plaintext: {target}")


def inspect(package: Path) -> None:
    iterations, _, ciphertext, _ = _parse_package(package)
    print("Format: skill-protector v1")
    print("Cipher: AES-256-CBC")
    print("Authentication: HMAC-SHA-256")
    print("KDF: PBKDF2-HMAC-SHA-256")
    print(f"Iterations: {iterations}")
    print(f"Ciphertext bytes: {len(ciphertext)}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    bundle_parser = commands.add_parser(
        "bundle", help="create an installable, self-unlocking protected Skill"
    )
    bundle_parser.add_argument("source", help="skill directory path or installed skill name")
    bundle_parser.add_argument(
        "--output", type=Path, required=True,
        help="new directory; its lowercase hyphen-case basename becomes the Skill name",
    )
    bundle_parser.add_argument(
        "--passphrase-file", type=Path,
        help="0600 key file or 0700 directory containing exactly one key file",
    )
    bundle_parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    protect_parser = commands.add_parser("protect", help="encrypt a complete skill folder")
    protect_parser.add_argument("source", help="skill directory path or installed skill name")
    protect_parser.add_argument("--output", type=Path, required=True)
    protect_parser.add_argument(
        "--passphrase-file", type=Path,
        help="0600 key file or 0700 directory containing exactly one key file",
    )
    protect_parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    unlock_parser = commands.add_parser("unlock", help="authenticate and temporarily decrypt a package")
    unlock_parser.add_argument("package", type=Path)
    unlock_parser.add_argument("--output", type=Path)
    unlock_parser.add_argument(
        "--passphrase-file", type=Path,
        help="0600 key file or 0700 directory containing exactly one key file",
    )
    cleanup_parser = commands.add_parser("cleanup", help="remove a marked temporary plaintext directory")
    cleanup_parser.add_argument("directory", type=Path)
    inspect_parser = commands.add_parser("inspect", help="show non-secret package metadata")
    inspect_parser.add_argument("package", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "bundle":
            bundle(args.source, args.output, args.passphrase_file, args.iterations)
        elif args.command == "protect":
            protect(args.source, args.output, args.passphrase_file, args.iterations)
        elif args.command == "unlock":
            unlock(args.package, args.output, args.passphrase_file)
        elif args.command == "cleanup":
            cleanup(args.directory)
        else:
            inspect(args.package)
    except ProtectorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
