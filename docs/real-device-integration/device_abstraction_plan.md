# Device Abstraction Plan

| UI | Provider | Backend |
|----|----------|---------|
| Simulation connect | SimulationDeviceProvider | MockDeviceService |
| Real connect | RealDeviceProvider | HardwareDeviceManager |
| Mock scan | SimulationScanProvider | MockScanRuntimeService |
| Real scan | RealScanProvider / RealScanController | RealScanEngine |

Replace Provider/Adapter only — UI shell unchanged.
