# Landing Page Creator Installation

Install the entire `landing-page-creator` directory, not only `SKILL.md`. The skill uses relative
references to files in its subdirectories, so the complete folder structure must be preserved.

## Required installed structure

```text
$CODEX_HOME/skills/
└── landing-page-creator/
    ├── SKILL.md
    ├── README.md
    ├── agents/
    │   └── openai.yaml
    └── references/
        └── implementation-contract.md
```

## Install with `$skill-installer`

When `$skill-installer` is available, use this prompt:

```text
Use $skill-installer to install the complete skill package from:

https://github.com/eladrave/skills/tree/main/landing-page-creator

Preserve all files and subdirectories, install it globally, verify the complete package, and tell me
when the installed skill is available.
```

The important wording is `complete skill package`. The installer must recursively install the folder
instead of downloading only `SKILL.md`.

## Install manually

The following commands install the package into the configured Codex skills directory. They stop if
an installation already exists, so they do not silently merge or overwrite an existing package.

```bash
set -euo pipefail

SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
TEMP_DIR="$(mktemp -d)"

git clone \
  --depth 1 \
  --filter=blob:none \
  --sparse \
  https://github.com/eladrave/skills.git \
  "$TEMP_DIR/repository"

git -C "$TEMP_DIR/repository" \
  sparse-checkout set landing-page-creator

mkdir -p "$SKILLS_DIR"

if [ -e "$SKILLS_DIR/landing-page-creator" ]; then
  echo "Skill already exists: $SKILLS_DIR/landing-page-creator"
  exit 1
fi

cp -R \
  "$TEMP_DIR/repository/landing-page-creator" \
  "$SKILLS_DIR/landing-page-creator"
```

## Verify the installation

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/landing-page-creator"

test -f "$SKILL_DIR/SKILL.md"
test -f "$SKILL_DIR/README.md"
test -f "$SKILL_DIR/agents/openai.yaml"
test -f "$SKILL_DIR/references/implementation-contract.md"

echo "Complete skill package installed"
```

Refresh or reopen the Codex Skills page after installation so skill discovery can update.

## Directory or ZIP upload

For API-based skill uploads, OpenAI supports uploading a directory or a single ZIP archive. The
directory or ZIP must preserve the complete package structure, with `SKILL.md` at the skill root and
all referenced subdirectories included.

See the [OpenAI Skills API documentation](https://developers.openai.com/api/reference/python/resources/skills/methods/create).
