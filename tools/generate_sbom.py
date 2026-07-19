"""Generate an SPDX 2.3 JSON inventory from the active build environment."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from nfs_scanner.version import APP_NAME, APP_VERSION


def _spdx_id(name: str) -> str:
    safe = "".join(character if character.isalnum() else "-" for character in name)
    return f"SPDXRef-Package-{safe}"


def _locked_package_names(requirements_path: Path | None) -> set[str] | None:
    if requirements_path is None:
        return None
    names: set[str] = set()
    for line in requirements_path.read_text(encoding="utf-8").splitlines():
        requirement = line.strip()
        if not requirement or requirement.startswith("#"):
            continue
        match = re.match(r"([A-Za-z0-9_.-]+)==", requirement)
        if match is None:
            raise ValueError(f"SBOM requirements must use exact pins: {requirement}")
        names.add(match.group(1).lower().replace("_", "-"))
    return names


def build_sbom(requirements_path: Path | None = None) -> dict[str, object]:
    selected_names = _locked_package_names(requirements_path)
    distributions = sorted(importlib.metadata.distributions(), key=lambda item: item.metadata["Name"].lower())
    packages: list[dict[str, object]] = []
    relationships: list[dict[str, str]] = []
    root_id = _spdx_id(APP_NAME)
    packages.append(
        {
            "SPDXID": root_id,
            "name": APP_NAME,
            "versionInfo": APP_VERSION,
            "downloadLocation": "NOASSERTION",
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "LicenseRef-Proprietary",
            "filesAnalyzed": False,
        }
    )
    for distribution in distributions:
        name = distribution.metadata["Name"] or "unknown"
        if name.lower() == "nfs-scanner":
            continue
        canonical_name = name.lower().replace("_", "-")
        if selected_names is not None and canonical_name not in selected_names:
            continue
        package_id = _spdx_id(name)
        license_text = distribution.metadata.get("License-Expression") or distribution.metadata.get("License")
        packages.append(
            {
                "SPDXID": package_id,
                "name": name,
                "versionInfo": distribution.version,
                "downloadLocation": distribution.metadata.get("Home-page") or "NOASSERTION",
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": license_text or "NOASSERTION",
                "filesAnalyzed": False,
            }
        )
        relationships.append(
            {
                "spdxElementId": root_id,
                "relationshipType": "DEPENDS_ON",
                "relatedSpdxElement": package_id,
            }
        )
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    namespace_seed = f"{APP_NAME}:{APP_VERSION}:{created_at}".encode()
    namespace_hash = hashlib.sha256(namespace_seed).hexdigest()[:20]
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"{APP_NAME}-{APP_VERSION}",
        "documentNamespace": f"https://nfs-scanner.local/spdx/{namespace_hash}",
        "creationInfo": {"created": created_at, "creators": ["Tool: nfs-scanner-generate-sbom"]},
        "packages": packages,
        "relationships": relationships,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--requirements",
        type=Path,
        help="Only include packages pinned by this runtime lock file.",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(build_sbom(args.requirements), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
