# Security model

## Protection provided

The `.skill.enc` package protects the complete archived skill at rest. It uses encrypt-then-MAC:

- OpenSSL AES-256-CBC encryption with PBKDF2-HMAC-SHA-256 and a random encryption salt.
- A separate PBKDF2-HMAC-SHA-256 derivation with a random MAC salt.
- HMAC-SHA-256 over the format header and ciphertext, verified before decryption.
- 600,000 PBKDF2 iterations by default.

The passphrase must contain at least 12 UTF-8 bytes and no newline, carriage-return, or NUL bytes. Recommend 16+ characters or at least five random words. It is accepted through `getpass` over an interactive PTY, a regular non-symlink key file whose POSIX mode has no group or other permission bits, or a non-symlink mode-`0700` directory containing exactly one non-hidden regular non-symlink key file. The contained file must use mode `0600` or stricter. One trailing `LF` or `CRLF` line ending in a key file is ignored.

The passphrase is never accepted as a command-line value or environment variable. A passphrase supplied in conversation remains part of chat history and may also be retained by the surrounding product, so a local key file is safer for sensitive or reusable credentials. There is no credential recovery mechanism.

## Explicit limitations

- Each installable protected Skill contains a minimal plaintext `SKILL.md`, generic UI metadata, and a bundled loader script so Codex can discover and invoke it without `$skill-protector`. The original Skill content remains encrypted in `payload.skill.enc`.
- Package filenames, file size, modification time, and the fact that a protected package exists are not secret.
- Once authorized, Codex must see plaintext instructions to use the target Skill. This is encryption at rest, not DRM, copy prevention, revocable licensing, or protection from an authorized runtime.
- A compromised host, privileged local process, terminal recorder, model transcript containing copied plaintext, or modified launcher can defeat the protection.
- A passphrase posted in chat is only as confidential as that conversation and its retention controls. Deleting temporary plaintext does not remove the passphrase from chat history.
- Passphrase strength remains important. Recommend at least five randomly selected words or an equivalent password-manager-generated secret.

## Package layout

All integers are unsigned big-endian values:

```text
8 bytes   magic: SKPROT1\0
4 bytes   PBKDF2 iteration count
16 bytes  MAC salt
N bytes   OpenSSL salted AES-256-CBC ciphertext
32 bytes  HMAC-SHA-256 tag
```

The encrypted plaintext is a gzip-compressed tar archive containing one top-level skill directory. Symlinks, hard links, device files, absolute paths, and parent traversal are rejected.

## Installable wrapper layout

The `bundle` command creates a self-contained Codex Skill:

```text
protected-skill/
├── SKILL.md                 minimal generic loader
├── agents/openai.yaml       discovery metadata
├── payload.skill.enc        complete encrypted source Skill
└── scripts/skill_crypto.py  bundled unlock and cleanup runtime
```

The wrapper name and generic loader text are public. The source Skill's original metadata, instructions, scripts, references, templates, and assets exist only inside the encrypted payload.

## Lifecycle

Encryption never alters the source. Invoking an installable protected Skill runs its bundled loader, writes the restored source Skill to a mode-`0700` temporary directory, follows the restored instructions, and removes the marked directory afterward. Cleanup only removes marked directories after resolving and validating the target path; this limits accidental deletion.
