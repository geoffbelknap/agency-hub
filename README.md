# Agency Hub

Default component registry for the [Agency platform](https://github.com/geoffbelknap/agency).

## Structure

```
packs/          Declarative team compositions (pack.yaml + connectors)
connectors/     External system bindings (webhook, poll, schedule, channel-watch)
presets/        Agent preset definitions
skills/         Agent skill packages
policies/       Policy templates
workspaces/     Workspace definitions
```

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
