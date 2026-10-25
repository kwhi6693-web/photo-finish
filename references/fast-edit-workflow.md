# 默认照片编辑接口 2026-10-25.1

日常决策读总规范一次。日常优先photo_edit.py的prepare/submit/returned/review合并入口，完整字段按DELIVERY_ADAPTER.md；本页低层接口仅兼容/诊断按需读取。平台本地正式文件和自动展示/延后保存不走本页manual上传分支。本页仅接口/恢复按需读取；机器契约为runtime_policy.json#/fast_edit_workflow及protection_policy、color_delivery_policy。专业摄影判断覆盖所有分支，依据当次目的统筹构图与光色，强度保持开放。以下检查保护信息与真实执行，不限制审美。

## 接入与候选

从项目根以JSON stdin运行 `python 10_SYSTEM_CONFIG/scripts/photo_workflow.py prepare`：

```json
{"project_root":".","source_path":"/absolute/source.jpeg","path":"/absolute/job.json"}
```

prepare合并策略/五源摘要及总规范哈希、原图哈希/全尺寸/ICC基线及任务。首工具实际起点可传started_unix_ns；不补估计。需现有Pillow，无依赖不安装，bootstrap/timing/读账本可用标准库，涉及图片核验与验收不能绕过。来源明确时规则读取、接入与上传可独立并行。

实际看原片并读取适用全局指令后，由主入口photo_edit.prepare检索候选；低层photo_workflow.candidates接受path、project_root、tags（A–L）及可选intent/私有库筛选。自动检索先过滤场景不符者，未标注场景的私人参考仍可参与；明确ID、关键词或分组表达的选择可越过场景提示。排序依次考虑私人来源、观察标签与索引元数据的适配、置顶、场景交集、相对光色距离及稳定次序，最多返回3张。没有已知场景标签仍可检索私人库，不把未分类等同空库。

style_match.py使用source_pixel_features_v2，在原支持色彩模式中应用有效ICC后生成内存分析特征；不重测全库，不计算82项参数。measured_full来自收藏时的特征或冻结公开索引。元数据命中、置顶与相对距离不证明视觉适用性、概率或审美质量；源哈希及特征版本约束复用。实际查看拟采用候选后逐条取舍，并随submit记录最终方向。自动空/不适用检索允许专业回退；明确筛选无结果或结果全部不可用须报告具体问题。最终方向锁定前可因真实观察调整筛选，锁定后不能替换参考。

## 渲染前保护与取舍

新任务采用contract 3：prepare保存已核验项目路径、修订与配置/总规范哈希；accept轻量重核当前上下文，变化则拒绝新验收，新建任务并按当前要求复核。旧contract 2/无上下文任务仅追溯，历史已完成保存与记录不改写。initialize默认绑定控制器所在项目，也可显式project_root；优先使用prepare。

用workflow_session.py transact一次提交真实已完成的protect/select：

```json
{"path":"/absolute/job.json","events":[{"action":"protect","arguments":{"requirements":[{"target":"inscriptions","level":"semantic_identity","requirement":"题字、印章与画作可见内容及布局与原图一致；原本模糊处保持，不猜写补清"}],"reason":"本片普通摄影后期的原图可见内容保护"}},{"action":"select","arguments":{"branch":"PROFESSIONAL_FALLBACK","decisions":[{"reference_id":"实际候选ID","decision":"reject","viewed":false,"scope":"索引说明","reason":"具体材质或光照不适配；未声称看过原图"}],"reason":"基于本片独立设计"}}]}
```

示例需替换为真实候选；返回空列表才可decisions=[]。decision支持adopt/partial/reject/unavailable；adopt/partial必须viewed=true并实际查看。不得以未读参考推断库中无实例。protect只设置一次，在first_render或任何review之前锁定；可为空但须说明理由。semantic_identity保护指定关键语义/身份；exact_content保护逐笔内容等严格要求。提示词新增严格条件必须写入契约；路线能力不足不能在验收时放宽。新验收不得沿用缺少此契约的旧任务，旧账本仅保留历史。

