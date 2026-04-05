# Contributing to Agency Hub

Agency Hub is the package manager for Agency. Anyone can create and publish components — connectors, services, presets, missions, and packs.

## Quick Start

```bash
# 1. Scaffold a new component
agency hub create connector my-connector

# 2. Edit the YAML
nano my-connector/connector.yaml

# 3. Validate it
agency hub audit my-connector

# 4. Publish to the hub
agency hub publish my-connector
```

## Component Types

| Kind | File | What it does |
|------|------|-------------|
| **connector** | `connector.yaml` | Brings external data into Agency — polls APIs, receives webhooks, watches channels |
| **service** | `service.yaml` | Defines an API credential and tools agents can use |
| **preset** | `preset.yaml` | Agent configuration — model tier, identity, hard limits, escalation |
| **mission** | `mission.yaml` | Standing instructions for an agent — triggers, budget, success criteria |
| **pack** | `pack.yaml` | Bundle — deploys a team with agents, channels, missions, and dependencies |

## Directory Structure

Each component is a directory containing a YAML file and optional supporting files:

```
connectors/
  my-connector/
    connector.yaml    # required — the component definition
    README.md         # recommended — usage instructions
    metadata.yaml     # auto-generated — stamped by CI on merge
```

## Required Fields

Every component YAML must have:

```yaml
kind: connector          # must match the parent directory type
name: my-connector       # unique within the hub
version: "0.1.0"         # semver — bump on every change
description: >           # one-line description
  What this component does.
author: your-name        # who made it
license: MIT             # SPDX identifier
```

## Connector Guide

Connectors are the most common component. A connector polls an external API, writes data to the knowledge graph, and optionally routes work items to agents.

### Minimal Connector

```yaml
kind: connector
name: my-connector
version: "0.1.0"
description: Polls My API for events
author: your-name
license: MIT

requires:
  credentials:
    - name: MY_API_KEY
      description: API key from my-service.com
      type: secret
      scope: service-grant
      grant_name: my-service
  egress_domains:
    - api.my-service.com
  services:
    - my-service

source:
  type: poll
  url: "https://api.my-service.com/v1/events"
  method: GET
  interval: 5m
  response_key: "$.data"

graph_ingest:
  - nodes:
      - kind: Event
        label: "{{payload.id}}"
        properties:
          event_type: "{{payload.type}}"
          timestamp: "{{payload.created_at}}"
          source: "my-connector"
```

### Key Concepts

**Source types:**
- `poll` — periodically fetch from a URL
- `webhook` — receive POSTed events
- `schedule` — cron-triggered execution
- `channel-watch` — watch a Slack/comms channel

**Graph ingest:** Templates use `{{payload.field}}` syntax (Jinja2 sandboxed). Nodes are upserted by label — same label = update, not duplicate.

**Routes:** Direct work items to agents, missions, or channels:
```yaml
routes:
  - match:
      severity: [high, critical]
    target:
      mission: my-triage-mission
  - match:
      severity: [medium]
    target:
      channel: findings
```

**Deduplication:** Set `dedup_key` to a unique field to prevent duplicate processing:
```yaml
source:
  dedup_key: "event_id"
```

### Credential Requirements

Connectors declare what credentials they need in the `requires` block. When an operator installs the connector, they see exactly what access is required:

```yaml
requires:
  credentials:
    - name: MY_API_KEY
      description: API key (read-only scope sufficient)
      type: secret
      scope: service-grant
      grant_name: my-service
      setup_url: "https://my-service.com/settings/api"
```

**Important:** The `grant_name` must reference a service definition. The credential is only injected into requests to that service's configured domains — it cannot be sent elsewhere.

### Egress Domains

Declare every domain your connector accesses:

```yaml
requires:
  egress_domains:
    - api.my-service.com
```

These are shown to the operator during install. Undeclared domains will be blocked by the egress proxy.

**Never** use IP addresses, metadata endpoints (169.254.x.x), or wildcard domains.

## Service Guide

A service defines API credentials and tools that agents can use.

```yaml
service: my-service
display_name: My Service API
api_base: "https://api.my-service.com"
description: Query and manage resources in My Service.
credential:
  env_var: MY_API_KEY
  header: Authorization
  format: "Bearer {key}"
  scoped_prefix: agency-scoped-my-service

tools:
  - name: search_events
    description: Search for events by query
    method: GET
    path: /v1/events/search
    parameters:
      - name: query
        description: Search query
        required: true
```

