# Skill Protector

![Skill Protector banner](docs/skill-protector-banner.png)

**Protect private Skills and share them safely.**  
**保护私有 Skill，让它可以安全分享和授权使用。**

[English](#english) · [简体中文](#简体中文)

---

<a id="english"></a>

## English

Skill Protector turns a private Skill into an installable protected Skill. Its instructions, scripts, templates, and other files stay locked until the user provides the correct key.

## Why protect a Skill?

- **Protect core content:** All original Skill files are encrypted. Only authorized users can unlock them.
- **Prevent tampering:** The encrypted package includes an integrity check that detects damage or unauthorized changes.
- **Distribute independently:** The protected Skill can decrypt itself, so Skill users do not need to install Skill Protector.

## Skill distributor

### 1. Install Skill Protector

Ask your Agent:

```text
Install the skill-protector Skill from https://github.com/yonglixiang/skill-protector/tree/main/skill-protector
```

Start a new Agent session after installation.

To install it yourself:

```bash
git clone https://github.com/yonglixiang/skill-protector.git skill-protector-repo
cd skill-protector-repo
mkdir -p /path/to/your-agent/skills
cp -R ./skill-protector /path/to/your-agent/skills/skill-protector
```

Requires macOS or Linux, Python 3.10 or later, and OpenSSL 3.

### 2. Protect a Skill

Tell the Agent which Skill to protect, where to save it, and where the key is:

```text
Use $skill-protector to protect the my-skill folder on my Desktop.
Save the protected Skill on my Desktop as my-skill-protected.
Use the private.key file on my Desktop as the key.
Keep the original Skill unchanged.
```

You may provide the passphrase directly in the conversation instead of using a key file.

### 3. Share it

Share the newly created protected Skill folder. Send the key separately through a trusted channel—never include it in the Skill folder, repository, README, or installation message.

## Skill user

### 1. Install the protected Skill

Use the address supplied by the distributor:

```text
Install the <Skill name> Skill from <Skill address>
```

Start a new Agent session after installation.

### 2. Use it

Call the protected Skill by name and provide the key:

```text
Use $my-skill-protected to complete this task:
<describe what you need>

The key is in the private.key file on my Desktop.
```

You may also provide the passphrase directly in the conversation. You do **not** need to install or call `$skill-protector`.

## Key rules

- Use at least 12 English letters or numbers. We recommend 16 or more characters, or five random words.
- Keep the passphrase on one line and save a backup. A lost key cannot be recovered.
- A key file should contain only the passphrase and be accessible only to you.
- A key folder should contain exactly one visible key file and be accessible only to you.
- Do not reuse an important account password or send the key with the protected Skill.

For more details, see [Security model](skill-protector/references/security-model.md).

---

<a id="简体中文"></a>

## 简体中文

Skill Protector 可以把私有 Skill 变成可安装的受保护 Skill。原 Skill 中的指令、脚本、模板和其他文件都会被锁住，只有提供正确密钥后才能使用。

## 保护 Skill 有什么好处？

- **保护核心内容：** Skill 的全部原始文件会被加密，只有获得授权的使用者才能解锁。
- **防止内容被篡改：** 加密包带有完整性验证，可识别损坏或未经授权的修改。
- **方便独立分发：** 受保护 Skill 自带解密能力，Skill 使用者不需要安装 Skill Protector。

## Skill 分发者

### 第一步：安装 Skill Protector

直接告诉 Agent：

```text
请从 https://github.com/yonglixiang/skill-protector/tree/main/skill-protector 安装 skill-protector Skill
```

安装后新建一个 Agent 会话。

如果想自己安装：

```bash
git clone https://github.com/yonglixiang/skill-protector.git skill-protector-repo
cd skill-protector-repo
mkdir -p /你的/Agent/Skills/文件夹
cp -R ./skill-protector /你的/Agent/Skills/文件夹/skill-protector
```

需要 macOS 或 Linux、Python 3.10 或更新版本，以及 OpenSSL 3。

### 第二步：保护一个 Skill

告诉 Agent 要保护哪个 Skill、保存到哪里，以及密钥在哪里：

```text
使用 $skill-protector 保护我桌面上的 my-skill 文件夹。
把受保护 Skill 保存到桌面，名称叫 my-skill-protected。
使用我桌面上的 private.key 文件作为密钥。
保留原来的 Skill，不要修改它。
```

也可以不使用密钥文件，直接在对话中提供口令。

### 第三步：分享

分享新生成的受保护 Skill 文件夹。密钥必须通过另一条可信渠道发送，不要把它放进 Skill 文件夹、代码仓库、README 或安装消息中。

## Skill 使用者

### 第一步：安装受保护 Skill

使用分发者提供的地址：

```text
请从 <Skill 地址> 安装 <Skill 名称>
```

安装后新建一个 Agent 会话。

### 第二步：使用

用受保护 Skill 自己的名称调用它，并提供密钥：

```text
使用 $my-skill-protected 完成下面的任务：
<写下你想完成的事情>

密钥在我桌面上的 private.key 文件里。
```

也可以直接在对话中提供口令。你**不需要**安装或调用 `$skill-protector`。

## 密钥要求

- 至少使用 12 个英文字母或数字。建议使用至少 16 个字符，或者五个随机单词。
- 口令只写一行，并在安全的地方留一份备份。密钥丢失后无法找回。
- 密钥文件里只能放口令，并保存在只有你能访问的位置。
- 密钥文件夹里只能有一个看得见的密钥文件，并保存在只有你能访问的位置。
- 不要使用重要账号的密码，也不要把密钥和受保护 Skill 一起发送。

更多信息请查看 [安全说明](skill-protector/references/security-model.md)。
