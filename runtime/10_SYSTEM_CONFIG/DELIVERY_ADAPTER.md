# 真实工具与交付接口 2026-10-26.3

权威runtime_policy.json#/execution_adapter_policy。助手仍执行真实工具和实际看图；接口不渲染、不上传照片、不安装后台回调。普通任务按总规范，本页仅字段需要时读取。

## 日常合并入口

从项目根运行`python 10_SYSTEM_CONFIG/scripts/photo_edit.py ACTION`，stdin为单个JSON对象。已有现行文本同任务复用，不回读全手册。只返回紧凑回执，完整参数及凭据在job；不默认cat整份job或SESSION_BRIEF。下列示例字段替换为本次真实观察，示例通过值不是执行证据。

1. 实际看原片后prepare合并接入与候选检索；此时不锁定最终direction：

```json
{"project_root":".","source_path":"/absolute/source.jpeg","path":"/absolute/job.json","tags":[],"evaluation_kind":"live","scenario":"本次实际场景","intent":{"subject":["architecture"],"light":["sunlight"],"material":["wood"],"expression":["depth"]}}
```

tags用实际场景A–L（J仅历史兼容，不用于当前产品）；不确定可空。evaluation_kind为live/replay/synthetic/unclassified，默认unclassified；只有实际调用/实际看图的任务才标live，测试夹具用synthetic，历史复放用replay。scenario填写实际场景，供统计分组。最终direction在submit中提供，route为native/creative/hybrid；output_use为screen/print_proof_requested。兼容prepare.direction仅作已验证草案；采用参考时必须在查看后显式提交最终direction，无参考的专业判断可沿用草案。新调用建议直接省略prepare.direction。可传首工具真实started_unix_ns和observed_skill_revision；不硬传旧技能修订作为期望版本。prepare失败不当成功，不绕过核心契约。

2. 实际查看拟采用参考后submit依次合并protect、select、最终direction、可选issues和adapter.begin；先持久化提交再调用真实工具：

```json
{"path":"/absolute/job.json","protections":{"requirements":[{"target":"inscriptions","level":"semantic_identity","requirement":"题字与原图可见内容一致，模糊处不猜写"}],"reason":"原片可见文字保护"},"selection":{"branch":"PROFESSIONAL_FALLBACK","decisions":[],"reason":"原片专业判断；仅真实零候选可空decisions"},"issues":[],"tool_name":"实际工具名","arguments":{"prompt":"完整实际提示词及全部真实参数"},"protected_regions":{"inscriptions":["实际需比较区域"]},"display_mode":"platform_auto","fidelity":{"inscriptions":{"strategy":"generative_compare","capability_basis":"实际工具生成整幅，不具备原像素锁定；仅要求可见内容一致","repair_route":"实际比对原图；可见改变则定向修正或换真实可用的原区域保留路线，未解决保持阻塞"}},"direction":{"intent":"本次用途与实际表达目标","hierarchy":"主体与环境关系","light_material":"真实观察及光影材质方案","output_use":"screen","route":"creative","qa_focus":["受影响细节与保护区域"]}}
```

fidelity须逐保护目标填写strategy、capability_basis、repair_route；无保护可省略或{}。strategy支持native_preserved/local_excluded/generative_compare，按实际能力选，不凭提示词声称原像素保留。exact_content搭配generative_compare在出图前拒绝；原区域保留方案不能用content_recreated=true通过。允许生成式普通后期，但发现可见差异必须修正或阻塞，不能改称保留。

requirements可空但reason不可空；每个返回候选均须在decisions记录reference_id、decision（adopt/partial/reject/unavailable）、viewed、scope、reason；adopt/partial必须实际看过。issues每项为issue_id、targets列表、observation。无保护目标则protected_regions={}。不能把示例空列表用于绕过真实候选。submit失败原账本不落任何部分决策。

3. 紧挨真实工具两侧计时，returned传path、submission_id、status、start_unix_ns、end_unix_ns及真实output_path或output_url，按实际传task_id/request_id/presented/geometry_changed。本地正式结果合并finish与check，并返回review_requirements中的原定比较区域列表和准确问题目标ID；这些只是结构提示，不含通过结论。返回visual_review_required表示仍须实际看图。URL-only按next先fetch正式字节，再check，不把URL当成文件。下载目标须全新；低层接口也原子排他发布，拒绝同名、符号链接和并发碰撞。PNG/JPEG实际格式不符扩展名时失败，使用正确新路径重取原结果，不重渲染或自动转码。working续同task，unknown先调查。接口不调用渲染、不编造视觉通过。

