# Photo Finish 2.0：非生成式同源构图裁切（候选功能）

在用户授权修图、已真正查看原片、实际 v2 原生多区域编辑输出及源身份审查通过后，允许按摄影判断裁切以突出主体和空间叙事。不要求每张照片裁切；已有原始构图最佳时保持不变。不得将新的裁切方案作为自动已获用户审美接受。

使用已通过来源检查的同一待审原生输出，不会修改源像素或重绘任何内容：

\`python scripts/run_photo_finish.py v2_native_entry reframe ORIGINAL LINEAGE.json PENDING.png PENDING_RECEIPT.json FRAME_PLAN.json CROPPED.png FRAME_RECEIPT.json\`

\`FRAME_PLAN.json\` 要求原始相机 SHA-256、working PNG SHA-256、实际父候选 PNG SHA-256、原工作坐标系 \`source_bbox_px: [left,top,right,bottom]\`（像素整数、右/下边界不含）、确实实看的 \`source_visually_inspected: true\` 和 \`crop_visually_inspected: true\`、具体 \`photographic_intent\` 与 \`visual_observation\`。

硬门禁：父 PNG 必须是未验收的真实 source-bound pending；原相机与工作图的实际 ICC/字节来源一致；父 PNG 全尺寸和 ICC 正确；裁切不越界，输出仅从真实父 PNG 原坐标原样取像素，**不插值、不生成、不放大**。独占新 PNG 和 JSON 回执，不覆盖旧图；回执失败只回滚本次未登记的新裁切文件。

裁切后仍须全幅及 1:1 复核，另行评价主体、留白、环境叙事、纹理、文字、输出尺寸和保存品质；候选回执永久标记 \`photographic_quality_accepted=false\`、\`formal_V1_registered=false\`，只有独立专业审查通过，才能进入后续正式 V1 与交付。此入口不自动选择裁切参数、不决定摄影审美、不实现 Adobe 原始蒙版交接、iPhone 原生保存或恢复。

本功能仅限 PR #47 隔离候选，旧版不动，用户私人照片/样本及来源 SHA 不提交到公开仓库。
