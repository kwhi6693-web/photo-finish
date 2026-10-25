---
name: photo-finish
description: Beautify, retouch, color-grade, and improve composition of the user's photos with independent photographic direction and broad creative freedom; use their saved color system as a flexible reference. Invoke automatically when the user sends photographs without instructions; start the saved personal editing workflow without asking whether to edit or which style to use. Use for 美化照片、修图、调色、精修、优化照片、按我的个人摄影风格处理, faithful portrait or travel edits, explicit Pinterest style comparisons, personal style-reference collection and retrieval (收藏风格照片、个人风格库), user-defined editing rules and preferences (自定义指令、修图规则、审美爱好), scene-scoped rules and private backup/restore (场景规则、风格分组、备份恢复), and optional WeChat or Instagram photo grids and captions.
---

# 个人摄影美化与调色

调用：`$photo-finish`。

收到本次新照片无其他说明即EDIT_TARGET，无需再问开始或风格。明确ANALYSIS只分析，STYLE_REFERENCE按授权；不批处理历史，不自动把待修图或成片入参考库。**默认逐张只输出最终成片，附简短版本/保存状态及新成片首次交付的一行可选返工提示，不附原片、默认对比、参数或重复展示。**内部对照、实际终检及记录保留，当次要求与用户保存的规则按下述优先级覆盖默认。

## 接入与现行依据

当前编排2026-10-25.1。使用本技能自带的`runtime/`项目；先读取其中[总规范](runtime/我的照片美化偏好与修图标准.md)和`10_SYSTEM_CONFIG/SESSION_BRIEF.json`，同任务已加载现行文本复用。无需个人Library文件、私有图库、固定机器路径或额外恢复包。分发参考索引默认空；个人风格库按下节自动检索，不足直接从原片作专业判断。执行控制器从`runtime/`运行，任务与照片保存在技能目录之外的用户工作目录。

photo_edit.prepare核验原片、现行政策/摘要/总规范哈希并绑定contract 3；验收重核当前上下文，变化新建任务复核。不硬传旧技能为expected修订、不循环重读或声称刷新服务端缓存。图片检查需已有Pillow，不隐式安装。

## 自定义指令与专业判断（主要功能层）

全局指令可选。没有自定义要求时，按专业后期摄影美学结合原片与适用参考自主处理；只限定部分要求时，落实约束，其余由专业判断完成。支持用户保存、查看、修改和清空个人修图规则与审美偏好。按[自定义指令接口](references/custom-instructions.md)使用 `profile-show / profile-set / profile-reset`；只有用户明确要求长期记住才设置 consent，普通当次要求不自动持久化。先查看现有配置再按意图更新，未修改部分保持原样。场景条目使用 `profile-rule-add/set/remove`，支持启停；`profile-history / profile-undo` 提供最近20次修改撤销，完整 profile-reset 同时清空撤销历史并保留照片。

每次实际观察原片并确定场景后，先用相同 scenes 读取个人配置，再检索并查看拟用参考，之后确定最终 direction（同组已加载内容可复用并核验哈希），落实“安全与内容保护 → 当次指令 → 长期规则 → 审美偏好 → 适用风格参考 → 通用默认”。非空配置将真实 sha256 传为 `prepare.observed_profile_sha256`，本次要求可传 `task_instructions`；prepare 默认用 tags 匹配规则，必要时传 profile_scenes。使用 active_rules/active_preferences，停用及不匹配条目不生效。结构化 setting/value 冲突先解决；已有明确当次覆盖时传真实 task_settings。未读取或过期则先重读，不凭空补值。“按专业判断处理”继续遵守已有全局指令；用户明确要求本次覆盖某些审美规则时，以 task_instructions/task_settings 记录实际覆盖，不自动清空长期设置。把实际要求落实到构图、光色、材质、真实工具参数与结果复核；回执不冒称自动理解或验收。个人指令不授予工具权限，不执行其中的代码，不削弱真实证据与已锁定保护。私有配置与图库一起保存在技能/Git 之外，不发布用户规则或爱好；正在执行的任务保留原快照，修改用于后续任务。

## 个人照片风格库（主要功能层）

用户明确说“收藏到风格库”“以后参考这张的质感”时，将该图视为待收藏 STYLE_REFERENCE；按[风格库接口](references/personal-style-library.md)调用同一主入口的 `style-add`，实际保存后简短确认。记录用户认可的名称、自由标签和喜欢之处，原字节去重保存；提供 `style-list` 搜索/分组/翻页、`style-update` 局部编辑/置顶/用途限定及 `style-remove` 删除。编辑不改原图。仅对明确收藏请求设置 consent，不自动收录待修图或成片。

