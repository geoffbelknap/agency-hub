# Agency Hub API Surface

The standalone `agency-hub` service is the reference registry and assurance
authority for Agency packages. The initial API surface is intentionally
read-only and focused on metadata needed by Agency consumers.

## Goals

- expose publisher identity records
- expose artifact assurance statements
- expose hub-level metadata and trust-domain identity
- keep the first surface simple enough to implement on top of static hub data

## Initial Endpoints

### `GET /v1/hubs/{hub}/metadata`

Returns hub identity and policy metadata, including:

- `hub_id`
- `display_name`
- `policy_version`
- `publisher_verification_methods`
- `recognized_statement_types`

### `GET /v1/hubs/{hub}/publishers/{publisher_id}`

Returns the verified publisher record for an individual or organization.

### `GET /v1/hubs/{hub}/artifacts/{kind}/{name}/{version}/assurance`

Returns the assurance statements currently attached to an artifact version.

The first response shape should include:

- artifact identity
- issuer hub identity
- statement type
- result
- review scope
- reviewer type
- policy version
- timestamp
- evidence references when available

## Notes

- This surface is descriptive, not authoritative for local install policy on
  its own. `agency` still applies local policy over approved hubs and
  recognized assurance statements.
- The API should model multi-hub trust domains even while `agency-hub` is the
  only official authority at first.
