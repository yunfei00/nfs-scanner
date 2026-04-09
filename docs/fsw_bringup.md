# FSW Bring-Up

## Prerequisites

- Python 3.11
- `pyvisa` installed in the same environment
- A working VISA runtime on Windows
- One reachable Rohde & Schwarz FSW VISA resource

## Minimal Command

```powershell
py -3.11 scripts\test_spectrum_analyzer.py `
  --instrument FSW `
  --resource "TCPIP0::192.168.0.50::inst0::INSTR" `
  --start-freq 2.4GHz `
  --stop-freq 2.5GHz `
  --rbw 100kHz `
  --trace-name TRACE1
```

## Recommended Bring-Up Command

```powershell
py -3.11 scripts\test_spectrum_analyzer.py `
  --instrument FSW `
  --resource "TCPIP0::192.168.0.50::inst0::INSTR" `
  --start-freq 2.4GHz `
  --stop-freq 2.5GHz `
  --rbw 100kHz `
  --vbw 100kHz `
  --ref-level 10 `
  --detector RMS `
  --trace-mode WRIT `
  --trace-name TRACE1 `
  --preset `
  --log-level DEBUG `
  --save-json output\fsw_debug.json
```

## Expected Flow

The adapter performs this sequence for one single-shot acquisition:

1. `INITiate:CONTinuous OFF`
2. `INITiate:IMMediate`
3. `*OPC?`
4. `TRACe:DATA? TRACE1`

## Output Highlights

The script prints:

- instrument type
- VISA resource
- `*IDN?` response
- acquisition mode
- peak point value
- trace point count
- frequency window
- RBW/VBW
- detector and trace mode
- normalized metadata summary

## Failure Categories

The script classifies common failures as:

- `VISA connection failed`
- `SCPI timeout`
- `SCPI command not supported`
- `Unexpected instrument response`
- `Configuration error`
