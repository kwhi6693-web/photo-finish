# 个人资料备份与恢复

按用户要求迁移或备份其私有风格照片、元数据、全局/场景规则和最多 20 条撤销记录。该备份含私人内容，放在技能与 Git checkout 之外；不能作为公开安装包或提交到仓库。普通修图不执行备份。

## 导出

从 runtime/ 调用 `photo_edit.py backup-export`：

```json
{
  "destination": "../../photo-work/personal-backup.zip"
}
```

destination 必须是私有目录下的新 ZIP 路径，不能位于图库内部、Git checkout 或技能目录。已存在则拒绝覆盖。默认使用当前个人目录，可传 library_root。导出冻结本次索引并核验所有已登记原图；只复制登记图片和配置，不扫描带走未入库照片、工作记录或程序。回执给出实际路径、完整 SHA256 和条目数量。

## 检查与导入

先调用 `backup-inspect {"archive_path":"实际备份路径"}`，可传目标 library_root。检查格式版本、完整清单、文件大小/哈希、图片真实格式、资料结构，并返回 new_styles、duplicate_styles、conflicts 和 archive_sha256。检查不会创建或改写目标目录。校验只证明内容完整，不证明备份来源可信。

```json
{
  "archive_path": "../../photo-work/personal-backup.zip",
  "consent": true,
  "style_policy": "keep_existing",
  "settings_policy": "keep_existing",
  "expected_archive_sha256": "从实际检查回执取得的完整SHA256"
}
```

用户明确要求导入即为 consent 授权，不重复询问。默认合并新增照片，重复照片按字节身份去重，已有元数据与已有个人设置保留；存在冲突须如实告知，不暗中覆盖。当前个人设置即使已清空也视为已有设置，不会被旧备份重新启用。`style_policy` / `settings_policy` 可以分别设 `use_backup`，只在用户明确希望用备份对应内容时使用；优先绑定检查回执 SHA256，防止导入的文件与检查时不同。

空目标恢复照片、元数据、规则和原撤销历史。合并现有目标保留本地撤销历史；明确使用备份设置时，会记录变更前的本地配置以供 profile-undo。既有任务保持自己的快照。用户需要完整恢复损坏目录时，先在新的私有目录恢复并核验，不删除原目录。

## 失败与边界

整个备份完成校验后才写入目标；数据库事务失败会撤销元数据，并清理本次新建照片，保留原有或其他已提交引用的文件。图片损坏、哈希不符、未来版本、重复成员、符号链接、路径跳出、未登记成员、加密 ZIP 和超限文件会明确拒绝，不静默忽略。

格式为版本 1 的专用 ZIP，包含 manifest.json、catalog.json 与 images/ 原文件。默认上限：总展开体积 2 GiB、单张 256 MiB、索引 16 MiB、最多 10,000 张照片；不隐式安装解码器。备份未加密；需要加密或跨设备自动同步时由宿主提供相应私有存储能力。助手必须根据实际文件保存回执说明保存结果，不能把生成路径当成跨会话保存保证。
