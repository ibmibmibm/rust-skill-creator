#!/usr/bin/env python3
"""
Skill Creator - Generate complete Rust skill from approved SPEC.md.

Usage:
    create_skill.py --spec <SPEC.md> --output <output-dir>

This script generates a complete skill with Rust source code and build scripts.
It only proceeds if the SPEC.md is marked as APPROVED.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional


class SpecParser:
    """Parse SPEC.md to extract skill configuration."""

    def __init__(self, spec_content: str):
        self.content = spec_content
        self.data = {}
        self._parse()

    def _parse(self):
        """Parse the SPEC.md content."""
        # Extract skill name
        name_match = re.search(r'### Name\s*\n`([^`]+)`', self.content)
        self.data['skill_name'] = name_match.group(1) if name_match else 'unnamed-skill'

        # Extract description
        desc_match = re.search(r'### Description \(for SKILL\.md frontmatter\)\s*\n(.+?)(?=\n###|\n---)', self.content, re.DOTALL)
        self.data['description'] = desc_match.group(1).strip() if desc_match else 'A Rust-based skill.'

        # Extract purpose from overview
        purpose_match = re.search(r'\*\*Purpose\*\*:\s*(.+?)(?=\n---|\n##)', self.content, re.DOTALL)
        self.data['purpose'] = purpose_match.group(1).strip() if purpose_match else ''

        # Extract inputs table
        self.data['inputs'] = self._parse_inputs_table()

        # Extract output format
        format_match = re.search(r'### Output Format\s*\n\*\*(\w+)\*\*', self.content)
        self.data['output_format'] = format_match.group(1).lower() if format_match else 'json'

        # Extract output fields
        self.data['output_fields'] = self._parse_outputs_table()

        # Extract dependencies
        deps_match = re.search(r'```toml\s*\[dependencies\]\s*\n(.*?)```', self.content, re.DOTALL)
        self.data['dependencies'] = deps_match.group(1).strip() if deps_match else ''

        # Extract API config
        self.data['api_config'] = self._parse_api_config()

    def _parse_inputs_table(self) -> list:
        """Parse input parameters table."""
        inputs = []
        table_match = re.search(r'### Inputs\s*\n(.*?)(?=\n###|\n---)', self.content, re.DOTALL)
        if not table_match:
            return inputs

        table_content = table_match.group(1)
        # Filter to table rows only (exclude separator with ---)
        rows = [line for line in table_content.split('\n') if line.startswith('|') and '---' not in line]

        for row in rows[1:]:  # Skip header row only (separator already filtered)
            cells = [cell.strip() for cell in row.split('|')[1:-1]]
            if len(cells) >= 5:
                inputs.append({
                    'name': cells[0],
                    'param_type': cells[1],
                    'required': cells[2].lower() == 'yes',
                    'default': cells[3] if cells[3] != '-' else None,
                    'description': cells[4]
                })

        return inputs

    def _parse_outputs_table(self) -> list:
        """Parse output fields table."""
        outputs = []
        table_match = re.search(r'### Output Fields\s*\n(.*?)(?=\n---)', self.content, re.DOTALL)
        if not table_match:
            return outputs

        table_content = table_match.group(1)
        # Filter to table rows only (exclude separator with ---)
        rows = [line for line in table_content.split('\n') if line.startswith('|') and '---' not in line]

        for row in rows[1:]:  # Skip header row only (separator already filtered)
            cells = [cell.strip() for cell in row.split('|')[1:-1]]
            if len(cells) >= 3:
                outputs.append({
                    'name': cells[0],
                    'field_type': cells[1],
                    'description': cells[2]
                })

        return outputs

    def _parse_api_config(self) -> Optional[dict]:
        """Parse API configuration section."""
        api_section = re.search(r'### API/External Services\s*\n(.*?)(?=\n###|\n---)', self.content, re.DOTALL)
        if not api_section or 'No external API' in api_section.group(1):
            return None

        config = {}
        section = api_section.group(1)

        endpoint_match = re.search(r'\*\*Endpoint\*\*:\s*`([^`]+)`', section)
        if endpoint_match:
            config['endpoint'] = endpoint_match.group(1)

        method_match = re.search(r'\*\*Method\*\*:\s*(\w+)', section)
        if method_match:
            config['method'] = method_match.group(1)

        auth_match = re.search(r'\*\*Authentication\*\*:\s*(\w+)(?:\s*\(via\s*`([^`]+)`)?', section)
        if auth_match and auth_match.group(1).lower() != 'none':
            config['auth_type'] = auth_match.group(1)
            config['auth_env_var'] = auth_match.group(2) if auth_match.group(2) else 'API_KEY'

        return config if config else None


def check_approval(content: str) -> bool:
    """Check if SPEC.md is marked as approved."""
    return '[x] APPROVED' in content or '[X] APPROVED' in content


def generate_skill_md(spec: SpecParser) -> str:
    """Generate SKILL.md content."""
    skill_name = spec.data['skill_name']
    skill_title = ' '.join(word.capitalize() for word in skill_name.split('-'))

    return f"""---
