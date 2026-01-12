---
name: rust-skill-creator
description: Generate Rust-based skills that compile and run Rust applications. Use when users want to create skills that leverage Rust for HTTP API clients, CLI tools, system utilities, or any task requiring compiled performance. Triggers on requests like "create a rust skill", "make a skill to query [API]", "build a skill that uses rust", or "I want a skill that calls [service]".
---

# Rust Skill Creator

Generate skills that contain Rust source code with build and run scripts. The generated skills use Claude for orchestration while Rust handles the core logic.

## Workflow

Follow these phases in order:

### Phase 1: Gather Requirements

Run the requirements gathering script to collect user needs:

```bash
scripts/gather_requirements.py --output /tmp/requirements.json
```

The script collects:
- Skill name and purpose
- Input parameters (name, type, required)
- Output format and fields
- API endpoints (if applicable)
- Authentication needs
- Error handling requirements

### Phase 2: Generate SPEC.md

Create a specification document from the requirements:

```bash
scripts/generate_spec.py --requirements /tmp/requirements.json --output /tmp/SPEC.md
```

The SPEC.md contains:
- Skill overview and description
- Input/output specifications
- Technical design (Rust app, dependencies, API details)
- Generated file structure

### Phase 3: User Approval

**STOP and wait for user approval.**

Present the SPEC.md to the user. They must respond with:
- "APPROVED" - proceed to skill creation
- Modification requests - update SPEC.md and re-present
- "REJECTED" - abort skill creation

Do not proceed to Phase 4 until the user explicitly approves.

### Phase 4: Create Skill

Generate the complete skill from the approved SPEC:

```bash
scripts/create_skill.py --spec /tmp/SPEC.md --output ~/.claude/skills
```

This creates:
- SKILL.md with proper frontmatter
- scripts/build.sh - compiles Rust code
- scripts/run.sh - executes compiled binary
- rust/Cargo.toml - dependencies
- rust/src/main.rs - entry point

### Phase 5: Validate

The create_skill.py script automatically:
1. Runs `cargo build --release`
2. Parses any compilation errors
3. Attempts auto-fixes (up to 3 attempts)
4. Reports success or remaining errors

## Output Location

Default: `~/.claude/skills/<skill-name>/`

Override with `--output` flag in create_skill.py.

## Generated Skill Structure

```
skill-name/
├── SKILL.md              # Skill definition
├── scripts/
│   ├── build.sh          # Compiles Rust
│   └── run.sh            # Runs compiled binary
└── rust/
    ├── Cargo.toml        # Dependencies
    └── src/
        └── main.rs       # Entry point
```

## Resources

### References

- `references/rust-patterns.md` - Common Rust patterns (HTTP with reqwest, JSON with serde, CLI args, async with tokio)
- `references/error-handling.md` - Auto-fix strategies for compilation errors

### Templates

Templates in `assets/templates/` are used by the Python scripts:
- SPEC_TEMPLATE.md - Specification document structure
- SKILL_TEMPLATE.md - Generated skill's SKILL.md
- main_template.rs - Rust entry point boilerplate
- cargo_template.toml - Cargo.toml with common dependencies
- build_template.sh - Build script
- run_template.sh - Run script

## Example: Weather Query Skill

User request: "I want a skill to query weather for a given location"

1. **Requirements gathered:**
   - Name: weather-query
   - Input: location (String, required)
   - Output: JSON weather data
   - API: https://api.openweathermap.org/data/2.5/weather
   - Auth: API key in environment variable

2. **SPEC.md generated** with full technical design

3. **User approves** the specification

4. **Skill created** at `~/.claude/skills/weather-query/`:
   - main.rs uses reqwest to call the weather API
   - Cargo.toml includes reqwest, serde, tokio
   - build.sh compiles the binary
   - run.sh executes with location argument

5. **Usage:**
   ```bash
   cd ~/.claude/skills/weather-query
   scripts/build.sh
   scripts/run.sh "Tokyo"
   ```
