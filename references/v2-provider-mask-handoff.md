# V2 Adobe 原始蒙版交接与安全降级（候选门禁）

此文件随 Skill 打包；仓库中的 docs/V2_PROVIDER_MASK_HANDOFF.md 记录更多工程证据。

Adobe 的 `image_select_by_prompt` 成功、选区尺寸相符或返回 image/png URL，都**不等于本地原始蒙版已经可核验**。预览接口可能缩小并重新编码图像，绝不能把 JPEG 预览、截图、重新绘制图或仅有 URL 当作来源已验证的原始蒙版。

当且仅当可信宿主实际获得：(a) 与相机原件二进制一致的独立提供方输入文件；(b) 原始无损 PNG 蒙版的全量字节；(c) 实际工具返回的 requestId、格式和宽高数据；方可在私有隔离目录使用：
`python scripts/run_photo_finish.py v2_native_entry ingest-mask ORIGINAL LINEAGE.json PROVIDER_ORIGINAL RAW_MASK.png PROVIDER_RESULT.json CANONICAL_MASK.png HANDOFF.json`

`PROVIDER_RESULT.json` 保留真实工具回执字段 success、requestId、outputMediaType、metadata.source_width/source_height/mask_width/mask_height，可信宿主明确记录 provider=Adobe 和 operation=image_select_by_prompt。该 JSON 不是远端签名，需真实文件独立校验。

成功导入只证明像素与来源技术校验；必须继续观察原片和蒙版：同源尺寸、目标主体漏选、天空/文字误选、复杂边缘、保护区域、可能的光晕。任何一项不能证明就 STOP，或基于实际照片判断保留原片；**不得**自动把失败重标为已保留，也不得假称 Adobe mask 已验证或正式 V1 通过。

本路径不提供内建自动语义分割或 iPhone 原生保存。运行时的本地已审查蒙版途径可独立评估，但不视为 Adobe 交接通过。