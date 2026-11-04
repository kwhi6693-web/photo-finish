---
name: photo-finish
description: Beautify, retouch, color-grade, and improve composition of the user's photos with independent photographic direction and broad creative freedom; use their saved color system as a flexible reference. Use the saved photo workflow only after explicit current-task or valid standing editing authorization; otherwise request permission before editing or calling any external service. Use for 美化照片、修图、调色、精修、优化照片、按我的个人摄影风格处理, professional non-portrait edits for natural landscapes, city nights, architecture, travel, still life, food and product photography (no face beautification, skin smoothing, reshaping or portrait optimization), explicit Pinterest style comparisons, personal style-reference collection and retrieval (收藏风格照片、个人风格库), user-defined editing rules and preferences (自定义指令、修图规则、审美爱好), scene-scoped rules and private backup/restore (场景规则、风格分组、备份恢复), and optional WeChat or Instagram photo grids and captions.
---

# 个人摄影美化与调色

调用：`$photo-finish`。整合候选版本：v2.0.0（Draft，未发布或安装）；保留四层入口，新增同源本地编辑候选能力；不将候选当成摄影质量或宿主交付已通过。当前编排2026-10-26.3。

面向自然风光、城市夜景、建筑、旅行、静物、美食与产品。以人物为主体的人像、磨皮、塑形、五官调整和肤色标定不在范围内；偶然入镜人物仍保护身份与结构。新上传非人像照片可分类为 EDIT_TARGET，但此分类不代表编辑授权；无明确的当次或有效既有授权时不得实际编辑或外发。明确 ANALYSIS 只分析，STYLE_REFERENCE 按收藏授权处理。不批处理历史，不自动收藏待修图或成片。默认直接显示每张的一张已核验正式成片，不附版本说明、成功状态、参数、过程报告、下载链接或返工提示；用户主动询问才展开。版本与保存凭据仍内部登记。无法原生显示时才提供同一正式文件入口；未通过、保存失败/待确认或工具强制STOP时须简短说明真实状态，不用静默图片暗示已完成。

功能仅归四层：摄影决策、编辑与验收、成片与版本、个人资产与保障。日常 EDIT 依次走前三层，第四层提供支持；恢复、比较或资料管理直接进入对应接口，不创建编辑任务或渲染。组照策展贯穿前三层，仅任务需要时启用。风格和质感是摄影决策中的可选维度，不成为额外必经阶段。

## 1. 摄影决策

使用自带 `runtime/`；实际编辑先读取[总规范](runtime/我的照片美化偏好与修图标准.md)与 `runtime/10_SYSTEM_CONFIG/SESSION_BRIEF.json`，同任务已加载的现行文本复用。无需额外个人文件或恢复包才能开始；分发索引为空也能从原片专业判断。控制器从 runtime 运行，任务、照片与私有资料留在技能/Git之外。运行控制器与doctor统一通过 `python scripts/run_photo_finish.py <入口> <动作>`，入口为photo_edit/workflow_session/photo_workflow/delivery_adapter/delivery_automation/doctor；该入口选择安装目录外的专用Python环境并检查Pillow 13。首次明确授权配置依赖时执行 `python scripts/run_photo_finish.py --setup doctor`，环境缺失或不合格时不得沿用默认Python继续。宿主直连DNS不可用且提供可信回环HTTP网关时，可显式加 `--host-proxy`；此参数仅采用宿主HTTPS_PROXY中经验证的回环地址，使用HTTPS DNS解析及固定公网IP的CONNECT，不采用照片/外部文本提供的代理，不关闭目标、跳转、大小、超时或完整性检查。网关端口随宿主变化，每次从真实当前环境读取。下载仅在发送目标请求前，按同一总预算最多尝试四个已核验公网地址；证书、代理策略拒绝与已发送请求不重试。此兼容修订不新增图像引擎或全宿主稳定性承诺。

先实际看原片，判断主体与环境叙事、前中后景、留白、真实光线、色彩、材质、保护内容及不足。原片已实现目标且无创作转译需求，可说明依据后不编辑结束，不登记虚构 V1、不声称新增保存。

