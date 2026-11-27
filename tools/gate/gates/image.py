"""Build, scan and verify the packaged application image."""

from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

__all__ = ["ImageGateError", "check_findings", "locked_runtime", "main", "verify_sbom"]

_ROOT = Path(__file__).resolve().parents[3]
_BASELINE = Path("docs/decisions/P12-D5-trivy-baseline.json")
_BASELINE_DIGEST = "7ea4c0f78bba431357b75ce7cf2484fe77cd16ec98f91ee4ced84051394dc3ca"
_PLATFORM = "linux/amd64"
_DATABASE = (
    "ghcr.io/aquasecurity/trivy-db@"
    "sha256:e829daef99d6247063861b8626d07d8579658f8f97a2293c8b4ad50eee9d124f"
)
_DATABASE_FILE_DIGEST = "d6aee51946869bade3856816aef99a58b3b33cfd7f453ab7200c121b3426ca98"
_TRIVY = "0.76.2"
_SYFT = "1.57.0"
_TOOL_PINS = {
    ("trivy", "Linux", "x86_64"): (
        "aquasecurity/trivy",
        _TRIVY,
        "Linux-64bit",
        "bc0fc726e017b8927a62b2d3531d7a84ee01769daf5c99ed866dced54089fdbf",
    ),
    ("trivy", "Darwin", "arm64"): (
        "aquasecurity/trivy",
        _TRIVY,
        "macOS-ARM64",
        "ae7ea358326960406b703c77b2ac490190797d80b306b5b50c2a27221da0a5b8",
    ),
    ("syft", "Linux", "x86_64"): (
        "anchore/syft",
        _SYFT,
        "linux_amd64",
        "9c077a7d43029b3b13e98a8db720661e700c4d58db6352153a06395ae4a2a704",
    ),
    ("syft", "Darwin", "arm64"): (
        "anchore/syft",
        _SYFT,
        "darwin_arm64",
        "17012a5a110323bb1069e513a8665f1ae445905c56b4e3f9a9df4f95c5bb6161",
    ),
}
_FIELDS = ("PkgID", "PkgName", "InstalledVersion", "VulnerabilityID", "Severity")
_REQUIRED_RESULT_TYPES = {("os-pkgs", "debian"), ("lang-pkgs", "python-pkg")}


class ImageGateError(Exception):
    """Image acceptance or tool failure."""


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ImageGateError("expected a JSON object")
    return value


