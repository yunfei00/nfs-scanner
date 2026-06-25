# 09 Configuration

## 1. Goal

Configuration must support both development and commercial deployment.

The app should remember user preferences while keeping scan results reproducible.

## 2. Configuration Types

### Application Configuration

Global settings:

- theme
- language
- last opened project
- window layout
- default data directory
- log level

### Device Profiles

Reusable device settings:

- motion port and baudrate
- spectrum resource address
- camera index or camera id
- timeout settings
- default frequency parameters

### Scan Templates

Reusable scan settings:

- area size
- step values
- z height
- dwell time
- snake mode
- marker frequency
- trace selection

### Per-scan Configuration

Saved inside each scan task:

- actual scan config
- device snapshot
- alignment config
- display settings used for exports

## 3. Storage Locations

Recommended development locations:

```text
config/
  app_config.json
  device_profiles.json
  scan_templates.json
```

Recommended packaged app locations:

```text
NFSScanner/
  config/
  data/
  logs/
  plugins/
```

## 4. Rules

- User preferences may change freely.
- Per-scan configuration must be immutable after scan completion unless saved as a new analysis version.
- Device profiles must not be required to open historical data.
- Missing configuration should fall back to safe defaults.

## 5. Layout Persistence

Save:

- window size
- splitter positions
- collapsed panels
- selected theme
- last active work mode

## 6. Template Policy

Scan templates are user convenience features.

They should not replace saved scan_config.json in completed tasks.

## 7. AI Agent Rule

When adding a new persistent setting, document:

- where it is stored
- default value
- whether it is app-level, device-level, template-level or scan-level