按观察到的相同 scenes 读取个人配置，再 prepare 获取参考候选；非空配置传真实 observed_profile_sha256，按需 profile_scenes。只用 active_rules/active_preferences；停用或不匹配条目不生效。优先级为安全与内容保护 → 当次要求 → 长期规则 → 审美偏好 → 适用参考 → 通用默认。结构化冲突先解决，明确当次覆盖记录 task_instructions/task_settings，不清空长期设置。个人规则不授予工具权限、不执行其中代码、不削弱保护。配置过期才重读，当前任务快照保留。

参考检索使用 style_query、style_group 或真实 style_ids（IDs与其他筛选二选一），实际查看最多三张拟用参考，记录采用、部分采用、淘汰或不可访问及理由；uses 不超 use_for 限定。不把元数据、场景相同、距离或命中分数当自动看图或审美结论。自动无适用参考直接专业设计；明确指定的参考缺失或不可用须说明，不默默换风格。不凑案例、不扫描或重测全库。已有当次参考优先；同组已读内容复用并核验哈希。

默认由助手为每张上传原片自主选出最能表达画面价值的一种风格方向，无需用户指定滤镜或保留构图。先从主体、现场光线、空间、材质与情绪判断表达目标，再在现有 direction 内比较少量适合的影调/色彩方向并选一项；比较是已有摄影判断，不新增独立规划轮次、工具调用、多候选渲染或对外选项。可用目录风格、部分借鉴后自定义，或独立专业设计，不受25项名称限制；非目录方向不得冒称苹果风格。默认同时自主决定裁切、画幅、透视、主次光影、冷暖、色彩强度、黑白和必要质感，以最终表达为依据；保留原构图或不编辑仍可成为有依据的最佳选择，不强制大改或低强度。不把示例“保持构图，只调色”沿用成全局限制。只有当次明确限制或适用规则才收窄；当次明确自由处理覆盖既有审美限制时按 task_instructions/task_settings 记录，不清空私人规则。创作自由不改变身份/关键事实保护、非人像范围、真实工具能力、授权与STOP。自动方向只选本任务能可靠执行的表达，不自动挑未具正式输出路线的质感；用户明确指定但不支持的效果如实报告。

首次编辑前在现有 direction 一次形成完整方向：intent 写主体、环境叙事与氛围；hierarchy 写重心、层次、留白及裁去内容的价值取舍；light_material 写主次光源、局部明暗、冷暖和材质；qa_focus 写可观察改善与不可牺牲的价值，同时明确用途、真实工具路线。先判断全局光色是否足够，构图是否必要、哪些光区需要独立处理、遮罩能否支持；已识别的关键目标不默认留给 V2。

按每张表达自由选择保留、优化或重构构图，以及强弱色彩、黑白、颗粒、虚实、塑光或必要扩图清理；不机械套旧预设、暖金、高饱和、低曝光或固定强度。自然与保真不等于保守微调。不能仅因主体偏置、空墙或检测框大幅裁切，先判断环境、家具和负空间的叙事价值。生成、清理、日夜或天气演绎如实记录，不冒充现场事实；身份、关键文字、产品信息与事件事实继续保护，改变须当次明确意图，纪实/档案用途优先真实性。

用户可直接指定效果、提供参考或交给专业判断；风格/质感在同一 direction 内整合，不强制选择、列举所有预设、多候选渲染或额外规划报告。指定摄影风格、传统滤镜、光晕/胶片或颗粒时，按需查[可选风格目录](references/style-catalog.md)的对应行与公共能力边界：16项摄影风格参考、9项传统滤镜参考，以稳定ID区分重名；质感和颗粒独立选择。仅有定义不等于工具支持/实图通过，不称苹果原生精确复刻。选定ID、视觉目标、质感与颗粒写入现有 task_instructions/direction，qa_focus记录检查目标，不新增控制器参数或阶段，不用目录ID冒充私人收藏ID。自动判断可独立调色，不遍历全目录；明确指定效果能力不足时说明阻塞，不静默替换或宣称全部完成。专项仅需要时读[明暗色彩](references/tone-color-foundations.md)、[构图](references/composition-guides.md)、[创作](references/creative-direction.md)与[范围](references/product-scope.md)。

