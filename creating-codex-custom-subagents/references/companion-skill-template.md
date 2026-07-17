# Companion Skill Template

Create this as `<skill-directory>/SKILL.md`. Replace all placeholders and remove irrelevant sections.

```markdown
---
name: data-analyzer
description: Use when analyzing supported CSV or JSON datasets with the bundled deterministic analyzer. Do not use for spreadsheet editing or unsupported binary formats.
---

# Data Analyzer

## Required inputs

- Input file path
- Analysis goal
- Optional output path

## Supported inputs

- UTF-8 CSV
- JSON array of records

Reject unsupported formats without guessing.

## Required workflow

1. Validate that the input exists and is within the allowed workspace.
2. Run the bundled analyzer using an argument array equivalent to:

   ```bash
   python3 <skill-directory>/scripts/analyze.py \
     --input "$INPUT" \
     --output "$OUTPUT"
   ```

3. Confirm the command exit code is zero.
4. Read the generated JSON report.
5. Validate its schema version, input identity, status, and required fields.
6. Base quantitative conclusions on the generated report.
7. Label additional model interpretation as inference.

## Failure behavior

- Nonzero exit: report stderr and stop.
- Missing output: report failure and stop.
- Invalid JSON or schema: report failure and stop.
- Unsupported input: state supported formats and stop.
- Missing runtime or dependency: report the exact missing component. Do not install it unless permitted.

## Output

Return:

1. Summary
2. Quantitative findings from the report
3. Interpretive findings, clearly labeled
4. Validation performed
5. Limitations
```

## Agent linkage

In the custom agent TOML, point `skills.config.path` to the skill directory, not the file:

```toml
[[skills.config]]
path = "/absolute/path/to/.agents/skills/data-analyzer"
enabled = true
```

Also mention the required Skill explicitly in `developer_instructions` when its use is mandatory.