## 实际处理与文件检查

书画、题字与印章默认以“与原图可见内容一致”为准：保留内容、字形/笔触关系、印章和画作布局，原本模糊难辨的地方保持，不猜写或补清。允许所需光影与调色。仅因无法独立辨读、未逐笔鉴定，不判失败；不额外做每字释读、作者/真伪考证或像素级认证。实际改字、增删或明显变形/重绘改变可见内容，仍须修正。普通后期在渲染前用semantic_identity落实此要求；只有当次明确逐笔/像素级要求或严格档案用途才选exact_content，不自行在提示词升级条件。

按表达与已确认保护条件选择真实支持的路线；工具输入查看/结果预览不可省。生成编辑遵守imagegen技能并引用真实原片，不保证提示词能锁住细字。先检查上游输出，再作依赖几何/色彩的局部。

photo_workflow.py check参数path、output_path；几何改变传geometry_changed=true，返回文件/ICC/PNG色彩及亮部观测，accepted=false不提供视觉验收。局部可传input_path和mask_path；像素范围检查不证明语义覆盖。必要预览后视觉与独立文件工作可并行；验收等待两者真实完成。

下载workflow_session.py download只发一次urllib请求，临时文件完整解码/尺寸/颜色声明/可选SHA256核验后再替换；失败保留已有目的文件。需要现有Pillow；不能只凭签名发布。

## 逐目标验收

transact事件action包括issue/mask/resolve/review/protection/mark/tool及渲染前protect/select，每项含arguments，不能覆盖path或嵌套事务。实际事件按顺序核验，失败整批不落账，每job单写者。

问题逐目标corrected或有可观察理由not_needed；open/blocked不能完整通过。corrected与not_needed均绑定最终输出哈希。not_needed无需蒙版；已有真实review时可省略output_sha256，由接口绑定最新已审阅输出；没有review则必须显式提供实际查看的输出哈希。新输出不能沿用旧结论。corrected另需实际范围核验，全幅未用蒙版如实mask=null。独立保护目标用protection记录target、output_sha256、status（met/failed/unverified）、method（manual_detail_comparison/pixel_comparison/documented_transform）、content_recreated（布尔）、reason。证据绑定最新review的输出；exact_content已知重绘不能met，未知保持unverified。不能靠一句演绎说明关闭硬保护。

去AI味沿runtime_policy.json#/photographic_naturalness_policy执行；visual_passed须包含对当前实际成片摄影质感的判断。假纹理、涂抹、光影矛盾、结构/文字变形等按既有问题记录修正，未解决不完整通过；不新增阶段或自动打分。

review参数output_path、input_sha256、visual_passed、profile_passed、note；明确screen_srgb_assumed时另传color_assumption_reason，profile_passed保持false且用途须screen；只记录实际看图结果，同时直接检查当前文件。省略color_scope自动按文件推导；假设图只能web_srgb_assumed或更弱，无效/未支持只能visual_only；未知8位RGB PNG仅普通screen可按DELIVERY_ADAPTER.md明确screen_srgb_assumed，且profile_passed不能为true。managed表示有效声明的色彩解释，不是专业标定。

日常photo_edit.review或兼容transact可传accept_output_path；accept重新核对接入时绑定的当前政策/总规范上下文、真实源/输出哈希，复用同哈希绑定的实际文件检查凭据并交叉核对色彩范围、全部问题/保护及参考选择。通过不自动补造时间。实际图像判断、全幅及原生细节、作品文字和蒙版边缘仍须完成；脚本不能代替。

## 色彩与可恢复导出

PNG有效优先级cICP > iCCP > sRGB > cHRM/gAMA，低优先级回退不同不直接算冲突。同级矛盾、无效与有效但未支持分别报告；ICC描述名不作为空间识别。已有未支持HDR等声明不能假定为无标记sRGB。

普通分享未标记8位RGB/RGBA静态PNG确有需要时用photo_workflow.py export-web：

