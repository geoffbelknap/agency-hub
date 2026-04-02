---
name: code-review
description: Review code changes for correctness, style, and security issues
version: "1.0"
allowed-tools:
  - read_file
  - list_directory
  - search_files
  - execute_command
---

# Code Review

You are performing a code review. Follow this workflow:

## Process

1. **Understand the change**: Read the diff or changed files to understand what was modified and why.
2. **Check correctness**: Verify the logic is sound. Look for off-by-one errors, null/undefined handling, and edge cases.
3. **Check security**: Look for injection vulnerabilities (SQL, command, XSS), hardcoded secrets, and unsafe deserialization.
4. **Check style**: Verify naming conventions, consistent formatting, and appropriate use of language idioms.
5. **Check tests**: Confirm tests exist for new functionality and edge cases are covered.

## Output format

For each finding, report:
- **File and line**: Where the issue is
- **Severity**: critical / warning / suggestion
- **Description**: What the issue is and why it matters
- **Suggestion**: How to fix it

Summarize with a pass/fail recommendation and list of action items.
