# 📷 Photo Finish

> 从专业摄影与艺术指导出发，让照片的构图、光色和材质表达更充分，同时保留可信的摄影质感。

[English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md)

[![Agent Skill](https://img.shields.io/badge/Type-Agent%20Skill-3f4856?style=flat-square)](SKILL.md)
[![Version](https://img.shields.io/badge/Release-1.4.0-c45a2f?style=flat-square)](https://github.com/kwhi6693-web/photo-finish/releases/latest)
[![Validation](https://github.com/kwhi6693-web/photo-finish/actions/workflows/validate.yml/badge.svg)](https://github.com/kwhi6693-web/photo-finish/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-2f855a?style=flat-square)](LICENSE)

![Photo Finish — 方向、处理、复核](docs/assets/photo-finish.svg)

## ⚡ 快速开始

从[最新正式发布页](https://github.com/kwhi6693-web/photo-finish/releases/latest)下载 [最新技能安装包](https://github.com/kwhi6693-web/photo-finish/releases/latest/download/photo-finish.zip)与 [SHA-256 校验文件](https://github.com/kwhi6693-web/photo-finish/releases/latest/download/photo-finish.zip.sha256)。上述下载链接始终指向最新正式版。核对哈希后，安装解压得到的 `photo-finish/` 目录。GitHub 自动生成的 Source code 压缩包包含整个仓库；用于安装技能的是 `photo-finish.zip`。版本变化和升级说明见[更新记录](CHANGELOG.md)。

将整个仓库作为 `photo-finish` 技能安装。`SKILL.md`、`references/`、`scripts/`、`agents/`、`assets/` 和 **`runtime/` 必须一起保留**。执行包已经包含，无需个人资料库文件或额外恢复包。

```text
使用 $photo-finish 处理这张照片。
```

默认逐张只输出最终成片，不附原片、前后对比、参数或说明。内部原片对照、实际看图验收和记录继续执行。当次明确要求优先。

```bash
git clone https://github.com/kwhi6693-web/photo-finish.git
cd photo-finish
python -m venv .venv
# 按所用终端激活虚拟环境。
python -m pip install -r requirements.txt
python tools/doctor.py
```

宿主需要提供看图、真实图像编辑和文件访问能力。Python 依赖不包含图像生成服务；技能不收集 API Key，也不隐式安装外部工具。

**先检索风格，再确定方向：**观察原片并读取可选全局指令，检索并查看个人风格参考，再结合专业后期摄影美学确定最终方向。无自定义指令时专业自主处理；仅限定部分要求时，其余自主判断。首版的创作自由、内容保护、实际复核和成片交付要求保留。

## ✨ 核心能力

| 专业方向 | 实际处理 | 质量复核 | 交付 |
|---|---|---|---|
| 从原片建立意图，按需采用授权参考 | 自由构图、光影、调色、局部精修与材质 | 全幅表达与受影响原生细节 | 逐张仅输出成片，验收与保存分开记账 |

- 表达默认明显更充分，主动处理主次、层次、色彩关系和质感。
- 保留、优化、重构构图同等可选，不限定轻裁、固定画幅或统一暖金色。
- 长期保留去 AI 味：检查空间、反射、透视、塑料感、涂抹、假纹理与光晕。
- 书画题字按原图可见内容保持，模糊处不猜写；严格逐笔或像素保真只在明确要求时启用。
- **个人照片风格库**：主动收藏喜欢的照片，记录名称、标签与喜欢之处；每次修图自动检索最多三张适用参考，可按关键词或收藏 ID 指定，并支持查看、搜索与删除。
- 分发参考索引默认空。个人库无适用实例时，直接依据本片作专业判断。
- 绑定原片与成片哈希、完整真实参数、保护方案、实际复核和计时，不以方案或提示词代替执行。

## 自定义指令与爱好

用户可以保存自己的长期修图规则和审美偏好，并查看、修改、删除单条或清空。每次调用先读取个人配置，再结合原片建立处理方向；本次要求优先，临时尝试不会自动改写长期爱好。

```text
以后按这些规则修图，并记住我喜欢的光影和质感。
查看我的修图规则和偏好。
这次按另一种色彩处理，不改变我的长期偏好。
```

主入口新增 `profile-show / profile-set / profile-reset`，个人配置与图库一样独立私有保存，不进入公开仓库。详见[自定义指令接口](references/custom-instructions.md)。

## 管理、场景适配与备份

- 风格照片支持修改名称/标签/备注、分组、置顶和指定借鉴范围，列表支持筛选及翻页，原始照片保持不变。
- 规则可按场景生效，支持启停、结构化冲突提示及最近 20 次修改撤销；完整清空会清除撤销历史并保留图库。
- 私有照片、元数据、个人规则和修改历史可导出、检查、导入。默认合并保留已有内容，空目录可完整恢复；备份不进入公开仓库。

```text
把这张参考分到“旅行”，只借鉴光影和材质。
这条规则只用于夜景，先停用人像那条规则。
撤销刚才的规则修改；检查备份后合并到我的个人图库。
```

详见[风格库接口](references/personal-style-library.md)、[场景规则](references/custom-instructions.md)、[备份恢复](references/private-backup.md)。这些管理操作按需执行，不增加日常全库处理。

## 个人照片风格库

```text
把这张收藏到我的风格库，命名“柔光木质”，我喜欢它的光影与质感。
使用 $photo-finish 美化这张新照片，参考我的风格库。
这张按风格库里的“柔光木质”处理。
```

收藏、查看和删除复用主入口的 `style-add / style-list / style-remove`，修图继续使用原有 `prepare → submit → returned → review`。仅明确收藏才入库，待修图和成片不自动加入。个人库保存在当前用户的私有持久目录，公开仓库不含照片或个人偏好；跨设备同步由宿主提供，临时环境需指定持久位置。详见[风格库接口](references/personal-style-library.md)。

## 🧭 执行与能力边界

`prepare → submit → returned → review` 合并日常记账。控制器负责可追溯性和字段检查；真实修图、实际看图和审美判断由宿主与执行助手完成。

详见[运行指南](docs/runtime.md)、[完整规则](runtime/我的照片美化偏好与修图标准.md)、[接口字段](references/delivery-adapter.md)。核心要求为 Python 3.10+、Pillow 与宿主图像工具；本地验证与各平台 CI 分开记录。

Pillow 范围为 `>=12.3,<14`，pip 会为 Python 3.10 选择兼容的 12.x，并允许 Python 3.11+ 使用 13.x。NumPy、SciPy 保持可选，现有版本范围已允许兼容的新版。

生成重绘不保证逐像素保真。严格文字、身份、打印、RAW、色准任务按实际能力选择路线并验证。附带预设与 XMP 仅为可选设计起点，未声称完成 Adobe 导入、全场景实修或肤色标定验证。展示、质量接受和持久保存分别记录，无真实回执不宣称保存完成。

## 🔒 隐私与发布

公开内容仅含规则、执行代码、可选预设和合成测试。不包含私人参考照片、上传原片、个人生成图、资料库标识、会话记录、Token 或机器专属路径。照片、任务账本、签名 URL 和保存回执放在技能目录之外。

采用独立的新 Git 历史，并提供持续发布检查、确定性打包和哈希校验。安全检查有明确范围，不代表不存在所有潜在漏洞。详见[安全说明](SECURITY.md)与[发布审计](docs/security-audit.md)。

## ✅ 验证

```bash
python tools/doctor.py
python tools/check_publication.py
python tools/run_tests.py
python tools/build_release.py --output dist/photo-finish.zip
```

合成测试验证执行契约，不冒充真实照片质量证明。具体范围见[验证记录](docs/validation.md)。贡献前请阅读[贡献指南](CONTRIBUTING.md)。

## 许可证

[MIT](LICENSE)，copyright © 2026 kwhi。[方法来源](THIRD_PARTY_NOTICES.md)保留归属说明。用户照片与第三方服务各自遵守相应权利与条款。