4. 实际检查全幅表达、受影响原生细节、去AI味及保护区域后review一次登记明确证据、接受并可选写内部快照：

```json
{"path":"/absolute/job.json","output_path":"/absolute/generated.png","events":[{"action":"review","arguments":{"output_path":"/absolute/generated.png","input_sha256":"实际当前输入SHA256","visual_passed":true,"profile_passed":false,"color_scope":"screen_srgb_assumed","color_assumption_reason":"仅普通屏幕解释未标记8位RGB，源编码未认证","note":"实际全幅/受影响细节/表达与去AI味检查结论"}},{"action":"protection","arguments":{"target":"inscriptions","output_sha256":"实际输出SHA256","status":"met","method":"manual_detail_comparison","content_recreated":true,"comparison_scope":["实际需比较区域"],"reason":"实际一致性结论"}}],"record_destination":"/absolute/pending_record.json"}
```

comparison_scope必须是文本列表，逐项覆盖submit的protected_regions原字符串；不能传一段描述。mask的actual_scope必须是目标ID列表，例如target=light_depth则actual_scope=["light_depth"]；全幅处理未用蒙版也用该目标列表，实际作用区域/边缘对照写reason且mask_path=null。任何错误都在事务前给出field/hint，不写部分验收；模板不自动填visual_passed/met/corrected。

review事件必须来自实际看图，profile_passed和color_scope按真实声明/用途填写，不能照抄示例。保护事件逐目标覆盖；无保护则不填。已登记问题先按FAST_EDIT_WORKFLOW.md的resolve/mask补齐，可在同events提交。允许review/mask/resolve/protection/mark/stage，不在终检重置保护/参考或提交渲染。record_destination省略则只验收；有值则验收后snapshot，快照失败保留真实已接受状态，按adapter.snapshot恢复，不重复生成。manual确认保存仍走后文真实回执。

正式文件检查按当前路径+实际全字节SHA256+INSPECTION_VERSION复用；像素/元数据/版本变化重解码。只减少重复解码，颜色、几何/蒙版、问题、保护、源与当前上下文及实际视觉验收仍逐项核验。accept不以本地文件时间或旧摘要替代现行哈希。兼容低层入口为delivery_adapter.py；以下保留恢复与特殊路线字段。


**首次正式成片前的完整摄影决策。**在第一次图像编辑调用前，将本片值得保留的视觉价值与真实不足落实到现有 direction：intent 写主体、环境叙事与最终氛围；hierarchy 写构图重心、前中后景及留白的作用，拟裁去的内容价值与取舍；light_material 写主次光源、局部明暗分离、冷暖色彩关系与材质；qa_focus 写原片到目标成片应可观察的变化及不可牺牲的价值。不能仅凭主体偏置、空墙面积或主体检测框决定大幅裁切；先判断环境、家具、负空间与光线是否构成叙事。原片已充分实现目标时有依据保留或无需编辑，不为明显变化破坏美感。

把既定方向映射到真实能力与完整执行：全局调整是否足够、构图是否必要、哪些局部光区需独立处理，以及保护/遮罩是否实际支持。兼容且顺序正确的操作尽量合并；确有摄影收益才增加步骤，不强制多候选或最少渲染次数，不把基础调色当作默认完成方案，也不以更高饱和、对比或锐度冒充表现力。调用前已可识别的关键层次问题在首次方案中解决，不留作用户要求“更有表现力”后的默认 V2。复用本轮看图与现有字段，不新增独立规划轮次、工具调用或日常报告；授权与 STOP 规则不变。

**首次正式接受门槛。**正式接受和登记 V1 前，在现有 review.note 中对照同源原片逐项说明：主体与空间关系是否合理；主次光影、色彩和层次是否落实既定方向；正常屏幕上改善是否可感知；有价值的环境氛围、留白与真实材质是否保留；有无无意义裁切、过度调色、假纹理或重要内容损坏。不能用“主体更集中”、技术检查或保存成功独自证明摄影目标完成。尚有已识别的关键摄影目标未达时，不接受、不登记正式 V1；仅在现有工具、授权与 STOP 规则内作必要修正，不能安全完成则明确未通过。以上为实际人工视觉判断，不是自动审美认证；中间步骤可检查为适合继续编辑，但不能据此宣布最终目标已完成。