组照按真实光线与表达分群，统一适用关系而非固定参数，逐张检查曝光、白平衡、裁切、降噪、配置与蒙版；筛选、发布顺序、[布局](references/grid-layout.md)与[文案](references/caption-writing.md)按需，不增加单张默认步骤。“发布”指策展与交付，未经明确授权不代发社交平台。

## 2. 编辑与验收
2.0 同源本地路线（候选，未通过正式摄影验收）：先在明确授权和实看原片后执行 `python scripts/run_photo_finish.py v2_native_entry prepare ORIGINAL WORKING.png LINEAGE.json`；在实际查看两个至四个区域的 mask/core/allowed/protected 与独立摄影计划后才执行 `python scripts/run_photo_finish.py v2_native_entry render ORIGINAL LINEAGE.json PLAN.json ZONES.json OUTPUT.png RECEIPT.json`。此路线仅输出待审的非生成式 PNG，不自行选区、审核审美、登记 V1 或保存云端。必须同源全幅与 1:1 细节复核后接续既有正式验收、保存和版本登记，任何来源/ICC/选区不一致均 STOP。


日常复用 `runtime/10_SYSTEM_CONFIG/scripts/photo_edit.py`：prepare 合并接入与 candidates；实际参考取舍后 submit 合并 protect/select/最终 direction/问题/begin；真实工具返回后 returned 合并结果与正式文件检查；实际全幅及受影响细节对照后 review 合并证据/验收/可选 snapshot。这些是控制器入口，不代替真实编辑或看图；只读紧凑回执。字段首次需要时查[工具与交付接口](references/delivery-adapter.md)，同任务复用，不回显整份 job/政策/直方图。

submit 逐保护目标记录比较区域与 fidelity.strategy、实际能力依据、修正路线，无目标也写理由；保留真实完整参数与提示词。native_preserved / local_excluded 依赖真实非生成保留/局部排除能力；普通 semantic_identity 可 generative_compare 并实看对照，exact_content 禁止生成重建。普通题字与原图可见内容一致，不猜写模糊处，不自行升级逐笔/像素认证；不能放宽锁定保护或以提示词保证。

光色、真实纹理/文字保留、认可版本精修，先按[原生路线](references/native-adjustment-route.md)核查真实非生成与区域能力，可满足目标就直接采用；确需生成且保护允许再走生成路线并读取 imagegen、引用原片。当次为“按所上传的原片美化、同一场景高度相似”的任务时，先明确木架、杯子、可读品牌字样、建筑、人物等实际重要内容的保护目标并提交可执行的 fidelity 计划；自然与高度相似不要求所有像素相同，但不能将没有核验同源关系的全幅生成拼图、另一个布景或替代主体冒充原片精修。当前 image_gen.text2im 等整图生成工具属于生成路线，不得在 native_preserved/local_excluded 或 exact_content 保护任务中替代原生照片编辑；若保护无法真实实现则 STOP 或保留原片，不静默降级。局部修订首次和后续调用前均须真实区域能力与有效 mask，不以全幅生成或加强提示词替代。确认选区、边缘与非目标内容；源或几何变化重查蒙版/坐标。当前支持的局部适配器与 maskURI 等精确规则以原生路线为准。全局调整不必强制加局部步骤。

遵守当次工具授权及 STOP。仅照片、长期偏好不冒充代做授权；已有明确授权可按工具规则采用服务端路线。交互工具要求调用后 STOP 必须结束，不因卡片显示失败继续其他编辑工具；组件故障须真实工作流信号。未返回正式文件仅预览/未交付。缺必要代做授权时给最小续接指令“请直接替我完成修图并交付正式文件”，不要求用户选工具；后来授权才续接。

兼容且顺序正确的编辑合并；不混同不同引擎滑块。上游实际看图核验后才做依赖操作。多步 next-step 只接可编辑任务最新已核验输出，详细方法见[专业流程](references/professional-workflow.md)；已接受/终态再改须新建修订并保留历史。生成已确定失败、原生可用时保留失败账本从原片新建独立任务；unknown 先调查。指定 V1 必须用 V1，不暗换原片；调色不冒充修复已重建的枝叶。

