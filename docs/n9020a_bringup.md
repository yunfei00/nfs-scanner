# N9020A Bring-Up

## Prerequisites

- Python 3.11
- `pyvisa` installed in the same environment
- A working VISA runtime on Windows
- One reachable Keysight N9020A / MXA X-Series VISA resource

## Common VISA Resource Examples

- `TCPIP0::192.168.0.60::inst0::INSTR`
- `TCPIP0::192.168.0.60::hislip0,4880::INSTR`

## Minimal Command

```powershell
py -3.11 scripts\test_spectrum_analyzer.py `
  --instrument N9020A `
  --resource "TCPIP0::192.168.0.60::inst0::INSTR" `
  --start-freq 2.4GHz `
  --stop-freq 2.5GHz `
  --rbw 100kHz `
  --vbw 100kHz `
  --trace-name TRACE1
```

## Recommended Bring-Up Command

```powershell
py -3.11 scripts\test_spectrum_analyzer.py `
  --instrument N9020A `
  --resource "TCPIP0::192.168.0.60::inst0::INSTR" `
  --start-freq 2.4GHz `
  --stop-freq 2.5GHz `
  --rbw 100kHz `
  --vbw 100kHz `
  --points 1001 `
  --ref-level 10 `
  --detector POS `
  --trace-mode CLRW `
  --trace-name TRACE1 `
  --preset `
  --log-level DEBUG `
  --save-json output\n9020a_debug.json
```

## Expected Flow

The adapter performs this sequence for one single-shot acquisition:

1. `*IDN?`
2. `*CLS`
3. optional `*RST`
4. `FORM ASC`
5. frequency / RBW / VBW / sweep points / detector / trace type configuration
6. `ABOR`
7. `INIT:CONT OFF`
8. `INIT:IMM`
9. `*OPC?`
10. `TRAC:DATA? TRACE1`

## Output Highlights

The script prints:

- instrument type
- VISA resource
- raw `*IDN?` response
- acquisition mode
- frequency window
- RBW / VBW
- sweep points
- detector and trace mode
- trace point count
- first few trace points
- normalized metadata summary
