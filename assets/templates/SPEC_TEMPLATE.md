# Skill Specification: {skill_title}

Generated: {timestamp}

## Status

- [x] PENDING APPROVAL
- [ ] APPROVED
- [ ] REJECTED

---

## Overview

{description}

**Purpose**: {purpose}

---

## User Requirements

{user_requirements}

---

## Skill Details

### Name
`{skill_name}`

### Description (for SKILL.md frontmatter)
{description}

### Trigger Scenarios
{trigger_scenarios}

---

## Input/Output

### Inputs

{inputs_table}

### Output Format
**{output_format}**

### Output Fields

{outputs_table}

---

## Technical Design

### Rust Application

- **Binary Name**: `{skill_name}`
- **Entry Point**: `main.rs` with async main function
- **Runtime**: tokio async runtime

### Dependencies

```toml
[dependencies]
{dependencies}
```

### API/External Services

{api_section}

### Error Handling

{error_handling}

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
