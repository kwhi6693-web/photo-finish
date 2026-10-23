# Public release audit

Scope: Photo Finish 1.0.0 source tree, the installable ZIP and fresh public Git history. Private development snapshots and media are not part of the release.

| Area | Treatment |
|---|---|
| Private paths | Remove machine/workspace paths; use relative runtime and caller-supplied work paths |
| Credentials | Known GitHub/API/cloud credential patterns, private keys, URL credentials and signed URLs checked; findings do not echo values |
| Personal data | Remove Library IDs, photographs, upload names, user job/receipt/history records and private reference manifests |
| Packaging | Allowlist runtime files; reject traversal, duplicates, symbolic links and oversized archives |
| History | Independent initial repository; inspect every reachable historical blob before publication |
| CI | Read-only token, pinned actions, no secrets, no privileged pull-request context |
| Dependencies | Core and optional dependencies separated; no bundled third-party executable or model |
| Licensing | MIT for project code; independent method attribution retained, user-image rights not relicensed |
| Host behavior | No hidden uploader, service or scheduled job; authorized image-tool execution remains a host capability |

The executable checks are `tools/check_publication.py`, `tools/doctor.py` and the adversarial tests in `tests/test_publication.py`. Results must come from those commands on the final revision. This document describes scope rather than a blanket security certification. Unknown secret formats, semantic personal details, dependency vulnerabilities and host-tool behavior require additional review as appropriate. Runtime job files may contain sensitive URLs, paths and prompts; they are deliberately excluded from public packaging.
