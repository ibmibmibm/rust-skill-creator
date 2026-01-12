#!/usr/bin/env python3
"""
SPEC Validator - Validate SPEC.md format and completeness.

Usage:
    validate_spec.py <SPEC.md>

This script validates that a SPEC.md file has all required sections
and follows the expected format.
"""

import re
import sys
from pathlib import Path


class ValidationResult:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def add_error(self, msg: str):
        self.errors.append(msg)

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def print_results(self):
        if self.errors:
            print("ERRORS:")
            for err in self.errors:
                print(f"  - {err}")
            print()

        if self.warnings:
            print("WARNINGS:")
            for warn in self.warnings:
                print(f"  - {warn}")
            print()

        if self.is_valid:
            if self.warnings:
                print("Validation PASSED with warnings.")
            else:
                print("Validation PASSED.")
        else:
            print("Validation FAILED.")


def validate_spec(spec_path: str) -> ValidationResult:
    """
    Validate SPEC.md file.

    Checks:
    - File exists and is readable
    - Required sections are present
    - Skill name follows conventions
    - Description is present
    - Input/output sections are defined
    - Status section exists
    """
    result = ValidationResult()

    # Check file exists
    path = Path(spec_path)
    if not path.exists():
        result.add_error(f"File not found: {spec_path}")
        return result

    try:
        content = path.read_text()
    except Exception as e:
        result.add_error(f"Cannot read file: {e}")
        return result

    # Check required sections
    required_sections = [
        ('## Status', 'Status section'),
        ('## Overview', 'Overview section'),
        ('## Skill Details', 'Skill Details section'),
        ('### Name', 'Skill name'),
        ('## Input/Output', 'Input/Output section'),
        ('## Technical Design', 'Technical Design section'),
        ('## Generated Files', 'Generated Files section'),
        ('## Approval', 'Approval section'),
    ]

    for marker, name in required_sections:
        if marker not in content:
            result.add_error(f"Missing required section: {name}")

    # Extract and validate skill name
    name_match = re.search(r'### Name\s*\n`([^`]+)`', content)
    if name_match:
        skill_name = name_match.group(1)

        # Check naming convention
        if not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', skill_name) and len(skill_name) > 1:
            result.add_error(f"Invalid skill name '{skill_name}': must be hyphen-case (lowercase, digits, hyphens)")

        if len(skill_name) > 40:
            result.add_error(f"Skill name too long: {len(skill_name)} chars (max 40)")

        if '--' in skill_name:
            result.add_error("Skill name cannot contain consecutive hyphens")
    else:
        result.add_error("Could not find skill name in ### Name section")

    # Check description
    desc_match = re.search(r'### Description \(for SKILL\.md frontmatter\)\s*\n(.+?)(?=\n###|\n---)', content, re.DOTALL)
    if desc_match:
        description = desc_match.group(1).strip()
        if len(description) < 10:
            result.add_warning("Description is very short (< 10 chars)")
        if len(description) > 500:
            result.add_warning("Description is long (> 500 chars), consider shortening")
    else:
        result.add_error("Could not find description section")

    # Check status markers
    status_markers = ['PENDING APPROVAL', 'APPROVED', 'REJECTED']
    has_status = any(f'[x] {marker}' in content or f'[X] {marker}' in content for marker in status_markers)
    if not has_status:
        result.add_warning("No status marker is checked (PENDING APPROVAL, APPROVED, or REJECTED)")

    # Check inputs table
    if '### Inputs' in content:
        inputs_section = re.search(r'### Inputs\s*\n(.*?)(?=\n###|\n---)', content, re.DOTALL)
        if inputs_section:
            table_content = inputs_section.group(1)
            if '|' not in table_content and 'No input' not in table_content:
                result.add_warning("Inputs section exists but no table found")

    # Check outputs table
    if '### Output Fields' in content:
        outputs_section = re.search(r'### Output Fields\s*\n(.*?)(?=\n---)', content, re.DOTALL)
        if outputs_section:
            table_content = outputs_section.group(1)
            if '|' not in table_content and 'Output format' not in table_content:
                result.add_warning("Output Fields section exists but no table found")

    # Check dependencies
    if '```toml' not in content:
        result.add_warning("No Cargo.toml dependencies block found")

    # Check generated files structure
    if '```' in content:
        files_match = re.search(r'## Generated Files\s*\n```\s*\n(.*?)```', content, re.DOTALL)
        if files_match:
            files_content = files_match.group(1)
            required_files = ['SKILL.md', 'scripts/', 'build.sh', 'run.sh', 'rust/', 'main.rs', 'Cargo.toml']
            for file in required_files:
                if file not in files_content:
                    result.add_warning(f"Generated files structure may be missing: {file}")

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_spec.py <SPEC.md>")
        print()
        print("Validate SPEC.md format and completeness.")
        print()
        print("Checks:")
        print("  - Required sections present")
        print("  - Skill name follows conventions")
        print("  - Description is adequate")
        print("  - Input/output sections defined")
        print("  - Technical design present")
        sys.exit(1)

    spec_path = sys.argv[1]

    print(f"Validating: {spec_path}")
    print()

    result = validate_spec(spec_path)
    result.print_results()

    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
