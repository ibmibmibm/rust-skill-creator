#!/usr/bin/env python3
"""
Requirements Gatherer - Collect user requirements for Rust skill creation.

Usage:
    gather_requirements.py --output <requirements.json>

This script is designed to be read by Claude, who will use the structure
to interactively gather requirements from the user and save them to JSON.
"""

import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class InputParam:
    """Represents an input parameter for the skill."""
    name: str
    param_type: str  # String, i32, f64, bool, etc.
    required: bool
    description: str
    default: Optional[str] = None


@dataclass
class OutputField:
    """Represents a field in the output."""
    name: str
    field_type: str
    description: str


@dataclass
class ApiConfig:
    """API configuration for HTTP-based skills."""
    endpoint: str
    method: str  # GET, POST, PUT, DELETE
    auth_type: Optional[str] = None  # None, api_key, bearer, basic
    auth_env_var: Optional[str] = None  # Environment variable name for auth
    headers: Optional[dict] = None
    rate_limit: Optional[str] = None


@dataclass
class Requirements:
    """Complete requirements for a Rust skill."""
    skill_name: str
    description: str
    purpose: str
    inputs: list[InputParam]
    output_format: str  # json, text, file
    output_fields: list[OutputField]
    api_config: Optional[ApiConfig] = None
    error_scenarios: Optional[list[str]] = None
    additional_crates: Optional[list[str]] = None
    notes: Optional[str] = None


def validate_skill_name(name: str) -> tuple[bool, str]:
    """
    Validate skill name follows conventions.

    Returns:
        (is_valid, error_message)
    """
    if not name:
        return False, "Skill name cannot be empty"

    if len(name) > 40:
        return False, "Skill name must be 40 characters or less"

    if not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', name) and len(name) > 1:
        return False, "Skill name must be hyphen-case (lowercase letters, digits, hyphens only)"

    if '--' in name:
        return False, "Skill name cannot contain consecutive hyphens"

    return True, ""


def validate_requirements(req: Requirements) -> tuple[bool, list[str]]:
    """
    Validate complete requirements.

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    # Validate skill name
    is_valid, err = validate_skill_name(req.skill_name)
    if not is_valid:
        errors.append(f"Invalid skill name: {err}")

    # Validate description
    if not req.description or len(req.description) < 10:
        errors.append("Description must be at least 10 characters")

    if len(req.description) > 500:
        errors.append("Description must be 500 characters or less")

    # Validate purpose
    if not req.purpose:
        errors.append("Purpose is required")

    # Validate inputs
    if not req.inputs:
        errors.append("At least one input parameter is required")

    for inp in req.inputs:
        if not inp.name:
            errors.append("Input parameter name is required")
        if not inp.param_type:
            errors.append(f"Input parameter '{inp.name}' needs a type")

    # Validate output
    if req.output_format not in ['json', 'text', 'file']:
        errors.append("Output format must be 'json', 'text', or 'file'")

    # Validate API config if present
    if req.api_config:
        if not req.api_config.endpoint:
            errors.append("API endpoint is required when api_config is specified")
        if req.api_config.method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
            errors.append("API method must be GET, POST, PUT, DELETE, or PATCH")

    return len(errors) == 0, errors


def requirements_to_dict(req: Requirements) -> dict:
    """Convert Requirements to a serializable dictionary."""
    result = {
        'skill_name': req.skill_name,
        'description': req.description,
        'purpose': req.purpose,
        'inputs': [asdict(inp) for inp in req.inputs],
        'output_format': req.output_format,
        'output_fields': [asdict(field) for field in req.output_fields],
    }

    if req.api_config:
        result['api_config'] = asdict(req.api_config)

    if req.error_scenarios:
        result['error_scenarios'] = req.error_scenarios

    if req.additional_crates:
        result['additional_crates'] = req.additional_crates

    if req.notes:
        result['notes'] = req.notes

    return result


def save_requirements(req: Requirements, output_path: str) -> bool:
    """
    Save requirements to JSON file.

    Returns:
        True if successful, False otherwise.
    """
    try:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        data = requirements_to_dict(req)

        with open(output, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Requirements saved to: {output}")
        return True
    except Exception as e:
        print(f"Error saving requirements: {e}")
        return False


# ============================================================================
# GATHERING INSTRUCTIONS FOR CLAUDE
# ============================================================================
#
# When this script is used, Claude should gather the following information
# from the user through interactive conversation:
#
# 1. BASIC INFO
#    - skill_name: What should the skill be called? (hyphen-case, e.g., "weather-query")
#    - description: One-line description for SKILL.md frontmatter
#    - purpose: What problem does this skill solve? What's the main use case?
#
# 2. INPUT PARAMETERS
#    For each input, collect:
#    - name: Parameter name (e.g., "location", "api_key")
#    - param_type: Rust type (String, i32, f64, bool, Vec<String>)
#    - required: Is this required or optional?
#    - description: What is this parameter for?
#    - default: Default value if optional
#
# 3. OUTPUT SPECIFICATION
#    - output_format: How should results be returned? (json/text/file)
#    - output_fields: What fields/data will be in the output?
#      - name: Field name
#      - field_type: Data type
#      - description: What this field contains
#
# 4. API CONFIGURATION (if applicable)
#    - endpoint: Full API URL (can include placeholders like {location})
#    - method: HTTP method (GET, POST, etc.)
#    - auth_type: How to authenticate (api_key, bearer, basic, or none)
#    - auth_env_var: Environment variable name for auth credentials
#    - headers: Any custom headers needed
#    - rate_limit: Known rate limits (for documentation)
#
# 5. ERROR SCENARIOS
#    List common error cases to handle:
#    - Network errors
#    - Invalid input
#    - API errors (rate limit, auth failure, not found)
#    - Parse errors
#
# 6. ADDITIONAL CRATES (optional)
#    Any extra Rust crates needed beyond the defaults:
#    - Default: tokio, reqwest, serde, serde_json
#    - Examples: clap (CLI), chrono (dates), regex, etc.
#
# 7. NOTES (optional)
#    Any additional context or requirements
#
# After gathering, validate with validate_requirements() and save with
# save_requirements().
# ============================================================================


def main():
    if len(sys.argv) < 3 or sys.argv[1] != '--output':
        print("Usage: gather_requirements.py --output <requirements.json>")
        print()
        print("This script defines the structure for gathering requirements.")
        print("Claude will read this script and use the defined data structures")
        print("to interactively collect requirements from the user.")
        print()
        print("Required information:")
        print("  - Skill name (hyphen-case, max 40 chars)")
        print("  - Description and purpose")
        print("  - Input parameters (name, type, required, description)")
        print("  - Output format and fields")
        print("  - API configuration (if HTTP-based)")
        print("  - Error scenarios to handle")
        print("  - Additional Rust crates needed")
        sys.exit(1)

    output_path = sys.argv[2]
    print(f"Output will be saved to: {output_path}")
    print()
    print("Claude should now gather requirements interactively and call")
    print("save_requirements() with the collected data.")


if __name__ == "__main__":
    main()
