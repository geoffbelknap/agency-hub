# Agency Hub

Registry repo for Agency components.

## Repo Purpose

This repo is the source for discoverable Agency content:
- connectors
- services
- presets
- packs
- missions
- ontology and related hub-managed definitions

Agency pulls from this repo through hub workflows.

## Working Rules

- Keep changes schema-compatible with Agency.
- Treat published component definitions as product surface, not casual examples.
- Prefer additive, explicit component metadata over implicit behavior.
- When changing pack, preset, connector, or service structure, consider downstream install, audit, and upgrade flows.
- Changes that do not touch component paths may bypass review-bot logic; be deliberate about what you modify.

## Operator Expectations

- Users install and deploy components through `agency hub ...` commands.
- Hub-managed files synced into `~/.agency/` are not the place for operator customizations.
- Respect the separation between hub-managed content and operator-local overrides.

## Contribution Focus

If you add or change a component:
- keep the repo structure and publishing workflow consistent with `CONTRIBUTING.md`
- make sure dependencies, required credentials, and egress domains are declared clearly
- keep install and deploy behavior understandable from the component definition itself
