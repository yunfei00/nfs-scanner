# 05 Plugin Architecture

## 1. Goal

The product must support new instruments and cameras without modifying the main application each time.

The plugin system should serve commercial delivery, not just development convenience.

## 2. Plugin Types

V1 plugin types:

- Spectrum instrument plugin
- Camera plugin

Future plugin types:

- Motion controller plugin
- Data importer plugin
- Report template plugin
- Analysis algorithm plugin

## 3. Plugin Loading

Recommended locations:

```text
plugins/
  spectrum/
  camera/
  analysis/
  report/
```

Packaged commercial deployments may use:

```text
NFSScanner/
  plugins/
    spectrum/
    camera/
```

## 4. Plugin Contract

A plugin must provide metadata:

- plugin_id
- display_name
- version
- vendor
- supported_models
- capabilities

A plugin must expose an adapter factory that returns the expected adapter interface.

## 5. Spectrum Plugin

A spectrum plugin must implement capabilities equivalent to the Spectrum Adapter:

- connect
- disconnect
- identify
- configure
- sweep
- read trace

## 6. Config-based Instrument Plugin

For standard SCPI devices, a JSON command template can be used.

Recommended fields:

- device_name
- connection_type
- idn_pattern
- commands.init
- commands.configure
- commands.read_trace
- units
- parse_rules

## 7. Security and Stability

Plugins run locally and can affect reliability.

Rules:

- plugin errors must be isolated and reported
- failed plugin load must not stop the whole app
- plugins must not control UI layout directly
- plugin metadata must be available to unified device diagnostics and logs

## 8. Versioning

Plugin compatibility should include:

- minimum_app_version
- adapter_api_version
- plugin_version

## 9. Testing

Each plugin should have:

- mock mode
- connection test
- metadata validation
- basic command validation

## 10. Commercial Delivery

The plugin system enables paid integration:

- standard SCPI template support
- custom plugin development
- customer-specific device bundles
