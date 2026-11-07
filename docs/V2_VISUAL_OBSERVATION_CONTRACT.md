# V2 方案 C：来源绑定摄影观察与决策编译门禁

> 未发布的 PR #47 工程候选。这个模块不读取照片像素、不能自主分割、不批准质量，也不是正式 V1。

## 真实调用顺序

1. 取得当前用户对这张非人像原片的**实际编辑授权**。只读分析不等于授权编辑或上传。
2. 运行已验证的原片预处理：

   `python scripts/run_photo_finish.py v2_native_entry prepare ORIGINAL WORKING.png LINEAGE.json`

3. **助手必须真正查看原片**（复杂边缘要检查实际细节），根据可见画面写私有的 `OBSERVATION.json`。不能从文件名、元数据、预设或用户要求推断“已看图”。
4. 基于确切原片和工作文件身份运行：

   `python scripts/run_photo_finish.py v2_native_entry decide ORIGINAL LINEAGE.json OBSERVATION.json PLAN.json DECISION.json`

5. 三种返回状态：
   - `EDIT_PLAN_READY_MASKS_UNVERIFIED`：产出来源绑定摄影方向；**尚未有蒙版或编辑许可的技术证据**。必须继续 `ingest-mask` 或另一条真实已审查的本地蒙版途径，并检查实际工具能力、边缘与像素保护；之后才考虑 `render`。
   - `RETAIN_ORIGINAL`：基于实际视觉判断明确保留原片；不产生编辑输出、不伪造 V1。
   - `STOP`：观察缺失、照片源改变、可靠性/收益不确定、非人像范围被突破、目标不支持等；不创建虚假的计划。
6. 真正的编辑输出、正常及 1:1 摄影质量独立审核、正式交付与版本登记，是后续不同门禁。**任何阶段不得自行升级为正式成片**。

## `OBSERVATION.json` 必需字段

以下均应填写来自**真实画面视觉观察**的具体事实，不是为了凑齐字段而编造描述。

| 字段 | 允许值/内容 |
|---|---|
| `camera_original_sha256` | 实际原始相机文件 SHA-256 |
| `source_sha256` | prepare 得到的受 ICC 管理的 WORKING PNG SHA-256 |
| `observation_origin` | `assistant_visual_inspection` 或 `human_visual_inspection` |
| `original_visually_inspected` | 真实已看图才写 `true` |
| `subject_scope` | 必须是 `nonportrait_scene`（偶然入镜人物仍保护身份） |
| `geometry_change_requested`, `generative_edit_requested` | 当前原生路线均不支持；写 `false` 才符合能力 |
| `scene`, `principal_subject`, `attention_entry` | 实际场景、主体、视线进入点 |
| `secondary_discovery`, `spatial_relationship` | 可见的环境事实与前中后景关系 |
| `source_light_evidence` | 原片真实光线证据，不虚构光源 |
| `fixed_content_to_preserve` | 实际照片里不允许改变的纹理、文字及结构 |
| `visible_improvement_goal`, `edit_reason` | 可核验的摄影改善目标与原因 |
| `review_note` | 具体看图说明（至少 25 字符，不能以空泛人设替代） |
| `risk_flags` | 明确列出风险：`none`、`mixed_lighting`、`deep_shadow`、`architecture_sky_edge`、`foliage_sky_edge`、`readable_text`、`fine_object_boundary`、`reflective_surface`、`transparent_object` |
| `scene_complexity` | `simple` 或 `complex`；高风险会自动提升为 complex |
| `critical_edges_visually_inspected` | 复杂场景只有实际检查边缘后才能写 `true` |
| `edit_necessity` | `edit_needed`、`retain_original` 或 `uncertain`；不确定会 STOP |
| `tonal_strategy` | 需要编辑时使用 `preserve_highlights`、`balance_local_depth`、`lift_subject_shadows` 或 `subdue_distractions` |
| `retain_reason` | 明确保留原片时，必须有具体现象支持的理由 |

编译后仅有 `PLAN.json`（仅在 EDIT/RETAIN 状态）与 `DECISION.json`。外部输入不能执行为代码，输出不覆盖旧文件。来源不同、未实看、没有审查复杂边缘、无改善理由时均停止；不能用 “True” 字段代替对实际照片的视觉证据。

## 真实性界限

- 代码只是**观察到计划的受约束编译器**，不是视觉模型。实际观察必须由当前助手/用户通过显示原片提供。可以减少用户手填 12 项摄影计划，但不能宣称无需看图。
- 风险分类是输入证据约束，不能证明真实选区准确；高风险蒙版还需源对齐、语义检验、边缘及 1:1 对照。
- `PHOTO_DIRECTION` 不等于 `EDIT`。图片原件、私有 SHA、工具返回临时 URL、个人风格/私人记录不得上传公开仓库。
- 跨平台 CI、候选构建、真实修图、正式 V1 与 iPhone 保存具有独立验收边界。
- 本轮直接使用 PR #47，保持 Draft；不合并、不发布、不安装、不修改历史版本。
