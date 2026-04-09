"""Rohde & Schwarz FSW spectrum-analyzer adapter."""

from __future__ import annotations

from .scpi_adapter import BaseScpiSpectrumAnalyzer, SpectrumCommandSet

FSW_COMMAND_SET = SpectrumCommandSet(
    query_commands={
        "start_freq": "FREQuency:STARt?",
        "center_freq": "FREQuency:CENTer?",
        "stop_freq": "FREQuency:STOP?",
        "span": "FREQuency:SPAN?",
        "rbw": "BANDwidth:RESolution?",
        "vbw": "BANDwidth:VIDeo?",
        "ref_level": "DISPlay:WINDow:TRACe:Y:RLEVel?",
        "points": "SWEep:POINts?",
        "scale": "DISPlay:WINDow:TRACe:Y:SCALe:PDIVision?",
        "detector": "DETector?",
        "trace_mode": "TRACe:MODE? {trace_name}",
    },
    set_commands={
        "start_freq": "FREQuency:STARt",
        "center_freq": "FREQuency:CENTer",
        "stop_freq": "FREQuency:STOP",
        "span": "FREQuency:SPAN",
        "rbw": "BANDwidth:RESolution",
        "vbw": "BANDwidth:VIDeo",
        "ref_level": "DISPlay:WINDow:TRACe:Y:RLEVel",
        "points": "SWEep:POINts",
        "scale": "DISPlay:WINDow:TRACe:Y:SCALe:PDIVision",
        "detector": "DETector",
        "trace_mode": "TRACe:MODE {trace_name},",
    },
    preset_command="SYSTem:PRESet",
    trigger_single_command="INITiate:IMMediate",
    opc_query="*OPC?",
    trace_query_template="TRACe:DATA? {trace_name}",
    continuous_on_command="INITiate:CONTinuous ON",
    continuous_off_command="INITiate:CONTinuous OFF",
)


class FswSpectrumAnalyzer(BaseScpiSpectrumAnalyzer):
    """Concrete adapter for FSW-family spectrum analyzers."""

    instrument_type = "FSW"
    default_trace_name = "TRACE1"
    command_set = FSW_COMMAND_SET