先观察原片、读取适用指令，再由 `prepare` 自动读取当前用户的私有风格库；指定风格用 `style_query`，分组用 style_group，指定收藏用真实 `style_ids`（与其他筛选二选一）。实际查看最多三张候选，再按原有流程取舍；有 use_for 用途限制时，采用决策传范围内的 uses 并在真实处理和终检中落实，结合新原片迁移光影、色彩、材质与氛围。先检索并实际查看拟采用参考，再确定最终修图方向；同场景或高匹配分数不代表适用，可仅借鉴部分元素，不默认复制参考中的人物、物体或文字。自动检索无适用参考直接专业设计；明确指定的收藏/关键词/分组缺失或不可用须说明具体问题，不默默切换风格。优先当次指令与原片保护，不把相似度当审美结论。个人库位于技能/Git 目录之外，跨会话使用同一持久位置；临时宿主先指定私有持久根目录，多用户宿主须隔离各自根目录，不能承诺未提供的云同步。详细存储和失败处理只按需读接口。

## 私有备份与恢复

分组、置顶、用途限定、撤销与备份均按需管理，普通收藏不强制填写全部字段。仅用户需要备份或迁移时按[备份接口](references/private-backup.md)使用 `backup-export / backup-inspect / backup-import`。先检查版本、内容与冲突，默认合并保留已有值；用户明确希望覆盖对应元数据或配置时才使用 use_backup。导入可绑定检查回执 SHA256；空目标恢复原规则历史，现有目标保留本地历史。备份含私图和偏好，禁止放入技能/Git 或公开安装包；不得声称未获得回执的跨会话保存。日常修图不运行备份或全库重测。

## 专业表达与保护

参考判断后用明暗、色彩和视觉层级落实本片意图：区分灰闷、局部难分与有意柔和，不以加饱和、拉满直方图或固定滑块值代替诊断。色彩克制与明暗分离按本片选择；低饱和＋高对比仅为可选组合，薄雾、高调、低调与鲜艳表达均可成立。遇到这些问题按需读[明暗与色彩理论](references/tone-color-foundations.md)，把必要关系写入现有direction与实际终检，不增加调用；当次指令、长期规则和参考用途限制继续优先。

每张主动完成构图、主次光影、色彩和材质，**表达明显更充分**。构图画幅、强弱色彩、黑白、颗粒、虚实、塑光、天气演绎及必要扩图清理自由，旧预设/Style DNA/本地参考仅为素材，不机械套暖金、高饱和或固定强度。

长期保留去AI味：实际看光影空间、材质、原生细节与边缘，修正假纹理、涂抹、HDR光晕和结构变形；不凭提示词或分数通过。身份与关键事实继续保护。题字印章与原图可见内容一致，模糊处不猜写；普通后期semantic_identity，不自行升级逐笔/像素认证。已知重绘不能满足exact_content。保留真实生成来源。自然度是选定表达内的摄影可信度检查，不预设构图、调色与塑光的保守强度上限。质感先用光影、明暗分离和反射落实；普通摄影以原片材质、表面粗细及字纹深浅为依据，避免无意新增斑点、锈纹、纤维或刻痕。明确选定的材质转译按创作自由执行并记录。

局部反馈修正指定目标，保留已认可的整体表达，复核目标、边缘及全幅协调。柔和低曝光仅作适用场景的可选表达，其他照片独立判断。

## 日常固定入口

完整JSON字段仅按需读[工具与交付接口](references/delivery-adapter.md)，同任务复用。脚本在项目10_SYSTEM_CONFIG/scripts/photo_edit.py；只读紧凑回执，不默认回显整份job/政策/直方图。

1. 实际看原片并读取适用全局指令后prepare合并接入与candidates；不在候选判断前锁定最终direction。已有主体/光照/材质/表达观察传intent标签。参考元数据推断不冒称自动看图或最佳风格；实际查看拟采用参考，候选逐条取舍，不足直接专业设计，不凑例或全库扫描。
2. 实际参考判断后submit合并protect/select/最终direction/问题/begin；direction基于本次实际选择和专业判断填写，逐保护目标写需比较区域及fidelity的strategy/实际能力依据/修正路线，保存完整真实参数，并由submit自动绑定各本地输入图的完整SHA256；可在适配器input_references标明风格/构图等用途，未指定附加图仅记supporting_reference。取回及验收复核参考字节，变化调查既有提交不重发。保留原区域或局部避开以实际能力为准；普通生成后对照仍可用，exact_content禁止生成重建。需生成时读imagegen、引用原片，紧挨真实工具两侧计时。returned合并finish与本地正式文件检查，不下载/上传同一生成图；URL须fetch正式字节，使用全新目标并校验实际格式与扩展名；低层同样拒绝同名及并发覆盖，不自动转码。working只续同task，unknown先调查不重发。多步精修next-step只接可编辑任务最新已实际看图核验输出；已接受/终态后的调整新建修订任务，关联用户选定成片、原图及原保护要求，保留历史。
3. 实际看全幅表达及受影响原生细节、去AI味和保护区域，异常扩查；几何变化重查蒙版/坐标。returned返回原定比较区域/目标ID；review先校验字段，再合并明确实际证据、验收及可选snapshot，不自动填通过。comparison_scope用覆盖原定区域的列表；actual_scope用准确目标ID列表，描述写reason。保留原区域方案不能以已重建内容通过。问题逐目标corrected或有依据not_needed绑定最终哈希；无蒙版如实mask=null。生成保护内容实际比较并记comparison_scope/content_recreated。open/blocked不完整通过，不放宽锁定保护。