## 参考检索参数

photo_workflow.py candidates可传intent，例如{"subject":["architecture","garden","foliage"],"light":["sunlight"],"material":["tile","wood"],"expression":["depth"]}。四个字段的值都是标签列表，每字段最多12项，缺少观察就省略，不传中文自由文本字符串。支持标签：architecture、garden、foliage、water、urban、portrait、sunlight、warm_light、soft_light、night、wood、stone、tile、glass、metal、depth、reflection、low_key。portrait仅为旧接口兼容标签，不用于当前人像修图；偶然人物继续受通用内容保护。标签来自本次实际看图，索引侧仅作文字元数据推断；不确定时省略intent或用空对象，保留原场景/色彩检索，不为填标签增加一轮图像调用。

## 调用与真实返回

begin字段：path、tool_name、arguments（完整实际参数对象）、display_mode（manual/platform_auto）、protected_regions（保护目标到比较区域说明列表，每个目标覆盖，无目标为空对象）。接口保存arguments_sha256；保留prompt和引用来源，不记录base64。begin保存submission_id后才调用真实工具，不把begin后的准备间隙当渲染时间。

调用代码紧挨真实工具的两侧观测：start=Date.now()；await真实工具；end=Date.now()。毫秒乘1000000传Unix纳秒单位，精度仍为毫秒。finish字段：path、submission_id、status（ready/working/unknown/error）、start_unix_ns、end_unix_ns及真实output_path/output_url/task_id/request_id。本地正式输出和URL互斥，output_path必须是真实可解码返回文件，不填预览或原片。平台已显示时presented=true，仅platform_auto且ready并有本地正式文件才允许。

finish原子登记参数、输出哈希、工具与render阶段区间。相同回执幂等复用；working仅轮询相同task_id并记新调用边界，unknown/error保持调查状态不重发。有意精修用next-step(path,tool_name,arguments)，只从最新已复核正式输出接续，不作未知提交重试。本地referenced_image_paths由submit/begin和next-step逐张绑定实际完整文件SHA256及角色。可在适配器层传input_references=[{"path":"/absolute/style.png","role":"style_reference"}]，路径必须确实出现在工具参数中；角色还支持edit_target、composition_reference、identity_reference、supporting_reference。这是适配器元数据，不传给图像工具。未指定的源/当步输入记edit_target，其他附加图记supporting_reference；远程/对话图未取得本地字节时明确不作文件哈希保证。保留原参数路径并复核链接解析与字节。新鲜度与最终验收检查参考字节，变化则调查既有提交而非重发；兼容回填保留并锁定已绑定配方，next-step本地附件须含最新已复核输出，验收必须绑定当前submission_id的调用或有效调查证据。完整参数和文件绑定仍不保证生成结果像素级可重现。

未知提交后来有真实调查结果时，resolve-unknown(path,submission_id,evidence_path)关联原提交，不重新调用生成。证据JSON须有basis=observed_tool_result、相同tool_name和input_sha256、实际status=ready/working、真实output_path/output_url/task_id及非空note；presented按实际观察填写。接口核验正式字节，保留调查证据哈希，不补造缺失渲染时间，不增加虚构工具次数。只有实际状态获证实才使用；猜测或预期不能作证据。

## 实际复核与屏幕范围

photo_workflow.check检查正式文件，实际看全幅、受影响原生细节及保护区域。workflow_session.review传真实input_sha256、visual_passed、profile_passed、note；保护另传comparison_scope说明实际比较区域。提示词、bbox或区域说明本身不证明视觉通过。

未标记8位RGB/RGBA PNG且direction.output_use=screen时，可明确color_scope=screen_srgb_assumed、profile_passed=false、color_assumption_reason非空。accept只作有范围的屏幕接受，绝不将profile_passed改true或认证源编码。P3/HDR、无效或未支持声明不可用此分支；print_proof_requested不接受屏幕假设。

## 展示、质量和保存

status返回display、quality、profile_check_passed、professional_color_calibrated、persistence及controller_next。presented=false保持display=unobserved，不写成已展示；platform_auto仍不另行上传/重复展示来制造观察证据。自动展示可先于复核，不等于自动通过。接受后平台无真实保存回执时plan=AWAIT_PLATFORM_SAVE_CONFIRMATION，表示待确认而非失败。snapshot(path,destination,brief)保存内部pending_platform_confirmation记录，不冒充最终归档，不重复显示或上传生成图，结束回合前不等待后提交保存，不创建自动任务。

