# Hub Assurance Schema

This document defines the initial machine-readable metadata added for the Agency Hub assurance model.

## Publisher Records

Publisher records live under `publishers/` as JSON documents. They bind a publishing principal to a verified identity.

Required fields:

- `publisher_id`
- `kind`
- `display_name`
- `verification`

## Assurance Statements

Assurance statements are structured, scoped claims about a specific artifact version and review scope.

Required fields:

- `artifact`
- `issuer`
- `statement_type`
- `result`
- `review_scope`
- `reviewer_type`
- `policy_version`
- `timestamp`

## Initial ASK Outcomes

The initial ASK review outcome model is:

- `ASK-Pass`
- `ASK-Partial`
- `ASK-Fail`

These outcomes are always scoped. They do not imply universal safety or runtime-context compliance.
