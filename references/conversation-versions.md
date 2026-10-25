# 会话版本与快捷返工

所有动作经 photo_edit.py，stdin 一个 JSON。session_root 是宿主为当前用户当前会话选定的私有持久目录，必须在技能与 Git 之外；不同会话不能共享游标。索引只是定位器，每次选择均核验已接受账本与完整文件哈希。旧版任务可显式 version-register，不伪造历史编号。

- `delivered`: `{path, session_root, presented:true}`。只有实际已接受并实际展示才调用；返回版本、来源、中文保存状态及一次性 hint。工具自动展示无需另行展示。重复调用不再返回提示；不要先调用再等待展示。平台展示和这里的提示领取不等于保存回执。
- `hints`: `{session_root, enabled:false}`。关闭当前会话提示；不写长期偏好。省略 enabled 查看设置。
- `versions`: `{session_root, series}`。有序轻量元数据；未逐项检查照片，选择时才校验。
- `current-version`: `{session_root}`。读取跨回合当前选定版本，核验正式文件。
- `restore`: `{session_root, series, version:"V1"}`。核验并取回已有文件，仅更新会话游标，不写历史账本/图片、不调用编辑。缺失或哈希变化即失败，不静默重渲染。用户明确要旧版时可重新展示该已有文件，不附新成片提示。
- `compare`: 同 restore 输入。只返回所选任务 source 与 output 的准确路径/哈希，以及系列原片；用户明确选择后才展示。修订的 before 是该修订实际输入，不拿系列原片冒充其直接输入。
- `revise`: `{session_root, series, version:"V2", path, request:"只改天空，让层次更明显", local:true}`。仅 prepare 新任务，不调用渲染。返回父版、原片、保护要求、比较区域与已认可方向。读取本次适用个人规则后可传 observed_profile_sha256 等 prepare 参数，不能覆盖选定源文件。随后实际参考判断、submit、真实工具、returned、实际视觉复核及 review。新输出接受后登记成为下一个版本；从 V1 分支仍使用递增新编号，来源保留 V1。

保护要求不得删除、改写或降低；局部修订自动要求保留构图、人物及已认可方向。参考区域和原片必须在真实终检中比较，不将保护要求当成像素保证。源版本和系列原片均保留绑定。长期规则仍仅经明确授权修改，局部反馈不自动成为偏好。

索引使用事务和唯一任务键防止重复编号/提示。SQLite 不替代照片保存；私有目录是否跨设备/跨会话可用由宿主能力决定。无持久位置时如实说明恢复边界。
