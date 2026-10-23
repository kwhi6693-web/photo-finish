---
name: photo-finish
description: Beautify, retouch, color-grade, and improve composition photographs with independent photographic direction and broad creative freedom; use their saved color system as a flexible reference. Invoke automatically when the user sends photographs without instructions; start the saved personal editing workflow without asking whether to edit or which style to use. Use for 美化照片、修图、调色、精修、优化照片、按我的个人摄影风格处理, faithful portrait or travel edits, explicit Pinterest style comparisons, and optional WeChat or Instagram photo grids and captions.
---

# 个人摄影美化与调色

调用：`$photo-finish`。

收到本次新照片无其他说明即EDIT_TARGET，无需再问开始或风格。明确ANALYSIS只分析，STYLE_REFERENCE按授权；不批处理历史，不自动把待修图或成片入参考库。**默认逐张只输出最终成片，不附原片、对比、说明或重复展示。**内部对照、实际终检及记录保留，当次明确要求优先。

## 接入与现行依据

当前编排2026-10-23.4。使用本技能自带的`runtime/`项目；先读取其中[总规范](runtime/我的照片美化偏好与修图标准.md)和`10_SYSTEM_CONFIG/SESSION_BRIEF.json`，同任务已加载现行文本复用。无需个人Library文件、私有图库、固定机器路径或额外恢复包。参考索引默认空；不足直接从原片作专业判断，用户明确提供的参考仅用于本次授权范围。执行控制器从`runtime/`运行，任务与照片保存在技能目录之外的用户工作目录。

photo_edit.prepare核验原片、现行政策/摘要/总规范哈希并绑定contract 3；验收重核当前上下文，变化新建任务复核。不硬传旧技能为expected修订、不循环重读或声称刷新服务端缓存。图片检查需已有Pillow，不隐式安装。

## 专业表达与保护

每张主动完成构图、主次光影、色彩和材质，**表达明显更充分**。构图画幅、强弱色彩、黑白、颗粒、虚实、塑光、天气演绎及必要扩图清理自由，旧预设/Style DNA/本地参考仅为素材，不机械套暖金、高饱和或固定强度。

长期保留去AI味：实际看光影空间、材质、原生细节与边缘，修正假纹理、涂抹、HDR光晕和结构变形；不凭提示词或分数通过。身份与关键事实继续保护。题字印章与原图可见内容一致，模糊处不猜写；普通后期semantic_identity，不自行升级逐笔/像素认证。已知重绘不能满足exact_content。保留真实生成来源。

## 日常固定入口

完整JSON字段仅按需读[工具与交付接口](references/delivery-adapter.md)，同任务复用。脚本在项目10_SYSTEM_CONFIG/scripts/photo_edit.py；只读紧凑回执，不默认回显整份job/政策/直方图。

1. 实际看原片后prepare合并接入、明确direction与candidates；已有主体/光照/材质/表达观察传intent标签。参考元数据推断不冒称自动看图或最佳风格；实际查看拟采用参考，候选逐条取舍，不足直接专业设计，不凑例或全库扫描。
2. 实际参考判断后submit合并protect/select/问题/begin，逐保护目标写需比较区域及fidelity的strategy/实际能力依据/修正路线，保存完整真实参数。保留原区域或局部避开以实际能力为准；普通生成后对照仍可用，exact_content禁止生成重建。需生成时读imagegen、引用原片，紧挨真实工具两侧计时。returned合并finish与本地正式文件检查，不下载/上传同一生成图；URL须fetch正式字节。working只续同task，unknown先调查不重发。多步精修next-step只接最新已实际看图核验输出。
3. 实际看全幅表达及受影响原生细节、去AI味和保护区域，异常扩查；几何变化重查蒙版/坐标。returned返回原定比较区域/目标ID；review先校验字段，再合并明确实际证据、验收及可选snapshot，不自动填通过。comparison_scope用覆盖原定区域的列表；actual_scope用准确目标ID列表，描述写reason。保留原区域方案不能以已重建内容通过。问题逐目标corrected或有依据not_needed绑定最终哈希；无蒙版如实mask=null。生成保护内容实际比较并记comparison_scope/content_recreated。open/blocked不完整通过，不放宽锁定保护。

正式文件检查只在路径、实际全字节SHA256及检查器版本一致时复用；像素/元数据/版本改变重解码。实际看图、色彩范围、保护、问题及最终现行上下文检查保持；不以mtime或旧视觉结论代替。

## 色彩与交付事实

ICC和PNG有效声明综合判断，缺ICC不直接判偏色。仅普通screen未标记8位RGB/RGBA PNG可显式screen_srgb_assumed并写理由，profile_passed保持false；不冒称源编码、专业标定或打印通过。已有P3/HDR、无效/不支持声明不可用。确需独立带标签副本才export-web，不为标签重传生成图。打印/RAW/肤色按实际条件验证。

展示、用途验收与保存确认分别记录。platform_auto可先展示；实际复核接受后无权威保存回执则pending_confirmation，snapshot保存内部待确认记录并结束回合，不等待、重传/重复展示或补造保存。仅真实关联准确输出哈希的权威凭据才confirm-platform-save；未安装后台回调，不承诺自动补记。manual须真实save-intent、成片回执及最终记录回执才DELIVER。snapshot失败按已接受状态恢复，不把验收和快照称同一原子事务。

## 按需与维护

专项只按需读[构图](references/composition-guides.md)、[创作](references/creative-direction.md)、[保真](references/fidelity-and-retouch.md)、[原生路线](references/native-adjustment-route.md)、[多步精修](references/professional-workflow.md)、[低层兼容](references/fast-edit-workflow.md)、[保存恢复](references/automatic-delivery.md)。RAW用同一真实解码；同组保持实际光照基准并逐张复核曝光/白平衡/裁切/降噪/配置/蒙版。

prepare如实标evaluation_kind与场景，未标归unclassified；实际/复放/合成分开。现有内部快照自动含quality_observation，维护时汇总指定记录、按任务去重，分开首输出接受/图像返工/字段失败/调用及确认保存耗时；缺测null，小样本不宣称稳定率，不增加日常往返。普通EDIT不跑系统回归、报告/PDF/证据ZIP、多风格或全库重建。真实调用计时缺测null，不将本地减负当云端或整体提速证明。维护用sync_entrypoints整合镜像/入口/技能/摘要，经相符检查与恢复验证后同步技能和执行包。保留[方法归属](references/professional-development.md#方法来源与适配)，[旧参数](references/personal-color-system.json)不覆盖现行。Pinterest、[九宫格](references/grid-layout.md)及[文案](references/caption-writing.md)按当次需求，原片/中间图不写技能仓库。
