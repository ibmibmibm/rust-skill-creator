---
name: {skill_name}
description: {description}
---

# {skill_title}

{purpose}

## Usage

### Build

Compile the Rust application:

```bash
scripts/build.sh
```

### Run

Execute with arguments:

```bash
scripts/run.sh {usage_args}
```

## Input Parameters

{input_docs}

## Output

Returns {output_format} formatted output.

{output_docs}

## Example

```bash
# Build the skill
scripts/build.sh

# Run with example input
scripts/run.sh {example_args}
```

## Error Handling

The skill handles the following error cases:
{error_docs}
