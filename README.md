# Agency Hub

The package manager for [Agency](https://github.com/geoffbelknap/agency). Discover, install, and share connectors, services, presets, missions, and packs.

**Want to contribute a component?** See [CONTRIBUTING.md](CONTRIBUTING.md).

## Assurance

Agency Hub separates publication from assurance.

- publication makes an artifact available from a hub
- assurance records verified review outcomes and publisher identity facts
- local Agency policy decides what may be installed or activated

## Install a Component

```bash
agency hub install limacharlie          # auto-detects kind, shows consent prompt
agency hub install security-ops         # pack — deploys a full team
```

No `--kind` needed — names are auto-detected. The install prompt shows what credentials and egress domains the component needs before you approve.

## Deploy a Pack

```bash
agency hub deploy security-ops
```

One command: installs dependencies, creates the team, assigns missions.

## Create and Publish

```bash
agency hub create connector my-scanner  # scaffold
nano my-scanner/connector.yaml          # edit
agency hub audit my-scanner             # validate
agency hub publish my-scanner           # submit PR
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

## CLI Reference

```bash
# Discovery
agency hub search <query>               # search components
agency hub info <name>                  # detailed info

# Install / Remove
agency hub install <name>              # install + activate + resolve deps
agency hub remove <name>               # remove component
agency hub deactivate <name>           # stop without removing

# Packs
agency hub deploy <name>               # deploy pack (team + missions)
agency hub teardown <name>             # stop agents, archive channels

# Updates
agency hub update                      # refresh sources (git pull)
agency hub outdated                    # show available upgrades
agency hub upgrade [name...]           # apply upgrades

# Health
agency hub check [name]                # component health
agency hub doctor                      # system-wide health

# Sources
agency hub add-source <name> <url>     # add third-party source
agency hub list-sources                # show sources
agency hub remove-source <name>        # remove source

# Publishing
agency hub create <kind> <name>        # scaffold component
agency hub audit <path>                # validate before publishing
agency hub publish <path>              # submit PR to source
```

## Available Components

### Packs

| Name | Description |
|------|-------------|
| `agency-bridge-slack` | Foundational Slack-native Agency conversation bridge |
| `community-admin` | Private community administration for Slack communities and managed documents |
| `security-ops` | Phase 1 security operations — alert triage (Haiku) + environment explorer (Sonnet) |
| `jira-ops` | Jira queue management — polls issues, routes by type/priority |
| `red-team` | Authorized security testing coordination |

### Connectors

| Name | Type | Description |
|------|------|-------------|
| `limacharlie` | poll | LimaCharlie endpoint security alerts |
| `limacharlie-sensors` | poll | LimaCharlie sensor inventory (graph-only) |
| `nextdns-blocked` | poll | NextDNS blocked DNS queries |
| `nextdns-analytics` | poll | NextDNS domain analytics (graph-only) |
| `unifi` | poll | UniFi infrastructure devices (graph-only) |
| `unifi-hosts` | poll | UniFi console inventory (graph-only) |
| `unifi-sites` | poll | UniFi site topology (graph-only) |
| `slack-admin` | none | Privileged Slack admin operations |
| `slack-app-home` | none | Slack App Home publishing |
| `slack-canvas` | none | Slack Canvas publishing |
| `slack-commands` | webhook | Slack slash command ingress |
| `slack-events` | webhook | Slack Events API real-time |
| `slack-interactivity` | webhook | Slack interactivity and modal lifecycle |
| `agency-bridge-slack-events-outbound` | channel-watch | Relay Slack Events replies back to Slack |
| `agency-bridge-slack-interactivity-outbound` | channel-watch | Relay Slack interactivity replies back to Slack |
| `agency-bridge-slack-commands-outbound` | channel-watch | Relay Slack slash command replies back to Slack |
| `agency-bridge-slack-outbound` | channel-watch | Relay Slack-originated replies back to Slack |
| `google-drive-admin` | none | Bounded Google Drive sharing and permission administration |
| `jira-ops` | poll | Jira issue polling |
| `comms-to-slack` | channel-watch | Mirror comms to Slack |

### Services

| Name | Domain |
|------|--------|
| `limacharlie-api` | api.limacharlie.io |
| `nextdns-api` | api.nextdns.io |
| `unifi-api` | api.ui.com |
| `brave-search` | api.search.brave.com |
| `slack` | slack.com |
| `jira` | *.atlassian.net |
| `github` | api.github.com |

### Presets

| Name | Tier | Description |
|------|------|-------------|
| `security-triage` | fast | Autonomous alert assessment |
| `security-explorer` | standard | Scheduled environment enrichment |
| `community-administrator` | standard | Governance and access coordination for private communities |

### Missions

| Name | Trigger | Description |
|------|---------|-------------|
| `alert-triage` | LC connector | Triage security alerts, post to findings |
| `security-explorer-mission` | Cron (6h) | Enrich knowledge graph with environment context |
| `community-vote-close` | Cron (5m) | Close community votes and summarize outcomes |
| `community-memory-distill` | Cron (4h) | Distill durable administrative memory from discussion |
| `community-access-sync` | Cron (daily) | Reconcile approved membership and managed access |

## Hub-Managed Files

`agency hub update` syncs these files into `~/.agency/`. Do not edit them directly.

| File | Customization |
|------|--------------|
| `routing.yaml` | Use `routing.local.yaml` for custom providers |
| Service definitions | Create new files, don't edit hub-managed ones |
| Base ontology | Add to `~/.agency/knowledge/ontology.d/` |

## Third-Party Sources

Host your own hub:

```bash
# Users add your source
agency hub add-source my-org https://github.com/my-org/agency-hub.git

# Then install from it
agency hub install my-connector --source my-org
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for hub repo structure and CI setup.

## CI

**Review bot** — validates PRs, auto-approves routine changes, flags security surface changes.

**Stamp metadata** — stamps `metadata.yaml` with build hash on merge.