```json
{"input_path":"/absolute/generated.png","output_path":"/absolute/web.png","assume_untagged_srgb":true,"assumption_reason":"普通分享按未标记RGB的sRGB解释，源编码未确认","source_kind":"generated","receipt_path":"/absolute/color.json"}
```

只补元数据，逐像素、尺寸及IDAT不变；保留原生成文件，不复制相机P3到生成像素。非sRGB须真实转换，严格色准未确认继续标记。图片和记录先预检/暂存，发布失败仅回滚本次新建文件。中断后显式resume_existing=true只允许核验与确定性输出字节完全一致的图片，再补缺失记录；绝不盲目覆盖。

## 手动保存终点与精简记录（仅manual）

实际观察mark记录first_render/local_final_ready/visual_accepted，tool记录调用名称、真实起止和状态，可与其他凭据同一transact提交；缺时null。只写mark不能证明保存。成片成功保存后调用workflow_session.py saved，参数path、result_path（当前Library上传helper真实结果JSON），可传实际观测的observed_unix_ns；核对成功、路径和文件身份、输出哈希后持久化save_completed，重复同结果幂等。保存失败不落终点。

再调用workflow_session.py record，参数path、destination、brief、recipe，默认仅在accepted且已有成片成功回执/保存终点后创建final精简JSON，无强制82项参数。未闭合快照须显式draft=true，永久标draft，不冒充最终记录；验收transact可同时传save_result_path，绑定接受的输出哈希与尚不存在的新回执路径；或验收后用save-intent（path、result_path）登记。随后实际保存成片，saved只接受与该意图匹配的本次回执，旧成功记录不能证明新字节已保存。先确认成片回执再生成并保存最终内部记录，避免永久漏终点。save_completed截止“成片成功回执”，明确不含随后记录上传；完整对话交付时间另行观测，不能冒称已测。记录失败可用相同成片回执续接，不重复渲染/上传照片。

prepare/candidates/check/review凭据写入/accept/transact自动记录本地操作span及异常，实际看图另行记录。外部工具调用用stage记录stage、start_unix_ns、end_unix_ns和ok/error/cancelled；阶段支持intake/context_read/visual_diagnosis/reference_matching/upload/render/download/visual_verification/file_verification/review_receipt/acceptance/save/ledger_transaction。本地失败span写入同job的.timing.json旁证（源哈希+任务起点绑定），不改变原账本；归档任务时带上旁证。用finish的status=failed或cancelled、reason及实际unix_ns结束无法完成的任务，终态不可修改或再验收，继续工作新建任务。timing分别返回各阶段、缺测null、原始span、sum/union及已观测保存或失败/取消窗口覆盖率；空隙不归为已测模型/云端阶段。文件只改元数据，只有像素和有效色彩解释均等价且实际有凭据时才复用视觉判断，不自动继承。

## 系统维护验证

仅系统变更运行全部verify_*.py、workflow_integrity.validate（含嵌套镜像/独立开发配置、总规范及本地技能版本/哈希）、技能校验、受影响真实文件及恢复包连通测试，复评速度并同步总规范/技能/政策/摘要/执行包。日常EDIT不生成测试报告、PDF、证据ZIP或重建全库；fast_delivery.build仅旧Lightroom研究兼容，完整参数仅按实际路线/用户要求。

原生保真调色的能力、实际文件与保存接口按NATIVE_ADJUSTMENT_ROUTE.md执行（技能内见native-adjustment-route.md）；不能以预览URL或JPEG预览代替正式输出。

自动续接按delivery_automation.py与AUTOMATIC_DELIVERY.md（技能内automatic-delivery.md）；现行上下文优先于入口旧版本，只有成片和最终记录的真实保存都确认后才DELIVER。

专业视觉意图/光线材质优先于候选色彩距离，多步编辑用direction/next-render保留原片与当步来源；全幅及受影响细节实际复核。完整接口按需见PROFESSIONAL_WORKFLOW.md（技能内professional-workflow.md）。
