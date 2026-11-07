# V2 源绑定摄影观察与执行决策（候选门禁）

该文件随候选 Skill 分发；独立研发背景见仓库 docs/V2_VISUAL_OBSERVATION_CONTRACT.md。**无用户当次编辑授权不得调用图像编辑/上传**。

**观察先于参数：** 实际打开原片；观察主体、环境叙事、可见亮暗、前中后景、真实纹理、可读文字、需要保护的元素、复杂边缘。禁止通过文件名、场景标签、模型预设或未经核实的布尔字段宣称看过图。

先运行：
`python scripts/run_photo_finish.py v2_native_entry prepare ORIGINAL WORKING.png LINEAGE.json`

在私有目录中记录 `OBSERVATION.json`，依据实际观察填写：
- `camera_original_sha256`（原始相机文件）和 `source_sha256`（WORKING.png，与 LINEAGE 完全一致）
- `observation_origin` 为 `assistant_visual_inspection` 或 `human_visual_inspection`；真正看过才可设置 `original_visually_inspected: true`
- `subject_scope: nonportrait_scene`；当前原生方案不支持的 `geometry_change_requested: false`、`generative_edit_requested: false`
- 具体画面事实字符串：`scene`、`attention_entry`、`principal_subject`、`secondary_discovery`、`spatial_relationship`、`source_light_evidence`、`fixed_content_to_preserve`、`visible_improvement_goal`、`edit_reason`、`review_note`（不得空泛）
- `scene_complexity: simple|complex` 与真实观察到的 `risk_flags`，从 none、mixed_lighting、deep_shadow、architecture_sky_edge、foliage_sky_edge、readable_text、fine_object_boundary、reflective_surface、transparent_object 中明确选择；复杂边缘只有实看后才写 `critical_edges_visually_inspected: true`
- `edit_necessity: edit_needed|retain_original|uncertain`。编辑需要 `tonal_strategy` 为 preserve_highlights、balance_local_depth、lift_subject_shadows 或 subdue_distractions；保留需要具体 `retain_reason`。不确定必须 STOP，不可以冒充有依据的保留。

执行：
`python scripts/run_photo_finish.py v2_native_entry decide ORIGINAL LINEAGE.json OBSERVATION.json PLAN.json DECISION.json`

输出只可能为 EDIT_PLAN_READY_MASKS_UNVERIFIED（尚无蒙版）、RETAIN_ORIGINAL（没有新成片）或 STOP（无计划）。控制器检查来源字节与观察证据完整性，只是将实际看图结果编译为结构化摄影方向，**不自身执行视觉识别、自动选区、调光、审美评分、正式 V1 登记或 iPhone 保存**。

EDIT 状态必须另行取得实际来源绑定、逐像素与语义审查通过的蒙版，并通过 1:1 边缘、保护区和摄影质量独立门禁后才可正式编辑交付。不得用单元测试中写的“看过”来证明真实看过。私人原片/哈希/工具 URL 不提交公开仓库。