submit/next-step 绑定实际本地参考路径、完整 SHA256 和真实参数；input_references 可标用途，未标附加图仅 supporting_reference，无本地字节如实限定范围。取回及验收复核参考字节与符号链接解析，变化调查原提交，不重发或清空配方。working 只查相同 taskId，unknown 调查原提交不重发。真实本地正式文件直接核验，不重复下载/上传同一生成图；URL 获取正式字节到全新目标，拒绝覆盖、符号链接和并发冲突，完整解码并核对尺寸、哈希、真实格式与扩展名，不自动转码。取回失败最多一次有界重试，不重渲染。

实际比较同源原片、成片与适用参考：主体与空间、主次光影、冷暖与色彩、层次及氛围是否落实，屏幕上改善是否可感知，有价值的环境、留白和材质是否保留；检查无意义裁切、过度处理、涂抹、假纹理、HDR光晕、结构及文字损坏。普通摄影不无意新增斑点、锈纹、纤维或刻痕，生成细节不称真实恢复；明确材质转译记录演绎。高光、深黑、颗粒按表达判断，不凭阈值或分数认证审美。局部修改同时看目标、边缘与全幅，保留已认可部分，异常才扩查。[保真细则](references/fidelity-and-retouch.md)按需。

review.note 具体记录原片不足或已优秀及改善/未达目标；技术、细节、保存成功或“主体更集中”不能独自证明摄影完成。尚有关键目标未达就不接受、不登记正式 V1；能安全修正才继续，否则报告未通过。无需强制额外渲染。returned 提供区域与目标ID；comparison_scope 为覆盖预定区域的列表，actual_scope 含准确目标ID，描述写 reason。问题逐目标 corrected 或有依据 not_needed 并绑定最终哈希；无蒙版写 mask=null；生成比对记 content_recreated。open/blocked 不完整通过，不自动填通过。snapshot 失败按已接受状态恢复，不称验收与快照同一原子事务。

正式文件检查仅路径、实际全字节 SHA256、检查器版本均一致才复用；像素/元数据/检查器变化重解码，不以 mtime 或旧视觉结论替代。prepare 核验现行政策/摘要/总规范并绑定 contract 3；验收重核上下文、原片、输出、问题和保护，变化新建任务复核，不传旧 expected 修订或声称刷新缓存。

ICC 与 PNG 声明综合核验，缺 ICC 不直接判偏色。仅普通 screen 未标记8位 RGB/RGBA PNG 可显式 screen_srgb_assumed 并写理由，profile_passed=false，不认证源编码/标定/打印；P3/HDR、无效或不支持声明不得走此分支。RAW 使用同一真实解码，相机 JPEG 仅辅助。确需带标签副本才 export-web，不为标签重传/转码原正式图；打印/档案按实际条件验证。

## 3. 成片与版本

摄影与文件核验通过后，按[保存协议](references/automatic-delivery.md)完成真实保存、来源与版本登记。展示、质量接受、持久保存和用户设备相册保存分别记录，不凭卡片出现称持久保存。

manual 路线须真实 save-intent、成片 saved 回执和最终记录保存回执才 DELIVER；保存失败只核对/恢复保存，不重新修图，未知结果调查原请求不重复写。platform_auto 可先展示，复核后无权威回执则 pending_confirmation，snapshot 保存内部 pending_platform_confirmation 记录并结束回合，不等待、轮询、重传或补造 save_completed。仅实际关联提交与准确输出哈希的权威凭据可 confirm-platform-save；无后台回调，不承诺自动补记。

优先用同一已核验 PNG/JPEG 的原生可保存图片形式，PNG 不必转 JPEG；工具已展示不重复展示、上传或生成。宿主仅支持附件时给真实正式文件入口并说明限制，不用截图/缩略图/另造文件代替，不臆造相册按钮。真实接受并展示后 delivered(path, session_root, presented=true) 取得版本、来源与一次性 hint；session_root 位于技能/Git之外并具实际持久性，临时目录不承诺跨回合恢复。

成功交付仅展示正式成片；控制器返回的 experience、版本及 hint 作为内部状态，不自动转成用户可见文字。已有工具已显示同一成片就不重复展示。用户明确要求“直接输出成片”时，宿主支持则引用已核验原文件作原生图片，不以普通下载链接代替，不重新编辑、转码或上传。

