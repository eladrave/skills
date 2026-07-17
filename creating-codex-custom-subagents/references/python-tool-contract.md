# Python Tool Contract

Complete this before relying on bundled Python as part of an agent workflow.

## Command

- Script path:
- Python version:
- Invocation command:
- Working-directory assumptions:
- Timeout:

## Inputs

- Required arguments:
- Optional arguments:
- Supported formats:
- Maximum size:
- Encoding:
- Validation rules:
- Handling of paths with spaces:
- Handling of untrusted content:

## Outputs

- Output location:
- Output format:
- Schema version:
- Required fields:
- Input identity field:
- Freshness or timestamp rule:
- Atomic-write behavior:

## Exit codes

- `0`:
- `1`:
- `2`:
- Other:

## Diagnostics

- stdout usage:
- stderr usage:
- Logging location:
- Secret redaction:

## Dependencies

- Standard library only, yes or no:
- Dependency manifest:
- Virtual environment:
- Installation policy:
- Offline behavior:

## Safety

- Allowed read roots:
- Allowed write roots:
- Network use:
- Subprocess use:
- Shell interpolation prohibited:
- Idempotency expectations:
- Cleanup behavior:

## Tests

- Unit tests:
- Representative fixture:
- Invalid input fixture:
- Large input fixture:
- Injection-like input fixture:
- Malformed dependency output:
- Timeout test:
- Output schema validation:
