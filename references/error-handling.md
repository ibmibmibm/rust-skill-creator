# Rust Compilation Error Auto-Fix Guide

Common compilation errors and their solutions for auto-fixing during skill creation.

## Error Categories

### 1. Missing Imports

**Pattern**: `cannot find type|trait|function|macro`

**Common Cases and Fixes**:

| Error Message | Fix |
|--------------|-----|
| `cannot find type 'Error'` | Add `use std::error::Error;` |
| `cannot find derive macro 'Serialize'` | Add `use serde::{Serialize, Deserialize};` |
| `cannot find derive macro 'Deserialize'` | Add `use serde::{Serialize, Deserialize};` |
| `cannot find type 'HashMap'` | Add `use std::collections::HashMap;` |
| `cannot find type 'Vec'` | (Built-in, check for typo) |
| `cannot find function 'env'` | Add `use std::env;` |

**Auto-Fix Strategy**:
1. Parse error message for type/trait/function name
2. Look up in known imports map
3. Add import statement at top of file

### 2. Missing Dependencies

**Pattern**: `unresolved import`, `can't find crate`

**Common Cases and Fixes**:

| Error Message | Cargo.toml Addition |
|--------------|---------------------|
| `unresolved import 'reqwest'` | `reqwest = { version = "0.12", features = ["json"] }` |
| `unresolved import 'serde'` | `serde = { version = "1", features = ["derive"] }` |
| `unresolved import 'serde_json'` | `serde_json = "1"` |
| `unresolved import 'tokio'` | `tokio = { version = "1", features = ["full"] }` |
| `unresolved import 'chrono'` | `chrono = "0.4"` |
| `unresolved import 'regex'` | `regex = "1"` |
| `unresolved import 'clap'` | `clap = { version = "4", features = ["derive"] }` |

**Auto-Fix Strategy**:
1. Extract crate name from error
2. Look up in known crates map
3. Add to [dependencies] in Cargo.toml

### 3. Type Mismatches

**Pattern**: `expected X, found Y`

**Common Cases and Fixes**:

| Error | Solution |
|-------|----------|
| `expected String, found &str` | Add `.to_string()` |
| `expected &str, found String` | Add `&` or `.as_str()` |
| `expected i32, found i64` | Add `as i32` cast |
| `expected Option<T>, found T` | Wrap in `Some()` |
| `expected T, found Option<T>` | Add `.unwrap()` or use `?` |

**Auto-Fix Strategy**:
1. Parse expected and found types
2. Determine conversion method
3. Apply conversion at error location

### 4. Async/Await Issues

**Pattern**: `async fn main`, `cannot find attribute 'tokio'`

**Fixes**:

| Error | Solution |
|-------|----------|
| `main function is not allowed to be async` | Add `#[tokio::main]` attribute |
| `cannot find attribute 'tokio'` | Add tokio dependency with full features |
| `future cannot be sent between threads safely` | Add `Send` bound or restructure |
| `.await` used outside async fn | Mark function as `async` |

**Auto-Fix Strategy**:
1. Check for tokio in dependencies
2. Add `#[tokio::main]` attribute if missing
3. Ensure tokio has "full" features

### 5. Borrow Checker Issues

**Pattern**: `cannot move out of`, `value borrowed here`, `does not live long enough`

**Common Fixes**:

| Error Pattern | Potential Fix |
|--------------|---------------|
| `cannot move out of borrowed content` | Add `.clone()` |
| `value borrowed here after move` | Clone before move, or restructure |
| `does not live long enough` | Extend lifetime, clone, or restructure |
| `cannot borrow as mutable` | Change to `let mut` |

**Auto-Fix Strategy** (conservative):
1. For "cannot move" errors: try adding `.clone()`
2. For mutation errors: add `mut` keyword
3. For complex cases: report to user

### 6. Method Not Found

**Pattern**: `no method named X found`

**Common Cases**:

| Error | Check |
|-------|-------|
| `no method named 'json'` | Reqwest needs "json" feature |
| `no method named 'await'` | Function not async, or not in async context |
| `no method named 'parse'` | Check type implements FromStr |

**Auto-Fix Strategy**:
1. Check if it's a feature flag issue
2. Update Cargo.toml features if needed

## Auto-Fix Algorithm

```python
def auto_fix_errors(error_output: str, main_rs: str, cargo_toml: str) -> tuple[str, str]:
    """
    Parse compilation errors and apply fixes.

    Returns:
        (fixed_main_rs, fixed_cargo_toml)
    """

    # 1. Parse errors into structured format
    errors = parse_cargo_errors(error_output)

    for error in errors:
        # 2. Categorize error
        category = categorize_error(error.message)

        # 3. Apply category-specific fix
        if category == "missing_import":
            import_stmt = lookup_import(error.missing_item)
            if import_stmt:
                main_rs = add_import(main_rs, import_stmt)

        elif category == "missing_dependency":
            dep = lookup_dependency(error.crate_name)
            if dep:
                cargo_toml = add_dependency(cargo_toml, dep)

        elif category == "type_mismatch":
            fix = suggest_conversion(error.expected, error.found)
            if fix:
                main_rs = apply_conversion(main_rs, error.location, fix)

        elif category == "async_issue":
            if "tokio" not in cargo_toml:
                cargo_toml = add_tokio_dependency(cargo_toml)
            if "#[tokio::main]" not in main_rs:
                main_rs = add_tokio_main_attribute(main_rs)

    return (main_rs, cargo_toml)
```

## Retry Logic

```
Attempt 1: Initial compilation
  └─ Success? → Done
  └─ Failure? → Parse errors, categorize, apply safe fixes

Attempt 2: Recompile after fixes
  └─ Success? → Done
  └─ Failure? → Parse new errors, apply additional fixes

Attempt 3: Final recompile
  └─ Success? → Done
  └─ Failure? → Report to user with suggestions
```

## When Manual Intervention Is Required

The following error types should not be auto-fixed:

1. **Logic Errors** - Infinite loops, wrong algorithms
2. **Complex Lifetime Issues** - May require structural changes
3. **Missing External Dependencies** - APIs, system libraries
4. **Security Issues** - Unsafe code, credential handling
5. **Multiple Conflicting Errors** - Fix one may break others

For these cases:
1. Report the error clearly to the user
2. Suggest possible manual fixes
3. Point to relevant documentation
4. Offer to regenerate with different requirements

## Testing Auto-Fixes

Before applying a fix, verify:
1. The fix doesn't introduce new errors
2. The fix is minimal and targeted
3. The fix preserves intended behavior

After applying fixes:
1. Recompile to verify success
2. If still failing, try alternative fixes
3. Report remaining issues with context
