# Public release audit

Scope: the current source tree, curated installation ZIP and reachable file blobs from public Git history. The 1.4.1 maintenance pass includes the 1.4.0 reference-first workflow, optional global instructions, private style catalog and backup interfaces. The initial 1.0.0 publication remains historical. Private development snapshots, user settings and media are outside this publication scope.

| Area | Treatment |
|---|---|
| Private paths | Remove machine/workspace paths; use relative runtime and caller-supplied work paths |
| Credentials | Known GitHub/API/cloud credential patterns, private keys, URL credentials and signed URLs checked; findings do not echo values |
| Personal data | Remove Library IDs, photographs, upload names, user job/receipt/history records and private reference manifests |
| Personal library | Private per-user roots outside the skill and Git; explicit collection, exact image-byte identity, no automatic collection of edit targets/results |
| Global instructions | Explicit persistence, current-scene acknowledgment and stable task snapshots; photographic guidance grants no tool privileges |
| Private backups | Separate unencrypted format; bounded manifest, strict names, hashes/formats, full validation before import, default conflict-preserving merge and failed-write cleanup |
| Packaging | Allowlist runtime files; reject traversal, duplicates, symbolic links and oversized archives |
| History | Independent initial repository; inspect every reachable historical blob before publication |
| CI | Read-only token, pinned actions, no secrets, no privileged pull-request context |
| Dependencies | Core and optional dependencies separated; no bundled third-party executable or model |
| Licensing | MIT for project code; independent method attribution retained, user-image rights not relicensed |
| Host behavior | No hidden uploader, service or scheduled job; authorized image-tool execution remains a host capability |
| Release distribution | Versioned tags remain historical; latest links point to the published stable ZIP/checksum, verified against committed bytes and the manifest |

The executable checks are `tools/check_publication.py`, `tools/doctor.py`, `tests/test_publication.py` and the synthetic library/profile/backup/reference-first regressions. Results must come from commands on the final revision; actual platform evidence is linked from [validation](validation.md). The scanner reports rule/location without echoing matched values. Its history mode skips non-blob Git objects: commit messages, annotated-tag messages and other Git metadata are not scanned. Public metadata requires a separate review. This document describes scope rather than a blanket security certification. Unknown secret formats, semantic personal details, dependency vulnerabilities and host-tool behavior require additional review as appropriate. Runtime job files may contain sensitive URLs, paths and prompts; they are deliberately excluded from public packaging. See [SECURITY.md](../SECURITY.md) for private reporting, metadata and deletion boundaries.
