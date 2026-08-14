---
name: skill-protector
description: Encrypt complete Codex skill folders and generate installable protected Skills that unlock themselves when authorized. Use when a user asks to encrypt, password-protect, package, lock, decrypt, inspect, install, or use a protected Skill, whether the source is an installed Skill name, a Skill folder, a protected wrapper, or a .skill.enc archive.
---

# Skill Protector

Protect every original file in a Skill as one authenticated encrypted payload. By default, generate a self-contained, installable protected Skill with a minimal plaintext loader.

## Security rules

- Require a passphrase of at least 12 UTF-8 bytes with no newline, carriage-return, or NUL bytes. Recommend 16+ characters or at least five random words because there is no recovery mechanism.
- Accept a passphrase supplied in conversation, a regular non-symlink key file with mode `0600` or stricter, or a non-symlink key directory with mode `0700` or stricter containing exactly one non-hidden regular non-symlink key file. Require that contained file to use mode `0600` or stricter.
- Warn once before the user posts a new conversational passphrase because it remains in chat history. Do not ask them to resend a value already supplied.
- Never place a passphrase in a command, argument, environment variable, source file, durable temporary file, or printed output.
- For a conversational passphrase, run the script in an interactive PTY and send it only at the hidden prompt. Send it twice when protecting and once when unlocking.
- Never overwrite or delete the source Skill unless the user separately and explicitly requests that destructive action.
- Treat decrypted contents as sensitive and always clean their marked temporary directory after use.
- Do not claim DRM or protection from an authorized runtime. Read [references/security-model.md](references/security-model.md) before changing security claims or the package format.

For key-file setup, recommend:

```bash
chmod 600 /absolute/path/to/private.key
```

For a key directory, recommend `chmod 700 DIRECTORY` and `chmod 600 DIRECTORY/KEY_FILE`. Treat the entire file content as the passphrase except for one optional trailing line ending.

## Locate a source Skill

Accept an explicit Skill directory or an installed Skill name. For a name, search `$CODEX_HOME/skills` when set, then `~/.codex/skills`. Require a regular `SKILL.md` and reject symlinks anywhere in the source tree. If several matches exist, ask the user to choose an explicit path.

## Create an installable protected Skill

Use this as the default protection workflow.

1. Choose a new output directory outside the source. Its basename becomes the protected Skill name and must use lowercase hyphen-case, for example `presentations-protected`.
2. Obtain the passphrase or key path under the security rules above.
3. Run:

   ```bash
   python3 scripts/skill_crypto.py bundle SOURCE \
     --output /absolute/path/to/presentations-protected
   ```

   Add `--passphrase-file /absolute/path` for a key file or private single-key directory. For a conversational passphrase, use a PTY and answer both hidden prompts.
4. Report the generated directory, its invocation name, and that the source remains unchanged.

The generated directory contains only:

- A minimal plaintext loader `SKILL.md` and UI metadata required for Codex discovery.
- `payload.skill.enc`, containing every original Skill file and all original text.
- A bundled decryption script, so the protected Skill does not depend on `$skill-protector` at runtime.

The user can install the generated directory in the Codex Skills location. After Codex loads it, they invoke that protected Skill directly and provide its credential or credential path. Do not tell them to invoke `$skill-protector` for normal use.

## Create a raw encrypted archive

Use raw mode only when the user explicitly wants a standalone `.skill.enc` archive rather than an installable Skill:

```bash
python3 scripts/skill_crypto.py protect SOURCE --output OUTPUT.skill.enc
```

Add `--passphrase-file /absolute/path` when applicable. A raw archive cannot be discovered as a Skill and must be unlocked with this project or another compatible runtime.

## Unlock a raw archive

For raw archives only, run:

```bash
python3 scripts/skill_crypto.py unlock PACKAGE.skill.enc
```

Add `--passphrase-file /absolute/path` when applicable. Read the returned `SKILL.md` completely, follow it for the task, then clean the exact returned cleanup root in a `finally`-style step:

```bash
python3 scripts/skill_crypto.py cleanup TEMP_DIRECTORY
```

Do not use this workflow when the user already loaded a generated protected Skill; its own plaintext loader performs these steps.

## Inspect a package

Use `python3 scripts/skill_crypto.py inspect PACKAGE.skill.enc` to show format and size metadata without decrypting. For an installable wrapper, inspect its `payload.skill.enc`.

## Failure handling

- On authentication failure, say only that the passphrase is incorrect or the package is damaged.
- On unsafe content, abort extraction and preserve the encrypted payload.
- On cleanup failure, report the exact marked temporary path and do not claim the plaintext was removed.
- On missing OpenSSL, ask the user to install OpenSSL 3 or make a compatible `openssl` executable available.
