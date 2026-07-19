# Third-party notices

The Windows application includes third-party Python packages. The release SBOM
contains the exact versions installed in each build. The baseline dependency
metadata currently reports:

| Component | Baseline version | Declared license |
| --- | --- | --- |
| PySide6 / shiboken6 | 6.11.1 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only |
| NumPy | 2.4.6 | BSD-3-Clause and bundled permissive licenses |
| OpenCV Python | 4.13.0.92 | Apache-2.0 |
| PyVISA | 1.16.2 | MIT |
| PyYAML | 6.0.3 | MIT |

Before a customer release, the release owner must review the generated SBOM,
retain the corresponding license texts, and confirm the selected Qt/PySide
commercial or open-source compliance route. This file is an engineering
inventory and is not legal advice.
