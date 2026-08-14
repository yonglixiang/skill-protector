# Skill Protector

![Skill Protector banner](docs/skill-protector-banner.png)

**Protect private Skills. Share them without sharing their contents.**  
**保护私有 Skill，让它可以安全分发和授权使用。**

[English](#english) · [简体中文](#简体中文)

---

<a id="english"></a>

## English

### What is Skill Protector?

Skill Protector turns a private Skill into a protected Skill that other people can install.

Everything in the original Skill—including its instructions, scripts, examples, templates, and images—stays locked. The protected Skill works only after the user provides the correct key.

### Who does what?

| Skill distributor | Skill user |
| --- | --- |
| Protects the original Skill. | Installs the protected Skill. |
| Shares the protected Skill. | Provides the key when using it. |
| Sends the key separately. | Does not need Skill Protector. |

~~~text
Original Skill → protect → share the protected Skill
                                  ↓
                     install → provide key → use
~~~

## For Skill distributors

### Step 1: Install Skill Protector

The easiest way is to send this message to your Agent:

~~~text
Install the skill-protector Skill from https://github.com/yonglixiang/skill-protector
~~~

Replace the example address with this repository's real address. Start a new Agent session after installation.

If you prefer to install it yourself, clone the repository first:

~~~bash
git clone https://github.com/yonglixiang/skill-protector.git skill-protector-repo
cd skill-protector-repo
mkdir -p /path/to/your-agent/skills
cp -R ./skill-protector /path/to/your-agent/skills/skill-protector
~~~

Replace /path/to/your-agent/skills with the folder where your Agent stores Skills.

Skill Protector currently needs macOS or Linux, Python 3.10 or later, and OpenSSL 3.

### Step 2: Protect a Skill

You can describe the files in language:

~~~text
Use $skill-protector to protect the my-skill folder on my Desktop.
Save the protected Skill on my Desktop and name it my-skill-protected.
Use the private.key file on my Desktop as the key.
Keep my original Skill unchanged.
~~~

You can also paste the passphrase directly into the conversation instead of using a key file.

### Step 3: Share it

Upload the newly created protected Skill folder to GitHub or your usual sharing location. Then give users its installation address:

~~~text
Install the <Skill name> Skill from <Skill address>
~~~

Send the key through a different, trusted channel. Do not put the key in the Skill folder, GitHub repository, README, issue, release download, or installation message.

## For Skill users

### Step 1: Install the protected Skill

Use the address supplied by the distributor:

~~~text
Install the <Skill name> Skill from <Skill address>
~~~

If the distributor sends you a folder instead, tell your Agent where that folder is and ask it to install the Skill.

Start a new Agent session after installation.

### Step 2: Use it with the key

Call the protected Skill by its own name and tell the Agent where your key file is:

~~~text
Use $my-skill-protected to complete this task:
<describe what you need>

The key is in the private.key file on my Desktop.
~~~

You may also provide the passphrase directly in the conversation.

You do **not** need to install or call $skill-protector. The protected Skill knows how to ask for the key and open itself for the current task. It closes and removes the temporary unlocked copy afterward.

## Key rules

### Choose one way to provide the key

- **In the conversation:** easiest, but the passphrase remains in the chat history.
- **A key file:** recommended for keys you plan to use again.
- **A key folder:** useful when you prefer to point the Agent to a folder instead of a file.

### Create a strong passphrase

- Use at least 12 English letters or numbers. For better protection, use 16 or more characters, or five random words.
- Keep it on one line.
- Save a backup somewhere safe. A lost key cannot be recovered.
- Do not reuse an important account password.

### If you use a key file

- Put only the passphrase in the file.
- Store it somewhere only you can open.
- On macOS or Linux, you can limit access with:

~~~bash
chmod 600 /path/to/private.key
~~~

### If you use a key folder

- Keep exactly one visible key file in that folder.
- Do not keep other possible key files in the same folder.
- On macOS or Linux, you can limit access with:

~~~bash
chmod 700 /path/to/key-folder
chmod 600 /path/to/key-folder/private.key
~~~

## What can other people see?

They can see the protected Skill's name and a short note explaining how to provide the key. They cannot see the original Skill contents without the correct key.

For detailed security information, see [the security notes](skill-protector/references/security-model.md).

## For contributors

~~~text
.
├── README.md
├── docs/
│   └── skill-protector-banner.png
├── skill-protector/          # the folder users install
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/security-model.md
│   └── scripts/skill_crypto.py
└── tests/
    └── test_skill_crypto.py
~~~

Run the checks from the repository folder:

~~~bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_skill_crypto.py
~~~

---

<a id="简体中文"></a>

## 简体中文

### Skill Protector 是什么？

Skill Protector 可以把私有 Skill 变成一个可以安全分享的受保护 Skill。

原 Skill 里的指令、脚本、示例、模板和图片都会被锁住。使用者只有提供正确的密钥，才能使用这个 Skill。

### 谁负责什么？

| Skill 分发者 | Skill 使用者 |
| --- | --- |
| 保护原来的 Skill。 | 安装受保护 Skill。 |
| 分享受保护 Skill。 | 使用时提供密钥。 |
| 通过另一条渠道发送密钥。 | 不需要安装 Skill Protector。 |

~~~text
原 Skill → 进行保护 → 分享受保护 Skill
                            ↓
                  安装 → 提供密钥 → 使用
~~~

## Skill 分发者

### 第一步：安装 Skill Protector

最简单的方法是直接给 Agent 发送这句话：

~~~text
请从 https://github.com/yonglixiang/skill-protector 安装 skill-protector Skill
~~~

如果想自己安装，请先克隆仓库：

~~~bash
git clone https://github.com/yonglixiang/skill-protector.git skill-protector
cd skill-protector
mkdir -p /你的/Agent/Skills/文件夹
cp -R ./skill-protector /你的/Agent/Skills/文件夹/skill-protector
~~~

请把 /你的/Agent/Skills/文件夹 换成 Agent 存放 Skill 的文件夹。

Skill Protector 目前需要 macOS 或 Linux、Python 3.10 或更新版本，以及 OpenSSL 3。

### 第二步：保护一个 Skill

可以直接用日常语言描述文件在哪里：

~~~text
使用 $skill-protector 保护我桌面上的 my-skill 文件夹。
把生成的受保护 Skill 保存到桌面，名称叫 my-skill-protected。
使用我桌面上的 private.key 文件作为密钥。
保留原来的 Skill，不要修改它。
~~~

如果没有密钥文件，也可以直接在对话中提供口令。

### 第三步：分享

把新生成的受保护 Skill 文件夹上传到 GitHub 或平时使用的分享位置，再把安装地址发给使用者：

~~~text
请从 <Skill 地址> 安装 <Skill 名称>
~~~

请通过另一条可信的渠道发送密钥。不要把密钥放进 Skill 文件夹、GitHub 仓库、README、Issue、Release 下载文件或安装消息中。

## Skill 使用者

### 第一步：安装受保护 Skill

使用分发者提供的地址：

~~~text
请从 <Skill 地址> 安装 <Skill 名称>
~~~

如果分发者直接发给你一个文件夹，只要告诉 Agent 文件夹在哪里，并让它安装这个 Skill。

安装后新建一个 Agent 会话。

### 第二步：提供密钥并使用

用受保护 Skill 自己的名称调用它，再告诉 Agent 密钥文件在哪里：

~~~text
使用 $my-skill-protected 完成下面的任务：
<写下你想完成的事情>

密钥在我桌面上的 private.key 文件里。
~~~

也可以直接在对话中提供口令。

你**不需要**安装或调用 $skill-protector。受保护 Skill 会自己请求密钥，只为当前任务打开内容，并在完成后删除临时打开的副本。

## 密钥怎么准备？

### 选择一种提供方式

- **直接在对话中提供：**最方便，但口令会留在聊天记录中。
- **使用密钥文件：**适合需要多次使用的密钥，也是推荐方式。
- **使用密钥文件夹：**不想指定某个文件时，可以告诉 Agent 密钥文件夹在哪里。

### 设置一个安全的口令

- 至少使用 12 个英文字母或数字。为了更安全，建议使用至少 16 个字符，或者五个随机单词。
- 口令只写一行，不要换行。
- 在安全的地方留一份备份。密钥丢失后无法找回。
- 不要使用重要账号的密码。

### 如果使用密钥文件

- 文件里只放口令，不要放其他内容。
- 把文件保存在只有你能打开的位置。
- 在 macOS 或 Linux 上，可以用下面的命令限制其他人访问：

~~~bash
chmod 600 /密钥文件的位置/private.key
~~~

### 如果使用密钥文件夹

- 文件夹里只能放一个看得见的密钥文件。
- 不要在同一个文件夹里放其他可能被当作密钥的文件。
- 在 macOS 或 Linux 上，可以用下面的命令限制其他人访问：

~~~bash
chmod 700 /密钥文件夹的位置
chmod 600 /密钥文件夹的位置/private.key
~~~

## 其他人能看到什么？

其他人可以看到受保护 Skill 的名称，以及一小段如何提供密钥的说明。没有正确密钥时，他们看不到原 Skill 的内容。

想了解更详细的安全说明，请查看[安全说明](skill-protector/references/security-model.md)。

## 给项目贡献者

~~~text
.
├── README.md
├── docs/
│   └── skill-protector-banner.png
├── skill-protector/          # 用户安装这个文件夹
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/security-model.md
│   └── scripts/skill_crypto.py
└── tests/
    └── test_skill_crypto.py
~~~

在仓库文件夹中运行检查：

~~~bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_skill_crypto.py
~~~

