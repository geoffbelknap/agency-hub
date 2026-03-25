# Agency Hub

Default component registry for the [Agency platform](https://github.com/geoffbelknap/agency).

## Structure

```
packs/          Declarative team compositions (pack.yaml + connectors)
connectors/     External system bindings (webhook, poll, schedule, channel-watch)
services/       Service definitions (Slack, Jira)
presets/        Agent preset definitions
skills/         Agent skill packages
policies/       Policy templates
workspaces/     Workspace definitions
pricing/        LLM model pricing (synced to routing.yaml by agency hub update)
```

## Hub-Managed Files

`agency hub update` syncs these files from the hub into `~/.agency/`. They are overwritten on every update — do not edit them directly.

| File | Location | Operator customization |
|------|----------|----------------------|
| `routing.yaml` | `~/.agency/infrastructure/routing.yaml` | Use `routing.local.yaml` for custom providers, models, pricing |
| Service definitions | `~/.agency/registry/services/*.yaml` | Create new files — don't edit hub-managed ones |
| Base ontology | `~/.agency/knowledge/base-ontology.yaml` | Add files to `~/.agency/knowledge/ontology.d/` |

## Usage

Add this hub source to `~/.agency/config.yaml`:

```yaml
hub:
  sources:
    - name: official
      url: https://github.com/geoffbelknap/agency-hub.git
      branch: main
```

Then:

```bash
agency hub update          # sync hub cache
agency hub search          # browse available components
agency hub install <name>  # install a component + dependencies
```

## Available Packs

### `slack-ops`

Ops team that monitors a Slack channel for requests, incidents, and evaluation
tasks. Agents read message threads, investigate, and post findings back to
Slack. Bidirectional — Slack is both the work source and the output channel.

**Required environment variables:**
- `SLACK_BOT_TOKEN` — Bot User OAuth Token (`xoxb-...`)
- `SLACK_CHANNEL_ID` — ID of the Slack channel to monitor

**Slack app scopes:**
`channels:history`, `channels:read`, `chat:write`, `reactions:read`,
`reactions:write`, `users:read`, `files:read`, `files:write`, `search:read`

**Bot user ID placeholder:** The `slack-ops` connector routes `@mention`
messages using a regex pattern. Replace `U0YOURBOTUSERID` in
`connectors/slack-ops/connector.yaml` with your bot's Slack user ID (find it
in your Slack App settings under *OAuth & Permissions → Bot User ID*, or call
`https://slack.com/api/auth.test` with your token).

```bash
agency hub install slack-ops
```

---

### `jira-ops`

Ops team that owns a Jira Cloud queue. Polls for new and updated issues, routes
by issue type and priority, and posts findings back to tickets.

**Required environment variables:**
- `JIRA_API_TOKEN` — Base64-encoded `email@example.com:api-token`
- `JIRA_DOMAIN` — Your Jira subdomain (e.g. `mycompany` for `mycompany.atlassian.net`)
- `JIRA_PROJECT_KEY` — Project key to monitor (e.g. `OPS`)

**Getting a Jira API token:** <https://id.atlassian.com/manage-profile/security/api-tokens>

```bash
agency hub install jira-ops
```

---

### `red-team`

Red team coordination pack for **authorized** security testing. A coordinator
delegates reconnaissance and exploitation tasks to specialist agents. Findings
are contributed to the organizational knowledge graph so prior work compounds
across engagements.

The pack ships with an `AGENTS.md` that defines authorized scope, required
behaviors, and hard limits for all agents. **Edit `packs/red-team/AGENTS.md`
before deployment** to set the `AUTHORIZED_TARGETS` for your engagement.

**Optional connector:** activate `red-team-escalations-to-slack` to surface
escalations in Slack in real time (requires `SLACK_BOT_TOKEN` and
`SLACK_ESCALATION_CHANNEL_ID`).

```bash
agency hub install red-team
```

---

### Connectors

Each pack bundles one or more connectors, but connectors can also be installed
standalone. The `slack-ops` connector (bundled with the `slack-ops` pack) and
`jira-ops` connector (bundled with the `jira-ops` pack) can be used
independently with any agent team.

| Name | Type | Description |
|------|------|-------------|
| `slack-ops` | poll | Poll a Slack channel for messages; route by pattern |
| `slack-events` | webhook | Receive Slack Events API webhooks in real time |
| `jira-ops` | poll | Poll a Jira project for new/updated issues |
| `comms-to-slack` | channel-watch | Mirror agency comms channel to a Slack channel |
| `red-team-escalations-to-slack` | channel-watch | Surface red-team escalations in Slack |

```bash
agency hub install slack-events
```

#### `slack-events` environment variables

- `SLACK_BOT_TOKEN` — Bot User OAuth Token
- `SLACK_SIGNING_SECRET` — App signing secret (used to verify HMAC-SHA256 webhook signatures)

Configure your Slack App's *Event Subscriptions URL* to point at:
```
https://<your-host>/webhooks/slack-events
```

The intake handles the Slack URL verification challenge automatically.