实际收到权威平台保存证据才confirm-platform-save(path,evidence_path)：证据须含source=platform_save_receipt、status=succeeded、本次准确output_sha256、library_file_id；若回执带submission_id则必须匹配（平台无需回传仅本地生成的令牌）。无这些可核验关联保持待确认；接口不搜索、下载或上传生成图来制造证据，不把预期保存改称已确认。当前无后台回调，独立取得新证据后才对账，不承诺自动执行。

确认后delivery_automation.complete生成/复用最终记录，record-intent/record-saved保存记录；DELIVER不重复显示已展示图片（display_needed=false）。manual路线沿用真实保存回执、save-intent和saved，不混用平台预期保存。

## 兼容与验证

低层原接口保留历史和协议兼容，正常新任务必须经适配器，不用手写mark代替调用回执。旧任务不补造时间或保存状态。验证分别列明合成协议、实际源图输出复放、实时工具调用及真实平台回执，未知部分如实标记，模拟回执不能称生产实测。

## 连续实测统计

review返回quality_observation，snapshot同一次写入该观察，沿现有内部记录保存，不增加日常工具往返。评估类型须如实声明，默认unclassified；live是调用者声明并关联真实调用凭据，不等于独立审美认证。

维护时运行`python 10_SYSTEM_CONFIG/scripts/delivery_metrics.py report`，stdin为`{"paths":["/absolute/job.json","/absolute/saved_record.json"]}`。只读指定账本/快照；同源哈希+任务起点+修订去重，矛盾快照须明确选择现行一份，不默默覆盖。实际样本、复放、合成分组，不将旧记录自动改写为本版实测。

first_output_acceptance显示分子/分母/比率，仅已知质量结论参与；图像有意精修另记image_revision，字段/事务失败单列，不当作重渲染。相同提交的轮询仅计一次生成提交。API真实调用区间去重后取中位数；photo_save仅真实回执确认的终点，缺测null，不冒称整体对话速度。小样本和同源重复不证明跨场景稳定性。

## 中文展示协议

photo_edit的experience为真实状态的中文视图，独立显示generated、quality_accepted、display_observed、persistence_confirmed。仅有正式文件仍等待实际看图，不冒称检查中或已通过。没有真实保存回执显示“成片已生成，保存状态待确认。”，错误说明附可执行恢复入口，不能把保存或未知渲染变成二次提交。新成片提示仅首次交付，批次末统一一次；关闭提示仅会话生效，长期保存另需授权。

体验指标另含average_revision_rounds（显式样本内每个原片/任务根的返工轮数）、duplicate_render_count（相同输入与完整参数的不同实际提交）、persistence_confirmation和accepted_output_median_seconds。后者仅从任务接入到正式文件/实际视觉接受，不包括接入前或宿主展示延迟，不冒称完整对话耗时；缺测null，复放/合成与live分开。独立修订保留根来源，样本不全会低估返工次数。


## 原文件图片展示与附件回退

此处仅约束宿主呈现，不新增渲染、上传、转码或版本登记接口。PNG/JPEG 的原字节、完整 SHA-256 与既有正式记录保持不变。

| 实际宿主能力/状态 | 本次交付动作 | 证据边界 |
| --- | --- | --- |
| 工具已自动展示，或 platform_auto 展示状态未知 | 仅附真实状态文本，不重复显示、上传或生成 | 未观察到不能推断未展示；图片出现不等于保存成功 |
| manual，宿主支持引用已核验原文件作为图片 | 仅一次引用同一原文件显示 | 不造截图、缩略图、JPEG副本；设备相册保存需实际观察 |
| manual，宿主仅支持附件/下载链接 | 提供同一正式原文件的有效下载入口，说明原生保存操作未验证或不可用 | 不把附件称为已支持一键存入相册，不冒称用户已保存 |

若图片展示未能确认，不自动再上传或重复显示来探测；保留原文件入口并如实说明。仅交付测试不调用 delivered/restore/revise 或补写旧版本记录。协议回归使用合成夹具；真实宿主展示、下载可用及用户设备保存须分别记录，不能由协议测试替代。
