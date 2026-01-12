# Rust Skill Creator

A Claude Code skill that generates Rust-based skills for Claude. Create HTTP API clients, CLI tools, system utilities, or any task requiring compiled performance.

## Features

- **Interactive Requirements Gathering**: Collects skill specifications through guided prompts
- **Specification-Driven Generation**: Creates detailed SPEC.md for user approval before building
- **Complete Skill Generation**: Produces fully-functional Rust skills with build/run scripts
- **Automatic Compilation**: Builds generated skills with auto-fix for common errors
- **Template-Based**: Customizable templates for all generated files

## Project Structure

```
rust-skill-creator/
├── SKILL.md                  # Skill definition with workflow documentation
├── LICENSE.txt               # Apache License 2.0
├── scripts/
│   ├── gather_requirements.py    # Phase 1: Collect user requirements
│   ├── generate_spec.py          # Phase 2: Generate SPEC.md
│   ├── create_skill.py           # Phase 4: Generate complete skill
│   └── validate_spec.py          # Validate SPEC.md format
├── assets/
│   └── templates/
│       ├── SPEC_TEMPLATE.md      # Specification document template
│       ├── SKILL_TEMPLATE.md     # Generated skill's SKILL.md template
│       ├── main_template.rs      # Rust entry point template
│       ├── cargo_template.toml   # Cargo.toml template
│       ├── build_template.sh     # Build script template
│       └── run_template.sh       # Run script template
└── references/
    ├── rust-patterns.md          # Common Rust patterns (HTTP, JSON, CLI, async)
    └── error-handling.md         # Compilation error auto-fix strategies
```

## Workflow

The skill generation follows a 5-phase process:

### Phase 1: Gather Requirements

Collect user needs including:
- Skill name and purpose
- Input parameters (name, type, required)
- Output format and fields
- API endpoints and authentication
- Error handling requirements

### Phase 2: Generate SPEC.md

Create a specification document containing:
- Skill overview and description
- Input/output specifications
- Technical design (dependencies, API details)
- Generated file structure

### Phase 3: User Approval

**Required checkpoint.** User must explicitly approve the SPEC.md before proceeding:
- "APPROVED" - continue to skill creation
- Modification requests - update and re-present
- "REJECTED" - abort

### Phase 4: Create Skill

Generate the complete skill:
- `SKILL.md` with proper frontmatter
- `scripts/build.sh` - compiles Rust code
- `scripts/run.sh` - executes compiled binary
- `rust/Cargo.toml` - package dependencies
- `rust/src/main.rs` - entry point

### Phase 5: Validate

Automatic compilation with:
- Runs `cargo build --release`
- Parses compilation errors
- Attempts auto-fixes (up to 3 attempts)
- Reports success or remaining errors

## Generated Skill Structure

Each generated skill has this structure:

```
<skill-name>/
├── SKILL.md              # Skill definition
├── scripts/
│   ├── build.sh          # Compiles Rust (cargo build --release)
│   └── run.sh            # Executes compiled binary
└── rust/
    ├── Cargo.toml        # Package and dependencies
    └── src/
        └── main.rs       # Async main entry point
```

Default output location: `~/.claude/skills/<skill-name>/`

## Example

User request: "Create a skill to query weather for a location"

**Generated skill:**
- `main.rs` uses reqwest to call weather API
- `Cargo.toml` includes reqwest, serde, tokio
- `build.sh` compiles the binary
- `run.sh` executes with location argument

**Usage:**
```bash
cd ~/.claude/skills/weather-query
scripts/build.sh
scripts/run.sh "Tokyo"
```

## Requirements

- Python 3.12+
- Rust toolchain (cargo, rustc)

## License

Apache License 2.0 - see [LICENSE.txt](LICENSE.txt)