def _array(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ImageGateError("expected a JSON array")
    return value


def _strings(values: list[object]) -> tuple[str, ...]:
    if not all(isinstance(value, str) and value for value in values):
        raise ImageGateError("expected nonempty finding fields")
    return tuple(str(value) for value in values)


def check_findings(report: object, baseline: object) -> None:
    """Reject unapproved findings and incomplete or mismatched scan reports."""
    approval = _object(baseline)
    expected = {
        "approval": "P12-D5",
        "platform": _PLATFORM,
        "trivy_version": _TRIVY,
        "database": _DATABASE,
    }
    if any(approval.get(key) != value for key, value in expected.items()):
        raise ImageGateError("image baseline metadata does not match the scan policy")

    scan = _object(report)
    if scan.get("SchemaVersion") != 2 or _object(scan.get("Trivy")).get("Version") != _TRIVY:
        raise ImageGateError("unexpected Trivy version or report schema")
    if scan.get("ArtifactType") != "container_image":
        raise ImageGateError("scan report must describe a container image")

    approved = {_strings(_array(row)) for row in _array(approval.get("findings"))}
    seen_types: set[tuple[str, str]] = set()
    unexpected: set[tuple[str, ...]] = set()
    for raw_result in _array(scan.get("Results")):
        result = _object(raw_result)
        category, package_type = _strings([result.get("Class"), result.get("Type")])
        seen_types.add((category, package_type))
        for raw_finding in _array(result.get("Vulnerabilities", [])):
            finding = _object(raw_finding)
            key = _strings([category, package_type, *(finding.get(field) for field in _FIELDS)])
            if key not in approved:
                unexpected.add(key)
    if not seen_types >= _REQUIRED_RESULT_TYPES:
        raise ImageGateError("scan omitted an expected package inventory")
    if unexpected:
        findings = ", ".join(f"{key[3]} {key[4]} {key[5]}" for key in sorted(unexpected)[:10])
        raise ImageGateError(
            f"{len(unexpected)} findings outside the approved baseline ({findings})"
        )


def locked_runtime(export: str, environment: dict[str, str]) -> set[tuple[str, str]]:
    """Read the exact target runtime packages from a frozen uv export."""
    requirements: set[tuple[str, str]] = set()
    for line in export.splitlines():
        if not line or line.startswith("#"):
            continue
        requirement = Requirement(line)
        if requirement.marker is not None and not requirement.marker.evaluate(environment):
            continue
        specifiers = list(requirement.specifier)
        if len(specifiers) != 1 or specifiers[0].operator != "==" or "*" in specifiers[0].version:
            raise ImageGateError(f"runtime dependency is not locked exactly: {requirement.name}")
        requirements.add((canonicalize_name(requirement.name), specifiers[0].version))
    if not requirements:
        raise ImageGateError("runtime dependency export is empty")
    return requirements


def verify_sbom(sbom: object, locked: set[tuple[str, str]]) -> None:
    """Require each locked runtime package and version in the CycloneDX inventory."""
    document = _object(sbom)
    if document.get("bomFormat") != "CycloneDX":
        raise ImageGateError("expected a CycloneDX SBOM")
    present: set[tuple[str, str]] = set()
    for raw_component in _array(document.get("components")):
        component = _object(raw_component)
        purl = component.get("purl")
        if isinstance(purl, str) and purl.startswith("pkg:pypi/"):
            name, version = _strings([component.get("name"), component.get("version")])
            present.add((canonicalize_name(name), version))
    missing = locked - present
    if missing:
        raise ImageGateError(f"locked runtime dependencies missing from SBOM: {sorted(missing)}")


def _run(cwd: Path, *command: str) -> str:
    environment = {**os.environ, "SYFT_CHECK_FOR_APP_UPDATE": "false"}
    result = subprocess.run(
        command, cwd=cwd, env=environment, capture_output=True, text=True, timeout=300, check=False
    )
    if result.returncode != 0:
        diagnostic = (result.stderr or result.stdout).strip().splitlines()[-1:]
        raise ImageGateError(
            f"{Path(command[0]).name} exited {result.returncode}: {' '.join(diagnostic)}"
        )
    return result.stdout


def _install(name: str, path: Path) -> Path:
    repository, version, asset, digest = _TOOL_PINS[(name, platform.system(), platform.machine())]
    filename = f"{name}_{version}_{asset}.tar.gz"
    url = f"https://github.com/{repository}/releases/download/v{version}/{filename}"
    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310  # nosec B310
        contents = response.read()
    if hashlib.sha256(contents).hexdigest() != digest:
        raise ImageGateError(f"{name} archive digest mismatch")
    with tarfile.open(fileobj=io.BytesIO(contents), mode="r:gz") as archive:
        member = archive.getmember(name)
        stream = archive.extractfile(member) if member.isfile() else None
        if stream is None:
            raise ImageGateError(f"{name} archive did not contain the executable")
        binary = stream.read()
    target = path / name
    target.write_bytes(binary)
    target.chmod(0o755)
    return target


def _config_check(root: Path, trivy: Path, logs: Path) -> None:
    targets = [root / "Dockerfile", root / "deploy" / "blueprint", root / "deploy" / "bundle"]
    for target in targets:
        if target.exists():
            _run(
                root,
                str(trivy),
                "config",
                "--skip-check-update",
                "--skip-version-check",
                "--exit-code",
                "1",
                "--format",
                "json",
                "--output",
                str(logs / f"config-{target.name}.json"),
                str(target),
            )


def _load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_baseline(root: Path) -> object:
    contents = (root / _BASELINE).read_bytes()
    if hashlib.sha256(contents).hexdigest() != _BASELINE_DIGEST:
        raise ImageGateError("approved image baseline digest mismatch")
    return json.loads(contents)


def _scan(root: Path, trivy: Path, logs: Path, cache: Path, tag: str) -> None:
    _run(
        root,
        str(trivy),
        "image",
        "--cache-dir",
        str(cache),
        "--download-db-only",
        "--skip-version-check",
        "--db-repository",
        _DATABASE,
    )
    with (cache / "db" / "trivy.db").open("rb") as database:
        if hashlib.file_digest(database, "sha256").hexdigest() != _DATABASE_FILE_DIGEST:
            raise ImageGateError("Trivy database file digest mismatch")
    report = logs / "trivy-image.json"
    _run(
        root,
        str(trivy),
        "image",
        "--cache-dir",
        str(cache),
        "--skip-version-check",
        "--offline-scan",
        "--skip-db-update",
        "--skip-java-db-update",
        "--image-src",
        "docker",
        "--scanners",
        "vuln",
        "--format",
        "json",
        "--output",
        str(report),
        tag,
    )
    check_findings(_load(report), _load_baseline(root))
    _run(
        root,
        str(trivy),
        "image",
        "--cache-dir",
        str(cache),
        "--skip-version-check",
        "--offline-scan",
        "--skip-db-update",
        "--skip-java-db-update",
        "--image-src",
        "docker",
        "--scanners",
        "secret",
        "--exit-code",
        "1",
        "--output",
        os.devnull,
        tag,
    )


def _verify_runtime(root: Path, tag: str) -> dict[str, str]:
    probe = """
import json, os, platform, sys

assert os.geteuid() != 0
assert sys.implementation.name == 'cpython'
print(json.dumps({
    'implementation_name': sys.implementation.name,
    'implementation_version': platform.python_version(),
    'os_name': os.name,
    'platform_machine': platform.machine(),
    'platform_python_implementation': platform.python_implementation(),
    'platform_release': platform.release(),
    'platform_system': platform.system(),
    'platform_version': platform.version(),
    'python_full_version': platform.python_version(),
    'python_version': '.'.join(platform.python_version_tuple()[:2]),
    'sys_platform': sys.platform,
}))
"""
    environment: dict[str, str] = json.loads(
        _run(
            root,
            "docker",
            "run",
            "--rm",
            "--read-only",
            "--network=none",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--memory=512m",
            "--cpus=1",
            "--pids-limit=128",
            tag,
            "python",
            "-c",
            probe,
        )
    )
    healthcheck = _run(
        root, "docker", "image", "inspect", "--format", "{{json .Config.Healthcheck}}", tag
    ).strip()
    if not json.loads(healthcheck):
        raise ImageGateError("image does not define a health check")
    return environment


def _verify_image(root: Path, tools: Path) -> None:
    logs = root / ".gate-logs" / "image"
    logs.mkdir(parents=True, exist_ok=True)
    trivy, syft = (_install(name, tools) for name in ("trivy", "syft"))
    _config_check(root, trivy, logs)
    commit = _run(root, "git", "rev-parse", "HEAD").strip()
    tag = f"control-tower-gate:{commit}"
    _run(root, "docker", "build", "--platform", _PLATFORM, "--provenance=false", "--tag", tag, ".")
    runtime = _verify_runtime(root, tag)
    _scan(root, trivy, logs, tools / "trivy-cache", tag)
    sbom = logs / "image.cdx.json"
    _run(root, str(syft), "scan", f"docker:{tag}", "--output", f"cyclonedx-json={sbom}")
    export = _run(
        root,
        "uv",
        "export",
        "--frozen",
        "--no-dev",
        "--no-emit-project",
        "--no-hashes",
        "--no-annotate",
    )
    verify_sbom(_load(sbom), locked_runtime(export, runtime))


def main() -> int:
    """Run the project image gate or validate a gate self-test fixture."""
    try:
        cwd = Path.cwd().resolve()
        fixture_root = os.environ.get("GATE_ROOT")
        if cwd == _ROOT:
            with TemporaryDirectory(prefix="control-tower-image-") as temporary:
                _verify_image(cwd, Path(temporary))
        elif fixture_root and Path(fixture_root).resolve() == cwd:
            check_findings(_load(cwd / "scan.json"), _load_baseline(_ROOT))
        else:
            raise ImageGateError("run the image gate from the project root")
    except (ImageGateError, OSError, KeyError, ValueError, subprocess.SubprocessError) as exc:
        print(f"image: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