正式文件检查只在路径、实际全字节SHA256及检查器版本一致时复用；像素/元数据/版本改变重解码。实际看图、色彩范围、保护、问题及最终现行上下文检查保持；不以mtime或旧视觉结论代替。

## 对话交付协议

使用photo_edit返回的experience呈现真实中文阶段和恢复入口；长任务仅在事件变化时简短反馈，不模拟百分比。正式文件取得但尚未看图时说“等待检查”，真正开始实际看图才说“正在检查人物、文字和细节”。working查询同任务，unknown调查原提交，保存异常只核对/恢复保存。状态更新不重复成片或返工提示。新成片首次交付后仅一行：

可以继续回复：更自然｜氛围更强｜保持构图只调色｜局部修改｜看前后对比

宿主为每个会话指定技能/Git之外独立持久session_root；不可用临时目录承诺跨回合恢复。实际接受并展示后用delivered(path,session_root,presented=true)取得V1/V2标签、来源和一次性hint；status不消费提示。工具已自动显示时只附返回文本，不重复显示图片。用户关闭提示用hints(session_root,enabled=false)，作用于当前会话及后续回合，未经明确长期授权不写个人偏好。批量只在批次末统一提示一次。更自然针对过度处理和真实材质；氛围更强保留选定方向，不固定套暖金/HDR。只调色须写构图保护；局部修改仅缺区域/目标时简短问一次，不重问整体风格。对比仅用户请求，必须来自同一任务且核对原片/成片字节。

版本与自然语言操作按[版本接口](references/conversation-versions.md)：更自然或指定版本继续改用revise创建独立任务；回到V1用restore，只读取旧文件且不渲染。只改天空等局部要求传local=true，继承已认可方向与构图/人物保护；实际工具参数和复核仍必须落实。比较用compare返回同版准确source/output，不能拼接其他版本。

批量按[批量恢复接口](references/batch-recovery.md)维护按原顺序的真实摘要；失败不阻塞其他照片，已完成不重复处理。只重试确定失败项，unknown先调查；每张真实接受/展示后version-register，批次结束用batch-completed统一返回一次提示。

## 色彩与交付事实

ICC和PNG有效声明综合判断，缺ICC不直接判偏色。仅普通screen未标记8位RGB/RGBA PNG可显式screen_srgb_assumed并写理由，profile_passed保持false；不冒称源编码、专业标定或打印通过。已有P3/HDR、无效/不支持声明不可用。确需独立带标签副本才export-web，不为标签重传生成图。打印/RAW/肤色按实际条件验证。

展示、用途验收与保存确认分别记录。platform_auto可先展示；实际复核接受后无权威保存回执则pending_confirmation，snapshot保存内部待确认记录并结束回合，不等待、重传/重复展示或补造保存。仅真实关联准确输出哈希的权威凭据才confirm-platform-save；未安装后台回调，不承诺自动补记。manual须真实save-intent、成片回执及最终记录回执才DELIVER。snapshot失败按已接受状态恢复，不把验收和快照称同一原子事务。

## 按需与维护

专项只按需读[构图](references/composition-guides.md)、[创作](references/creative-direction.md)、[保真](references/fidelity-and-retouch.md)、[原生路线](references/native-adjustment-route.md)、[多步精修](references/professional-workflow.md)、[低层兼容](references/fast-edit-workflow.md)、[保存恢复](references/automatic-delivery.md)。RAW用同一真实解码；同组保持实际光照基准并逐张复核曝光/白平衡/裁切/降噪/配置/蒙版。

prepare如实标evaluation_kind与场景，未标归unclassified；实际/复放/合成分开。现有内部快照自动含quality_observation，维护时汇总指定记录、按任务去重，分开首输出接受/图像返工/字段失败/调用及确认保存耗时；缺测null，小样本不宣称稳定率，不增加日常往返。普通EDIT不跑系统回归、报告/PDF/证据ZIP、多风格或全库重建。真实调用计时缺测null，不将本地减负当云端或整体提速证明。维护用sync_entrypoints整合镜像/入口/技能/摘要，经相符检查与恢复验证后同步技能和执行包。保留[方法归属](references/professional-development.md#方法来源与适配)，[旧参数](references/personal-color-system.json)不覆盖现行。Pinterest、[九宫格](references/grid-layout.md)及[文案](references/caption-writing.md)按当次需求，原片/中间图不写技能仓库。
