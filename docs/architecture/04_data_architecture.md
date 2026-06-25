# 04 Data Architecture

## 1. Goal

NFS Scanner data must be recoverable, traceable and reusable for offline analysis.

A scan should remain useful even when it is stopped early or a device fails after partial acquisition.

## 2. Project Structure

Recommended project layout:

```text
project_dir/
  project.json
  scans/
    scan_YYYYMMDD_HHMMSS/
      scan_config.json
      alignment.json
      photo.png
      points.csv
      traces.csv
      heatmap_cache/
      exports/
      logs/
```

## 3. Project Metadata

`project.json` stores:

- project_id
- project_name
- operator
- created_at
- updated_at
- notes
- default_device_profile
- default_output_dir

## 4. Scan Task Metadata

`scan_config.json` stores:

- scan_id
- project_id
- created_at
- x_start/x_stop/x_step
- y_start/y_stop/y_step
- z_height
- feed_rate
- dwell_time
- snake_mode
- trace_id
- marker_frequency
- device_snapshot

## 5. Alignment Metadata

`alignment.json` stores:

- image_path
- alignment_mode
- world_points
- image_points
- transform_matrix
- x_range
- y_range
- created_at

## 6. Point Data

`points.csv` stores one row per acquired point.

Recommended columns:

- point_index
- x
- y
- z
- timestamp
- trace_id
- marker_frequency
- marker_value
- status

## 7. Trace Data

Trace data must support existing formats.

Supported row keys:

- `x_y_z_trace1_re`
- `x_y_z_trace1_im`
- `x_y_z_Trc1_S21_re`
- `x_y_z_Trc1_S21_im`

Parsing rule:

- first 3 parts are x/y/z
- last part is re/im
- middle parts joined together form trace_id

## 8. Offline Analysis

Data View must be able to load historical tasks without connected devices.

Required capabilities:

- discover traces
- select frequency
- compute magnitude, dB, phase, real and imag
- generate heatmap matrix
- render heatmap with selected LUT

## 9. Cache Policy

Heatmap cache is optional.

If cache exists and matches the current parameters, it may be used.

If cache is missing or invalid, regenerate from source data.

## 10. Export Policy

Exports should not overwrite raw data.

Recommended export files:

- heatmap.png
- heatmap_with_photo.png
- spectrum.png
- selected_points.csv
- report.pdf

## 11. Data Compatibility Rule

Never break existing scan output formats without adding a migration path.
