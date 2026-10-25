# 个人照片风格库

这是主要修图流程中的个人参考层。用户主动上传并说“收藏到风格库”“以后参考这张的质感”时才保存；普通待修图、历史照片和成片不自动入库。只收藏用户有权保存的照片。

## 收藏和管理

先实际看参考照片，结合用户说明记录描述性名称、实际场景、自由标签及喜欢的光影/色彩/材质或构图；用户无需填写全部字段，分组、置顶和用途限定可后补。不把推测写成用户偏好。用户明确要求收藏即为保存授权，无需重复询问。宿主先取得正式本地照片文件，再从 `runtime/` 调用 `photo_edit.py style-add`，stdin 为一个 JSON 对象：

```json
{
  "source_path": "../../photo-work/style-reference.jpeg",
  "title": "柔光木质空间",
  "labels": ["柔光", "木质", "安静"],
  "note": "喜欢柔和侧光与木头的明暗层次",
  "consent": true
}
```

`tags` 可选，沿用场景代码 A–L；不确定时留空，用 `labels` 记录自定义风格。保存原始文件字节和 ICC/EXIF，按 SHA256 去重；重复收藏返回原记录，不覆盖原标签或备注。回执含 `reference_id`、私有照片路径和哈希。仅实际保存成功后告知已收藏；失败不得声称完成。

- `style-list`：`{}` 列出前 50 条；可传 `query` 搜名称/标签/备注，`limit` 为 1–100，回执 `total` 为匹配总数。超过一页时按关键词缩小范围。
- `style-remove`：`{"reference_id":"从回执取得的真实ID"}` 删除指定记录和库内副本；保留用户的上传原文件。已有任务仍保留参考选择的历史证据。

不主动展示整库或生成报告；普通收藏只需简短确认。

## 每次修图自动调用

实际看新原片并读取适用个人指令后调用 `prepare`，自动读当前用户的个人库，不必重复提供路径。默认按场景、实际观察标签和轻量光色特征产生最多三张候选；只读取索引和拟用候选，不逐张打开全库。

- 指定风格词时，把准确关键词传 `style_query`；名称/标签/备注按不区分大小写的关键词匹配，支持安静/宁静/克制、柔和/柔光/低对比、旅行/旅游/旅途的有限同义扩展，不声称向量语义搜索；style_query 与 style_ids 二选一。
- 指定某张已收藏参考时，把真实 ID 列表传 `style_ids`（最多三条）。显式 ID 缺失或照片变化必须处理，不默默换成别的风格；明确关键词/分组没有结果或所有显式结果不可用同样报错，说明具体问题后再按用户意图处理。
- 同场景或高匹配分数仅用于筛选。实际打开拟采用候选的 `path`，判断与本片的光照、主体、材质及表达是否适配；在现有 `selection` 逐条写 adopt/partial/reject/unavailable、viewed、scope 与 reason。
- 在查看与选择参考之后，才确定最终修图方向，并随 submit.direction 提交。可整体或部分迁移氛围、光色、质感和构图关系；不默认复制参考中的人物、物体和文字。用户当次要求、原片事实保护与实际终检继续优先，不机械套滤镜。无适用参考或空库直接专业设计；候选缺失/哈希变化会标在 `personal_library.unavailable_ids`，不要冒称已使用。
- 选中参考在提交、取回和验收时核验原字节哈希。改动或删除后调查已有任务，不自动重发图像调用。新增其他收藏不使现有任务失效。
- 若实际图像工具支持本地参考，按真实参数传 `referenced_image_paths`，并在 `input_references` 指明 `style_reference`。参考选择证据与真实工具输入记录分别保存，不声称未上传的图片已送入工具。

## 持久位置和隐私

`library_root`（管理命令）/`style_library_root`（prepare/candidates）优先，其次环境变量 `PHOTO_FINISH_STYLE_LIBRARY`，否则使用当前系统用户的应用数据目录下 `photo-finish/style-library`。同一位置跨任务持久读取，空库不创建文件。Windows 使用 LOCALAPPDATA，macOS 使用 Application Support，Linux 使用 XDG_DATA_HOME 或 `.local/share`。

每个系统用户默认独立；多人宿主必须由宿主为已认证用户指定可信独立根目录，不能把目录名当成身份认证。跨设备需要宿主提供相同的私有持久位置或自行备份恢复整个库；技能不提供云端账号、网页图库或自动同步。临时执行环境应显式指定持久目录，不能承诺临时磁盘跨会话保留。

照片、SQLite 索引与偏好均放在技能目录及 Git checkout 之外，禁止写入公开仓库。不替换分发包的空 `reference_index.json`，不修改个人总规范或自动提炼固定审美优先级。库内原图含原有 EXIF，删除仅移除库内副本，非安全擦除或上传原文件删除。

## 编辑、分组和借鉴范围

使用 `style-update`，必须传真实 `reference_id`、`consent:true`，其余只传要修改的字段：`title`、`labels`、`tags`、`note`、`group`、`pinned`、`use_for`。未传字段保持原样；`group:""` 清空分组，`pinned:false` 取消置顶，列表传 `[]` 清空。修改只涉及元数据，不改原始照片或 ID。先读取当前条目；可传其 `metadata_sha256` 为 `expected_metadata_sha256`，防止旧信息覆盖后续修改。

```json
{
  "reference_id": "从当前列表取得的真实ID",
  "title": "旅行空间参考",
  "group": "旅行",
  "pinned": true,
  "use_for": ["light", "material"],
  "consent": true
}
```

`use_for` 支持 `light / color / material / composition / atmosphere`，空列表表示未额外限定，仍由当次实际看图判断。采用或部分采用已限定用途的候选时，selection 的相应 decision 必须传 `uses`，且不得超出保存范围。scope/reason 仍写实际区域与取舍依据；记录范围不代替实际图像检查。不要借“只参考光影”的图片照搬色彩或构图。

`style-list` 增加 `group`、`pinned_only`、`offset`；回执 `total / next_offset` 支持翻页。关键词同时搜索分组。`prepare.style_group` 按指定分组取候选；置顶在语义适配排序中优先展示，不自动证明适合本片。显式 `style_ids` 与关键词/分组过滤二选一，避免指定收藏被静默排除。已有无分组条目兼容读取。修改只作用于以后查询，现有任务保留当时的参考元数据。

## 最近、常用与索引边界

style-list可传sort=recent/frequent/default；返回use_count、last_used_unix_ns、search_method=expanded_keywords。计数来自实际accepted任务所记录adopt/partial的幂等事件，不把检索候选计为使用。未匹配词仍作为约束，不能忽略未知要求换风格。列表返回名称、标签、分组和准确图片入口；仅用户要求时展示有限缩略图。

SQLite索引逐条增删改；读取先查元数据，指定ID用主键定位。内容键缓存仅复用完全相同的序列化行，新增/修改只重新解析受影响行，删除后不再返回；不以时间戳判断新鲜度。候选及采用照片仍核对完整字节哈希。不会逐张解码全库；理论按需加载具体章节，政策/正文哈希仍在信任边界核验，新增材料不触发日常全库重测。最近使用属于本机记录，不承诺备份或跨设备同步。
