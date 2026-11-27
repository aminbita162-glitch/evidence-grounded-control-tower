# Phase 12 stop report

phase: P12
task: P12-T01
condition: Part 1 §§5.6, 6.1 and 7.1, and P12-T01 image scan acceptance
what_happened: The confirmed directive and run-parameters hash prefixes are `f6437345` and `3037009f`. Decision D4 authorized landing D3 and using a verified local or digest-pinned Trivy database. The database downloaded successfully and the offline image scan completed. The rebuilt image has 225 operating-system findings and eight Python-package findings, including 59 high-severity findings in total. The repository provides no owner-approved image baseline covering those findings.
attempts: 1. Rebuilt the draft without an exported provenance attestation to rule out third-party SBOM input. The offline scan reproduced the findings. Failure signature: Trivy image scan, vulnerabilities outside an approved baseline, exit 1.
evidence: The official database manifest resolved to `sha256:e829daef99d6247063861b8626d07d8579658f8f97a2293c8b4ad50eee9d124f`, and `trivy image --download-db-only --db-repository` with that digest exited 0. The fresh `docker build --platform linux/amd64 --provenance=false` exited 0. `trivy image --offline-scan --skip-db-update --skip-java-db-update --scanners vuln --exit-code 1` exited 1 on both images. On the rebuilt image, 222 operating-system findings had no fixed version in the scanner output.
decision_needed: Provide the owner-approved image baseline for the findings that may remain, or identify and authorize a replacement base image or remediation path that satisfies the scan acceptance criteria.
options: An approved baseline must enumerate findings explicitly. A replacement image or remediation requires a fresh build and scan against the pinned database before T01 can be accepted.
untouched: The Phase 12 task ledger, gate implementations and deployment configuration. The existing Dockerfile and ignore-file drafts remain local.
