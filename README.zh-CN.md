# 📷 Photo Finish

> 从专业摄影与艺术指导出发，让照片的构图、光色和材质表达更充分，同时保留可信的摄影质感。

[English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md)

[![Agent Skill](https://img.shields.io/badge/Type-Agent%20Skill-3f4856?style=flat-square)](SKILL.md)
[![Version](https://img.shields.io/badge/Release-1.0.0-c45a2f?style=flat-square)](docs/validation.md)
[![Validation](https://github.com/kwhi6693-web/photo-finish/actions/workflows/validate.yml/badge.svg)](https://github.com/kwhi6693-web/photo-finish/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-2f855a?style=flat-square)](LICENSE)

![Photo Finish — 方向、处理、复核](docs/assets/photo-finish.svg)

## ⚡ 快速开始

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

## ✨ 核心能力

| 专业方向 | 实际处理 | 质量复核 | 交付 |
|---|---|---|---|
| 从原片建立意图，按需采用授权参考 | 自由构图、光影、调色、局部精修与材质 | 全幅表达与受影响原生细节 | 逐张仅输出成片，验收与保存分开记账 |

- 表达默认明显更充分，主动处理主次、层次、色彩关系和质感。
- 保留、优化、重构构图同等可选，不限定轻裁、固定画幅或统一暖金色。
- 长期保留去 AI 味：检查空间、反射、透视、塑料感、涂抹、假纹理与光晕。
- 书画题字按原图可见内容保持，模糊处不猜写；严格逐笔或像素保真只在明确要求时启用。
- 参考索引默认空。没有适用实例时，直接依据本片作专业判断，不依赖私人图库。
- 绑定原片与成片哈希、完整真实参数、保护方案、实际复核和计时，不以方案或提示词代替执行。

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
