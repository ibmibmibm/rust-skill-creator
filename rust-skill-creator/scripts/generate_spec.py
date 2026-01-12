#!/usr/bin/env python3
"""
SPEC Generator - Create SPEC.md from requirements JSON.

Usage:
    generate_spec.py --requirements <requirements.json> --output <SPEC.md>

This script generates a specification document that must be approved
by the user before skill creation proceeds.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def load_requirements(requirements_path: str) -> dict:
    """Load requirements from JSON file."""
    with open(requirements_path, 'r') as f:
        return json.load(f)


def generate_inputs_table(inputs: list) -> str:
    """Generate markdown table for input parameters."""
    if not inputs:
        return "No input parameters defined."

    lines = [
        "| Parameter | Type | Required | Default | Description |",
        "|-----------|------|----------|---------|-------------|"
    ]

    for inp in inputs:
        name = inp.get('name', '')
        param_type = inp.get('param_type', 'String')
        required = 'Yes' if inp.get('required', True) else 'No'
        default = inp.get('default', '-') or '-'
        description = inp.get('description', '')
        lines.append(f"| {name} | {param_type} | {required} | {default} | {description} |")

    return '\n'.join(lines)


def generate_outputs_table(output_fields: list) -> str:
    """Generate markdown table for output fields."""
    if not output_fields:
        return "Output format to be determined based on implementation."

    lines = [
        "| Field | Type | Description |",
        "|-------|------|-------------|"
    ]

    for field in output_fields:
        name = field.get('name', '')
        field_type = field.get('field_type', 'String')
        description = field.get('description', '')
        lines.append(f"| {name} | {field_type} | {description} |")

    return '\n'.join(lines)


def generate_dependencies(req: dict) -> str:
    """Generate Cargo.toml dependencies section."""
    deps = [
        'tokio = { version = "1", features = ["full"] }',
        'serde = { version = "1", features = ["derive"] }',
        'serde_json = "1"'
    ]

    # Add reqwest if API config exists
    if req.get('api_config'):
        deps.insert(0, 'reqwest = { version = "0.12", features = ["json"] }')

    # Add additional crates
    additional = req.get('additional_crates', [])
    for crate in additional:
        if '=' in crate:
            deps.append(crate)
        else:
            deps.append(f'{crate} = "*"')

    return '\n'.join(f'  - {dep}' for dep in deps)


def generate_api_section(api_config: dict) -> str:
    """Generate API configuration section."""
    if not api_config:
        return "No external API required."

    lines = []
    lines.append(f"- **Endpoint**: `{api_config.get('endpoint', 'TBD')}`")
    lines.append(f"- **Method**: {api_config.get('method', 'GET')}")

    auth_type = api_config.get('auth_type')
    if auth_type:
        auth_env = api_config.get('auth_env_var', 'API_KEY')
        lines.append(f"- **Authentication**: {auth_type} (via `{auth_env}` environment variable)")
    else:
        lines.append("- **Authentication**: None required")

    headers = api_config.get('headers')
    if headers:
        lines.append("- **Headers**:")
        for key, value in headers.items():
            lines.append(f"  - `{key}`: `{value}`")

    rate_limit = api_config.get('rate_limit')
    if rate_limit:
        lines.append(f"- **Rate Limits**: {rate_limit}")

    return '\n'.join(lines)


def generate_error_handling(error_scenarios: list) -> str:
    """Generate error handling section."""
    if not error_scenarios:
        error_scenarios = [
            "Network connection failure",
            "Invalid input parameters",
            "API error responses",
            "JSON parse errors"
        ]

    lines = []
    for i, scenario in enumerate(error_scenarios, 1):
        lines.append(f"{i}. **{scenario}**: Return descriptive error message to user")

    return '\n'.join(lines)


def generate_spec(req: dict) -> str:
    """Generate complete SPEC.md content."""
    skill_name = req.get('skill_name', 'unnamed-skill')
    skill_title = ' '.join(word.capitalize() for word in skill_name.split('-'))

    spec = f"""# Skill Specification: {skill_title}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Status

- [x] PENDING APPROVAL
- [ ] APPROVED
- [ ] REJECTED

---

## Overview

{req.get('description', 'No description provided.')}

**Purpose**: {req.get('purpose', 'No purpose specified.')}

---

## User Requirements

{req.get('notes', 'User requested a Rust-based skill for this functionality.')}

---

## Skill Details

### Name
`{skill_name}`

### Description (for SKILL.md frontmatter)
{req.get('description', 'A Rust-based skill.')}

### Trigger Scenarios
- User asks to {req.get('purpose', 'perform the skill task').lower()}
- Requests involving {skill_name.replace('-', ' ')}

---

## Input/Output

### Inputs

{generate_inputs_table(req.get('inputs', []))}

### Output Format
**{req.get('output_format', 'json').upper()}**

### Output Fields

{generate_outputs_table(req.get('output_fields', []))}

---

## Technical Design

### Rust Application

- **Binary Name**: `{skill_name}`
- **Entry Point**: `main.rs` with async main function
- **Runtime**: tokio async runtime

### Dependencies

```toml
[dependencies]
{generate_dependencies(req).replace('  - ', '')}
```

### API/External Services

{generate_api_section(req.get('api_config'))}

### Error Handling

{generate_error_handling(req.get('error_scenarios'))}

---

## Generated Files

```
{skill_name}/
├── SKILL.md              # Skill definition and usage
├── scripts/
│   ├── build.sh          # Compiles Rust code (cargo build --release)
│   └── run.sh            # Executes compiled binary with arguments
└── rust/
    ├── Cargo.toml        # Package and dependencies
    └── src/
        └── main.rs       # Application entry point
```

---

## Approval

**Review this specification carefully.**

To proceed with skill creation:
- Change `[x] PENDING APPROVAL` to `[ ] PENDING APPROVAL`
- Change `[ ] APPROVED` to `[x] APPROVED`

To request changes:
- Describe the modifications needed below

To reject:
- Change `[ ] REJECTED` to `[x] REJECTED`
- Provide reasoning below

### Feedback

_Add any comments or change requests here._
"""

    return spec


def save_spec(content: str, output_path: str) -> bool:
    """Save SPEC.md to file."""
    try:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, 'w') as f:
            f.write(content)

        print(f"SPEC.md saved to: {output}")
        return True
    except Exception as e:
        print(f"Error saving SPEC.md: {e}")
        return False


def main():
    if len(sys.argv) < 5 or '--requirements' not in sys.argv or '--output' not in sys.argv:
        print("Usage: generate_spec.py --requirements <requirements.json> --output <SPEC.md>")
        print()
        print("Generate a SPEC.md specification document from requirements JSON.")
        print("The specification must be approved by the user before skill creation.")
        sys.exit(1)

    # Parse arguments
    req_idx = sys.argv.index('--requirements') + 1
    out_idx = sys.argv.index('--output') + 1

    requirements_path = sys.argv[req_idx]
    output_path = sys.argv[out_idx]

    print(f"Loading requirements from: {requirements_path}")
    try:
        req = load_requirements(requirements_path)
    except FileNotFoundError:
        print(f"Error: Requirements file not found: {requirements_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in requirements file: {e}")
        sys.exit(1)

    print("Generating SPEC.md...")
    spec_content = generate_spec(req)

    if save_spec(spec_content, output_path):
        print()
        print("=" * 60)
        print("SPEC.md generated successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Review the SPEC.md file")
        print("2. Mark as APPROVED to proceed with skill creation")
        print("3. Or request changes / reject as needed")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