name: {skill_name}
description: {spec.data['description']}
---

# {skill_title}

{spec.data.get('purpose', '')}

## Usage

### Build

Compile the Rust application:

```bash
scripts/build.sh
```

### Run

Execute with arguments:

```bash
scripts/run.sh <arguments>
```

## Input Parameters

{_format_inputs_for_skill_md(spec.data['inputs'])}

## Output

Returns {spec.data['output_format'].upper()} formatted output.
"""


def _format_inputs_for_skill_md(inputs: list) -> str:
    """Format inputs for SKILL.md documentation."""
    if not inputs:
        return "No input parameters required."

    lines = []
    for inp in inputs:
        required = "(required)" if inp.get('required', True) else "(optional)"
        lines.append(f"- `{inp['name']}`: {inp.get('description', '')} {required}")

    return '\n'.join(lines)


def generate_main_rs(spec: SpecParser) -> str:
    """Generate main.rs content."""
    skill_name = spec.data['skill_name']
    inputs = spec.data['inputs']
    api_config = spec.data.get('api_config')
    output_format = spec.data['output_format']
    output_fields = spec.data['output_fields']

    # Build imports
    imports = [
        'use std::env;',
        'use std::error::Error;',
    ]

    if api_config:
        imports.append('use reqwest;')

    imports.extend([
        'use serde::{Deserialize, Serialize};',
        'use serde_json;',
    ])

    # Build argument parsing
    arg_parsing = _generate_arg_parsing(inputs)

    # Build main logic
    if api_config:
        main_logic = _generate_api_logic(api_config, inputs, output_fields)
    else:
        main_logic = _generate_basic_logic(inputs, output_format)

    # Build output struct
    output_struct = _generate_output_struct(output_fields) if output_fields else ""

    return f'''//! {skill_name} - Generated by rust-skill-creator
//!
//! {spec.data.get('description', '')}

{chr(10).join(imports)}

{output_struct}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {{
{arg_parsing}

{main_logic}

    Ok(())
}}
'''


def _generate_arg_parsing(inputs: list) -> str:
    """Generate argument parsing code."""
    if not inputs:
        return '    // No input arguments'

    lines = ['    let args: Vec<String> = env::args().collect();', '']

    for i, inp in enumerate(inputs):
        idx = i + 1
        name = inp['name']
        param_type = inp.get('param_type', 'String')
        required = inp.get('required', True)
        default = inp.get('default')

        if required:
            lines.append(f'    let {name} = args.get({idx})')
            lines.append(f'        .ok_or("Missing required argument: {name}")?')
            if param_type != 'String':
                lines.append(f'        .parse::<{param_type}>()?;')
            else:
                lines.append('        .to_string();')
        else:
            if default:
                lines.append(f'    let {name} = args.get({idx})')
                lines.append(f'        .map(|s| s.to_string())')
                lines.append(f'        .unwrap_or_else(|| "{default}".to_string());')
            else:
                lines.append(f'    let {name} = args.get({idx}).map(|s| s.to_string());')

        lines.append('')

    return '\n'.join(lines)


def _generate_api_logic(api_config: dict, inputs: list, output_fields: list) -> str:
    """Generate API call logic."""
    endpoint = api_config.get('endpoint', 'https://api.example.com')
    method = api_config.get('method', 'GET').upper()
    auth_type = api_config.get('auth_type')
    auth_env = api_config.get('auth_env_var', 'API_KEY')

    lines = ['    // Build HTTP client']
    lines.append('    let client = reqwest::Client::new();')
    lines.append('')

    # Build URL with input substitution
    url_expr = f'"{endpoint}"'
    for inp in inputs:
        name = inp['name']
        if f'{{{name}}}' in endpoint:
            url_expr = f'format!("{endpoint.replace("{" + name + "}", "{}") }", {name})'
            break

    # For format! the result is a String, for literals it's &str
    # Both String and &str implement IntoUrl, so we can just pass the variable directly
    lines.append(f'    let url = {url_expr};')
    lines.append('')

    # Build request
    lines.append(f'    let mut request = client.{method.lower()}(url);')

    if auth_type:
        lines.append('')
        lines.append(f'    // Add authentication')
        lines.append(f'    if let Ok(api_key) = env::var("{auth_env}") {{')
        if auth_type == 'api_key':
            lines.append('        request = request.query(&[("key", &api_key)]);')
        elif auth_type == 'bearer':
            lines.append('        request = request.bearer_auth(&api_key);')
        elif auth_type == 'basic':
            lines.append('        request = request.basic_auth(&api_key, None::<String>);')
        lines.append('    }')

    lines.append('')
    lines.append('    // Send request and parse response')
    lines.append('    let response = request.send().await?;')
    lines.append('')
    lines.append('    if !response.status().is_success() {')
    lines.append('        return Err(format!("API error: {}", response.status()).into());')
    lines.append('    }')
    lines.append('')

    if output_fields:
        lines.append('    let result: ApiResponse = response.json().await?;')
        lines.append('    println!("{}", serde_json::to_string_pretty(&result)?);')
    else:
        lines.append('    let text = response.text().await?;')
        lines.append('    println!("{}", text);')

    return '\n'.join(lines)


def _generate_basic_logic(inputs: list, output_format: str) -> str:
    """Generate basic processing logic."""
    lines = ['    // Process inputs']

    if inputs:
        first_input = inputs[0]['name']
        lines.append(f'    let result = format!("Processed: {{}}", {first_input});')
    else:
        lines.append('    let result = "No input provided".to_string();')

    lines.append('')
    if output_format == 'json':
        lines.append('    println!("{{\\"result\\": \\"{}\\"}}", result);')
    else:
        lines.append('    println!("{}", result);')

    return '\n'.join(lines)


def _generate_output_struct(output_fields: list) -> str:
    """Generate output struct definition."""
    if not output_fields:
        return ""

    lines = ['#[derive(Debug, Serialize, Deserialize)]']
    lines.append('struct ApiResponse {')

    for field in output_fields:
        name = field['name']
        # Convert to snake_case
        rust_name = re.sub(r'([A-Z])', r'_\1', name).lower().lstrip('_')
        rust_type = _map_type_to_rust(field.get('field_type', 'String'))

        if name != rust_name:
            lines.append(f'    #[serde(rename = "{name}")]')
        lines.append(f'    {rust_name}: {rust_type},')

    lines.append('}')
    return '\n'.join(lines)


def _map_type_to_rust(type_str: str) -> str:
    """Map generic type to Rust type."""
    type_map = {
        'string': 'String',
        'int': 'i64',
        'integer': 'i64',
        'float': 'f64',
        'double': 'f64',
        'number': 'f64',
        'bool': 'bool',
        'boolean': 'bool',
        'array': 'Vec<serde_json::Value>',
        'object': 'serde_json::Value',
    }
    return type_map.get(type_str.lower(), 'String')


def generate_cargo_toml(spec: SpecParser) -> str:
    """Generate Cargo.toml content."""
    skill_name = spec.data['skill_name']
    description = spec.data.get('description', 'A Rust-based skill')

    # Parse dependencies from spec
    deps = spec.data.get('dependencies', '')
    if not deps:
        deps = '''tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"'''

        if spec.data.get('api_config'):
            deps = f'reqwest = {{ version = "0.12", features = ["json"] }}\n{deps}'

    return f'''[package]
name = "{skill_name}"
version = "0.1.0"
edition = "2021"
description = "{description}"

[dependencies]
{deps}

[profile.release]
opt-level = 3
lto = true
'''


def generate_build_script(skill_name: str) -> str:
    """Generate build.sh content."""
    return f'''#!/bin/bash
# Build script for {skill_name}
# Generated by rust-skill-creator

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUST_DIR="$SCRIPT_DIR/../rust"

echo "Building {skill_name}..."
cd "$RUST_DIR"

cargo build --release

if [ $? -eq 0 ]; then
    echo "Build successful!"
    echo "Binary: $RUST_DIR/target/release/{skill_name}"
else
    echo "Build failed!"
    exit 1
fi
'''


def generate_run_script(skill_name: str) -> str:
    """Generate run.sh content."""
    return f'''#!/bin/bash
# Run script for {skill_name}
# Generated by rust-skill-creator

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BINARY="$SCRIPT_DIR/../rust/target/release/{skill_name}"

if [ ! -f "$BINARY" ]; then
    echo "Error: Binary not found. Run build.sh first."
    exit 1
fi

exec "$BINARY" "$@"
'''


def create_skill_directory(output_dir: str, skill_name: str, files: dict) -> Path:
    """Create skill directory and write all files."""
    skill_dir = Path(output_dir) / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (skill_dir / 'scripts').mkdir(exist_ok=True)
    (skill_dir / 'rust' / 'src').mkdir(parents=True, exist_ok=True)

    # Write files
    for rel_path, content in files.items():
        file_path = skill_dir / rel_path
        file_path.write_text(content)

        # Make shell scripts executable
        if rel_path.endswith('.sh'):
            file_path.chmod(0o755)

    return skill_dir


def compile_rust(skill_dir: Path) -> tuple[bool, str]:
    """Compile the Rust code and return (success, output)."""
    rust_dir = skill_dir / 'rust'

    try:
        result = subprocess.run(
            ['cargo', 'build', '--release'],
            cwd=rust_dir,
            capture_output=True,
            text=True,
            timeout=300
        )

        output = result.stdout + result.stderr
        return result.returncode == 0, output

    except subprocess.TimeoutExpired:
        return False, "Build timed out after 5 minutes"
    except FileNotFoundError:
        return False, "Cargo not found. Is Rust installed?"
    except Exception as e:
        return False, f"Build error: {e}"


def auto_fix_errors(skill_dir: Path, error_output: str, attempt: int) -> bool:
    """
    Attempt to fix common compilation errors.

    Returns True if fixes were applied, False otherwise.
    """
    main_rs = skill_dir / 'rust' / 'src' / 'main.rs'
    cargo_toml = skill_dir / 'rust' / 'Cargo.toml'

    content = main_rs.read_text()
    cargo_content = cargo_toml.read_text()

    fixes_applied = False

    # Fix: Missing Error import
    if 'cannot find type `Error`' in error_output or 'use of undeclared type' in error_output:
        if 'use std::error::Error;' not in content:
            content = 'use std::error::Error;\n' + content
            fixes_applied = True

    # Fix: Missing serde import
    if 'cannot find derive macro `Serialize`' in error_output or 'cannot find derive macro `Deserialize`' in error_output:
        if 'use serde::{Deserialize, Serialize};' not in content:
            content = content.replace('use std::error::Error;', 'use std::error::Error;\nuse serde::{Deserialize, Serialize};')
            fixes_applied = True

    # Fix: Missing reqwest
    if 'unresolved import `reqwest`' in error_output:
        if 'reqwest' not in cargo_content:
            cargo_content = cargo_content.replace(
                '[dependencies]',
                '[dependencies]\nreqwest = { version = "0.12", features = ["json"] }'
            )
            fixes_applied = True

    # Fix: Missing tokio
    if 'cannot find attribute `tokio`' in error_output or 'tokio::main' in error_output:
        if 'tokio' not in cargo_content:
            cargo_content = cargo_content.replace(
                '[dependencies]',
                '[dependencies]\ntokio = { version = "1", features = ["full"] }'
            )
            fixes_applied = True

    # Fix: async without await
    if 'unused `async`' in error_output:
        # This usually indicates the code structure needs adjustment
        # For now, just note it
        pass

    if fixes_applied:
        main_rs.write_text(content)
        cargo_toml.write_text(cargo_content)
        print(f"  Applied auto-fixes (attempt {attempt})")

    return fixes_applied


def main():
    if len(sys.argv) < 5 or '--spec' not in sys.argv or '--output' not in sys.argv:
        print("Usage: create_skill.py --spec <SPEC.md> --output <output-dir>")
        print()
        print("Generate a complete Rust skill from an approved SPEC.md file.")
        print("The SPEC.md must be marked as APPROVED before skill creation proceeds.")
        sys.exit(1)

    # Parse arguments
    spec_idx = sys.argv.index('--spec') + 1
    out_idx = sys.argv.index('--output') + 1

    spec_path = sys.argv[spec_idx]
    output_dir = sys.argv[out_idx]

    # Expand ~ in output path
    output_dir = os.path.expanduser(output_dir)

    # Load and check SPEC.md
    print(f"Loading SPEC.md from: {spec_path}")
    try:
        with open(spec_path, 'r') as f:
            spec_content = f.read()
    except FileNotFoundError:
        print(f"Error: SPEC.md not found: {spec_path}")
        sys.exit(1)

    # Check approval
    if not check_approval(spec_content):
        print()
        print("=" * 60)
        print("ERROR: SPEC.md is not approved!")
        print("=" * 60)
        print()
        print("The specification must be approved before skill creation.")
        print("Edit the SPEC.md and change:")
        print("  [ ] APPROVED  -->  [x] APPROVED")
        sys.exit(1)

    # Parse spec
    print("Parsing specification...")
    spec = SpecParser(spec_content)
    skill_name = spec.data['skill_name']

    print(f"Generating skill: {skill_name}")

    # Generate all files
    files = {
        'SKILL.md': generate_skill_md(spec),
        'scripts/build.sh': generate_build_script(skill_name),
        'scripts/run.sh': generate_run_script(skill_name),
        'rust/Cargo.toml': generate_cargo_toml(spec),
        'rust/src/main.rs': generate_main_rs(spec),
    }

    # Create skill directory
    print(f"Creating skill at: {output_dir}/{skill_name}")
    skill_dir = create_skill_directory(output_dir, skill_name, files)

    # Compile with auto-fix retry
    print()
    print("Compiling Rust code...")

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        print(f"  Build attempt {attempt}/{max_attempts}...")
        success, output = compile_rust(skill_dir)

        if success:
            print()
            print("=" * 60)
            print("SUCCESS! Skill created and compiled.")
            print("=" * 60)
            print()
            print(f"Skill location: {skill_dir}")
            print()
            print("Usage:")
            print(f"  cd {skill_dir}")
            print("  scripts/build.sh  # Build (already done)")
            print("  scripts/run.sh <args>  # Run")
            sys.exit(0)

        print(f"  Build failed.")

        if attempt < max_attempts:
            if auto_fix_errors(skill_dir, output, attempt):
                continue
            else:
                print("  No auto-fixes available.")
                break
        else:
            print("  Max attempts reached.")

    # Build failed after all attempts
    print()
    print("=" * 60)
    print("BUILD FAILED")
    print("=" * 60)
    print()
    print("Compilation errors:")
    print(output)
    print()
    print(f"Skill created at: {skill_dir}")
    print("Manual fixes may be required.")
    print("See references/error-handling.md for common solutions.")
    sys.exit(1)


if __name__ == "__main__":
    main()