## Preset Guide

Presets define agent configurations — model tier, identity, tools, hard limits.

```yaml
name: my-preset
type: standard
model_tier: standard     # frontier, standard, fast, mini
description: Agent for processing My Service events

tools:
  - python3
  - curl
capabilities:
  - file_read

identity:
  purpose: Process events from My Service
  body: |
    You process events and post findings to the findings channel.

hard_limits:
  - rule: "Never modify external systems — report only"
    reason: "Read-only integration"

escalation:
  always_escalate:
    - "Any event indicating data breach"
  flag_before_proceeding: []
```

## Mission Guide

Missions are standing instructions for agents.

```yaml
kind: mission
name: my-triage
version: "0.1.0"
description: Triage events from My Service

instructions: |
  When you receive an event, assess its severity and post
  a finding to the findings channel.

triggers:
  - source: connector
    connector: my-connector
    event_type: event_created

budget:
  per_task: 0.10
  daily: 1.00
cost_mode: frugal
```

## Pack Guide

Packs bundle everything together — one `agency hub deploy` creates the full setup.

```yaml
kind: pack
name: my-ops
version: "0.1.0"
description: My Service operations pack

requires:
  connectors: [my-connector]
  services: [my-service]
  presets: [my-preset]
  missions: [my-triage]

team:
  name: my-ops
  agents:
    - name: my-agent
      preset: my-preset
  channels:
    - name: findings
      topic: Findings and observations

mission_assignments:
  - mission: my-triage
    agent: my-agent
```

## Validation

Before submitting, validate your component:

```bash
agency hub audit my-connector
```

Checks:
- Required fields present
- Kind matches filename
- Description not empty
- Semver version format
- Template safety (no dunder access)
- No blocked egress domains (metadata endpoints)
- README exists

## Publishing

```bash
agency hub publish my-connector
```

This:
1. Copies your component to the hub cache
2. Creates a branch
3. Commits and pushes
4. Opens a PR via `gh` CLI

The review bot runs automatically on the PR and checks:
- Schema validation
- Credential-domain consistency
- Template safety scan
- Version bump validation
- Auto-approves routine changes
- Flags security surface changes for human review

## Review Criteria

**Auto-approved** (routine changes):
- Version bumps with no security surface change
- Description or documentation updates
- Property additions to existing graph_ingest nodes

**Flagged for human review:**
- New credentials or credential scope changes
- New egress domains
- MCP tool changes (added, removed, or path changed)
- New connectors (always reviewed on first submit)

## Versioning

Use [semver](https://semver.org/):
- **MAJOR** — breaking changes (renamed fields, removed routes)
- **MINOR** — new features (added graph_ingest rules, new tools)
- **PATCH** — fixes (template corrections, description updates)

Bump the version on every change. The review bot rejects PRs that don't bump.

## Third-Party Sources

You can host your own hub source:

```bash
# Users add your source
agency hub add-source my-org https://github.com/my-org/agency-hub.git

# Then install from it
agency hub install my-connector --source my-org
```

Your hub repo follows the same directory structure. Add a review bot workflow for quality control (see `.github/workflows/review-bot.yml` in this repo for reference).

## Code of Conduct

- Components must not exfiltrate credentials (the architecture prevents this, but don't try)
- Components must not access domains beyond what's declared in `egress_domains`
- Components must not inject instructions into agents via graph_ingest (XPIA)
- Components must declare all credential requirements honestly
- Components must be useful — no placeholder or spam submissions

## How Components Are Published

When your PR is merged to main, components are automatically:

1. **Metadata stamped** — version, build hash, and timestamp added to `metadata.yaml`
2. **Published to GHCR** — pushed as OCI artifacts to `ghcr.io/geoffbelknap/agency-hub/{kind}/{name}:{version}`
3. **Signed** — cosign keyless signing with GitHub Actions OIDC identity

You don't need to interact with the OCI registry directly. Just submit your YAML, pass review, and CI handles distribution.

Users install your component with:

```bash
agency hub update
agency hub install <name>
```
