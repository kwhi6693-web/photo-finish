# Photo Finish actual host acceptance

Updated 2026-10-26 (Asia/Shanghai), PR #14, continuing 7d252ed. Candidate remains **1.5.0-rc.1**, workflow 2026-10-25.1. Earlier 246-test evidence is retained. The Windows checkpoint fix now has its own native 261-test and matrix evidence; see the dated entry below.

## Product scope and exact installation

最新真实续接见[2026-10-26区域工具与宿主验收](HOST_CAPABILITIES_20261026.md)：原V1平台文件已通过权威资料库元数据及完整字节取回核验；独立Work仅照片触发已观察通过，但该新任务生成图未通过保真。Adobe天空局部光色本例已完成真实mask、原PNG与蒙版外零差验证。城市夜景/建筑文字/低曝光街景完成原生工具组件实测，尚不等于完整旅行批次或版本链验收。下文此前“平台保存/独立触发待确认”为历史状态，旧账本仍未恢复。

Long-term product scope: professional non-portrait photography for natural landscapes, city nights, architecture, travel, still life, food and products. Portrait photographs and portrait beautification are excluded. Incidental people retain the existing identity/content protections and receive no targeted retouching. Earlier portrait examples and acceptance requirements are superseded. Historical numerical scene J remains only for compatibility, not current orchestration or a product promise.

The corrected candidate was actually copied to the authenticated Skills workspace, validated, committed and successfully pushed (the original scope correction was d47ffd7; current reliability installation is recorded in progress). Host Skills readback contains the corrected scope and exactly matches the source SKILL text. All 115 manifest files match, with no extra installed files. This proves installation/loading; it does not prove a new user photo-only event.

- Package: 495152 bytes / 116 entries including manifest.
- Package SHA-256: `c3ef681c313bf094f9cecc03f8527ca4159bd0daf7273fb15b36b666b3e3d8c5`.
- Installed SKILL SHA-256: `587e47344a1a1727ae7efd4a9c1f1b76f23241e9dbd44c3577b9f1c3fcf1c8ba`.
- Doctor, publication/history scan, deterministic-build/relocated-install regression and diff checks passed. The requested Windows-fix full regression passed; installation commit 355df17 matches all 115 manifest files.

## Real landscape run