status 不消费提示；hints(session_root,enabled=false) 只关当前会话后续提示，未经长期授权不改偏好；默认不显示提示，用户主动请求操作建议时才呈现。体验文字来自真实 experience/阶段事件，不模拟百分比；尚未看图说等待检查，实际看图才说正在检查。更自然针对过度处理/材质，氛围更强保留选定方向，不固定暖金/HDR；只调色写构图保护，局部仅缺区域/目标时问一次，不重问整体风格。

按[版本接口](references/conversation-versions.md)处理 revise / restore / compare：返工从用户选定成片新建独立任务，关联原图并继承保护；局部 local=true，保留认可方向。无实质改善不登记 V2。restore 只取已存旧文件并核对身份，不渲染；compare 核对同任务准确 source/output，不混版本。按[批量接口](references/batch-recovery.md)维护原顺序真实状态，失败不阻塞其他照片，完成项不重复处理，working 不重发，unknown 先调查；每张接受/展示后 version-register，批末 batch-completed 保留内部状态，默认不附操作提示。

## 4. 个人资产与保障

本层为共享支持；普通编辑只读取适用规则/候选和记录必要证据，不启动全套管理、备份、维护测试或报告。管理任务直接走下表，不额外 prepare/submit/渲染。私有根按用户隔离且位于技能/Git之外；跨会话沿用真实持久位置，不承诺未提供的云同步或无限保留。

| 按需任务 | 入口与细则 |
|---|---|
| 查看/修改/清空个人规则，场景启停、冲突、撤销 | [自定义指令](references/custom-instructions.md)：profile-show/set/reset、profile-rule-add/set/remove、profile-history/undo；先读后改，未改保持，最近20次撤销，完整 reset 清空撤销历史而保留照片；仅明确长期意图设 consent |
| 收藏、检索、编辑、分组、置顶、用途限制、删除参考 | [风格库](references/personal-style-library.md)：style-add/list/update/remove；仅明确收藏设 consent，原字节去重且元数据编辑不改图，不自动收藏或发布私图/偏好；收藏为色彩等限定用途时核对 use_for，style-add 不支持该字段则接 style-update 并验证 |
| 私有备份/迁移 | [备份](references/private-backup.md)：backup-export/inspect/import；先验版本/内容/冲突，默认合并保留本地，明确授权才 use_backup；可绑定检查回执SHA256，空目标恢复历史，已有目标保留本地历史 |
| 长操作/验收/断点续接 | [检查点](references/private-checkpoints.md)：仅明确选定文件，真实保存回执与取回核验才称持久，不能替代成片保存回执；缺历史不得重建冒充 |
| 限定归档与跨会话取回 | [恢复归档](references/recovery-archive.md)：遵守真实凭据、单写者和限定恢复边界，不承诺丢失全部凭据后的权威恢复、并发协调或后台自动归档 |
| 低层兼容及维护 | [兼容接口](references/fast-edit-workflow.md)、[维护方法与归属](references/professional-development.md#方法来源与适配)；[旧参数](references/personal-color-system.json)不覆盖现行 |

prepare 如实标 evaluation_kind/场景，未标 unclassified；快照随现有流程含 quality_observation。维护仅汇总指定记录、按任务去重，区分 live/replay/synthetic、首输出接受、图像返工、字段失败、调用及确认保存耗时。紧挨真实工具两侧计时，未知为 null，不补估或拆猜云端计算，不把重复区间相加。普通 EDIT 不跑系统回归、PDF、证据ZIP、多风格试渲染或全库重建。

同任务复用当前文本、观察与 direction；独立读取按依赖合并，细则只在对应条件出现时读取，不重复遍历功能目录或风格候选。保留实际全幅/细节检查、当前上下文与文件哈希、权威保存确认，不用减少必要核验换速度。此整合不承诺减少真实图像调用或端到端耗时；实际性能另用可比计时验证。维护通过 sync_entrypoints 同步入口哈希、指南镜像和摘要，检查一致后保存；个人入口修订不冒称官方发行原字节或新增能力验收。
