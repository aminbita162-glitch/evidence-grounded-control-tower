# Phase 12 stop report

phase: P12
task: P12-T01
condition: Part 1 §§5.4, 6.1 and 7.1, Part 8 §8.2, and P12-T01 image scan acceptance
what_happened: Trivy 0.76.2 requires a vulnerability database for the image scan. The local cache has no database, and the directive permits the scanner database registry only in CI. The official database project has no current database archive in its GitHub Releases.
attempts: 0
evidence: Two independent linux/amd64 builds succeeded. The read-only runtime check returned UID 10001. Trivy Dockerfile configuration scanning found zero failures. The CycloneDX SBOM produced by Syft includes all 30 locked runtime dependencies for the target. The offline Trivy image scan exited 1 with the first-run database error. The content hashes differ (DERIVED from the build logs). The first is sha256:21dc90cd53ef8fbc77d8ee0c67db09be4ab735c95106fd638ef0ed8fd5be6f38. The second is sha256:85c876eb4e71040edce73117a4bbb39078e314206eb9ab9adeb5badecd845322. Layers 6 through 17 also differ.
decision_needed: Supply a verified local Trivy vulnerability database or authorize the local build machine to retrieve a current, digest-pinned database from ghcr.io before commit.
options: A verified local database supports the required offline image scan. A narrow registry allowance enables the build machine to acquire the pinned database directly.
untouched: The Phase 12 ledger and gate configuration. The draft Dockerfile and ignore file are local working files.