The earlier download blocker was overcome through the authorized GitHub connector using actual base64 file bytes, not search thumbnails. The [ArrayFire asset license index](https://github.com/arrayfire/assets/blob/master/examples/images/README.md) marks both `nature.jpg` and `trees_ctm.jpg` CC0. No test photo is shipped in this repository or skill package.

- Target: real grove/meadow/bright-sky photograph, 1920x1280 JPEG, 934266 bytes; Git blob `854d43c68afa874523974ff3abe5e01e7e7cf73f`; SHA-256 `8e1d84df59988537c9c2176bcb973b443dfc124e0ca35ae77c692b05691e3273`. This is the repository-distributed photograph, not a claimed original camera master. Visual category: backlit trees against bright sky; exact sun position/time is not asserted.
- Reference: real monochrome winter tree landscape, Git blob `37b1fa35321bc5eb5035ef4d9804478ffea7fdff`; SHA-256 `2193bc3b9f2b944dd696f63becb67b71acb00a86f72f6a302525e5ac60f48a99`. Distant incidental people are not targets and were not copied.
- An isolated anonymous library stored the authorized reference with tags, `use_for=[light]` and a no-scene-copy note. Query **宁静** actually matched **安静** through finite keyword expansion, not vector search. Actual prepare/submit carried the viewed reference and light-only decision into real image-tool arguments.
- Anonymous rules required preserved composition/objects and natural greens without HDR/false texture. Separate CLI processes repeatedly returned the same profile hash. No production preferences were accessed or inferred. Explicit private root configuration is required: one unsubmitted revision draft omitted it and saw the empty default; it was retained unused and corrected before any submission.
- The actual theory chapter on tone/color hierarchy informed the direction: keep trees darker than sky, separate shadows selectively and avoid inventing clipped-highlight detail. This is observed reasoning/application, not an isolated causal test of theory or reference effectiveness.

| Actual image_gen.imagegen call | Observed result | Quality decision |
|---|---|---|
| Initial edit, 28.333s | Added dramatic clouds/sunbeams and changed fence details | Failed actual full-frame/native-detail review; protected-content failure retained |
| One deliberate correction from original, 24.696s | No invented rays; recognizable canopy, mountains and fence positions correspond; natural greens and soft sky transitions | Accepted as **V1**, 1536x1024, ordinary screen / `screen_srgb_assumed` / semantic identity only. Fine leaves/grass were regenerated; no pixel preservation, recovered-detail or print claim |
| Local revision from accepted V1, 21.403s | Requested only lower-left grass color, but non-target canopy/right-grass texture changed and coarsened | Failed local preservation review; **no formal V2** registered; no further repeated generations |

Additional user-ordered checks were then performed: V1 was re-read at 1536x1024 with the exact accepted hash, but no authoritative save receipt or identity metadata existed; saving remains pending. Opening the rendered V1 and using its save/download action is the available manual method, with no re-edit. A filename search returning no result is not proof of absence.

| Additional actual call | Result | Decision |
|---|---|---|
| More natural from V1, 26.414s | More restrained color, but coarse/smoothed leaf clumps and restructured grass did not establish reduced false texture | Rejected; no formal V2 |
| Sky-only from explicit V1, 36.930s | Reconstructed cloud forms and changed non-sky grass/canopy texture | Rejected; no formal V2. Real non-sky RGB absolute-difference probe also recorded; it is not an automatic aesthetic score |

Both cases restored exact existing V1 with zero new editor calls; accepted ledger/output hashes remained unchanged. Naturalness output SHA-256: `b6760d23b5201923416b6eba016516a008f802fe8ce72ba04b03ddd10de124f1`; sky-only output SHA-256: `fe7828d1b3edcfe1c7abc8ed2210f1152b3270759720009dcef8fb1c21517d0e`.

These are actual tool-boundary durations at millisecond precision, not end-to-end latency claims. There is **one independent edit target**, five actual editor calls and five real visual reviews. Do not count the correction as a new independent scene or report first-source acceptance as 100%. The initial edit failed; source-level first acceptance is 0/1 in this small run.

Accepted V1 SHA-256: `268db8bc1a2e92fa61f2884503e9c15444ebd01d0220fd9d1d8cf1d2cf1a4226`. Initial rejected output: `4bb7a0cb4a8e3263caad57ce81590b3b0c6634c576b36c164c2a832d36e2d997`. Rejected local output: `b63ebc14e2186c1c3ce9642032c0fce3125fa7404a3970e2ce5af539cad424d0`.

## Delivery, restoration and limits

- Real generated/displayed/quality-accepted/save-confirmed states stayed separate. V1 is generated, displayed and accepted for its limited screen scope; persistent image saving is **pending confirmation**. The image tool supplies no authoritative persistence identity/hash receipt during this turn. No duplicate upload manufactured one.
- The failed first output could not enter `next-step` because the existing gate requires a passed upstream review. This refusal was preserved; no pass flag or protection was weakened. A new correction from the known original was deliberately prepared, with the failed ledger retained. This is not an unknown/working retry.
- After the rejected local attempt, actual `restore(V1)` returned the exact accepted bytes with **zero new editor calls**. The accepted ledger and output hashes stayed unchanged. Independent CLI processes re-read the V1 cursor and identical profile; repeated delivery returned no new hint.
- This demonstrates read-only return from a rejected displayed attempt to existing V1. It does **not** establish a successful accepted V2-to-V1 sequence, a fresh user conversation's context restoration or a real photo-only auto-trigger.
- No real save failure or unknown external render occurred. Their live recovery remains unverified; existing automated evidence is retained separately. Anonymous evidence-archive saving is not an edited-photo save receipt.

## Independent-session attempt and evidence-retention incident

A real fresh empty ChatGPT Work browser conversation was opened. Its file menu showed the updated landscape/architecture Skill summary. Only the authorized CC0 landscape was selected for upload; the file-chooser/upload tool timed out. No sent photo-only message, skill-selection trace or automatic render was observed. This case remains **unverified**; no repeated upload/submission was made after the unknown outcome.

After that long timeout, the temporary private acceptance root was no longer present. Its original ledgers, anonymous SQLite profile/session index and detailed CLI logs are unavailable. The five actual generated output files and authorized source bytes survived; they were re-read, fully decoded and matched all five recorded hashes. Retained actual tool-return metadata/timings and the first complete arguments also survived. A **partial** evidence archive with those bytes was successfully persisted, clearly declaring missing raw records. It must not be presented as a recovered original ledger, a photo-save receipt, or a completed cross-session version test. Previously observed restores/immutability are historical execution results; they cannot currently be resumed from the lost private index. This retention gap is an additional release blocker.

Do not synthesize replacement historical records or claim that a new index is the original one. Before another long UI task, persist private evidence and session state outside disposable temporary storage; any restoration must validate actual bytes and provenance.

## Required visual matrix and remaining work

| Required category | Current result / next evidence |
|---|---|
| Backlit natural landscape | One actual source edited; V1 accepted in limited screen scope after a failed first output; local revision failed |
| City night | Unverified; needs real lamp/neon, shadow/noise, color and halo review |
| Architecture and lettering | Unverified; needs original/result characters, sign geometry and structural comparison |
| Travel landscape group | Unverified; needs at least three authorized photos, per-photo acceptance, ordered delivery and completed-photo preservation |
| Soft-focus or low-exposure landscape | Unverified; preserve intended softness/darkness without invented detail or forced brightening |

Use authorized actual bytes only, outside Git/skill directories. Next perform a photo-only user message in the installed host; then obtain reliable local edit evidence without changing non-target regions, successful accepted V2/rollback, authoritative photo-save receipts and remaining four categories. Do not introduce a paid service, key or new infrastructure just to obtain a pass. Current whole-image generative local editing is a real failed acceptance item, not merely a missing test.

**Release decision: HOLD.** Keep PR #14 Draft and 1.5.0-rc.1. No main merge, formal tag, Release or final release notes until necessary acceptance passes and explicit user approval is given.

## Reliability repair continuation

See [actual causes, minimal repairs and evidence](RELIABILITY_FIXES.md). A new private checkpoint was actually saved, remotely retrieved, restored and verified, including unchanged V1 bytes; original raw ledgers remain missing and no original image-auto-save receipt was synthesized. Same-intent save recovery was fixed. Current known full-frame imagegen is rejected before submission for local-only version revisions; local visual quality itself remains failed. No new image render was issued.

Scope coverage beyond the existing five-category matrix: still life, food and product photography are supported non-portrait scenarios, but their real visual acceptance remains unverified. Portrait photos and portrait-effect metrics remain excluded; generic incidental-person protection tests remain. Fresh-chat upload result is unknown at the automation transport boundary, not an established Skill auto-trigger failure.

## Windows修复后的真实续接 — 2026-10-26

当前运行时修复ffdbe9a、测试连接清理e0e10d1；原生Windows先12项检查点、261项全套和4项符号链接/临时别名检查通过，Push/PR共12个任务成功。可核实日志：[Windows job121330018203](https://github.com/kwhi6693-web/photo-finish/actions/runs/40246818450/job/121330018203)。这属于代码与跨平台回归，不计入真实照片质量通过。

已安装355df17逐字节匹配当前115个manifest文件。此前持久检查点再次从私有存储取回，ZIP完整哈希db3cdd2fb4bb0fbe8f21f536e67d3b8a76683ce2b819a8d9674cebb278252f3c一致；固定运行时恢复9文件并重复恢复，全部字节保持。V1完整解码1536×1024，哈希与本页记录一致。没有调用图像编辑器，没有伪造原图自动保存回执或原始私有账本。恢复路径改变未自动重绑旧记录。

当前真实Work空会话界面可加载，原清理后的浏览器无旧标签页可检查。没有重发结果未知的原上传；此轮没有照片已发送/自动选Skill/渲染事件，因此独立触发继续未验证。现有全幅imagegen接口仍无mask参数；未通过的自然度和天空局部边界不重新生成碰运气。其余真实场景、正式V2连续验收、原图片保存回执仍待完成。Windows修复不解除HOLD。
