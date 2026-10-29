# Photo Finish

> 专注**非人像摄影**的自然照片美化：从光影、色彩、真实质感到可核验的正式交付。

[English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md)

[![Agent Skill](https://img.shields.io/badge/Type-Agent%20Skill-3f4856?style=flat-square)](SKILL.md)
[![稳定版](https://img.shields.io/badge/Stable-v1.5.3-2f855a?style=flat-square)](https://github.com/kwhi6693-web/photo-finish/releases/tag/v1.5.3)
[![CI](https://github.com/kwhi6693-web/photo-finish/actions/workflows/validate.yml/badge.svg)](https://github.com/kwhi6693-web/photo-finish/actions/workflows/validate.yml)
[![MIT](https://img.shields.io/badge/License-MIT-2f855a?style=flat-square)](LICENSE)

![Photo Finish — 摄影方向、处理与复核](docs/assets/photo-finish.svg)

**快速导航：**[下载安装](#下载安装) · [如何使用](#如何使用) · [能力与限制](#能力与限制) · [宿主兼容性](#宿主兼容性) · [技术文档](#技术文档)

**最新正式发行：[v1.5.3](https://github.com/kwhi6693-web/photo-finish/releases/tag/v1.5.3)。** GitHub 发布新版本**不等于**已安装 Skill 自动更新。

## 产品定位

Photo Finish 是 Agent Skill，帮助获得授权的智能体理解摄影原片、确定处理方向、借助**真实可用的图像工具**编辑、对照复核，并在宿主支持时交付经过文件核验的正式成片。

**适用场景：**自然风光、城市夜景、建筑、旅行、静物、美食和产品摄影。**不处理以人物为主体的人像专门修图**，不开发磨皮、美颜、五官调整或塑形功能。非人像照片中偶然出现的人物须保留身份与重要内容。[完整产品定位](references/product-scope.md)。

目标是自然可信的光影、色彩、主次层次和材质，而不是统一滤镜或保证每张照片都能改善。

## 下载安装

1. 从[最新正式发布页](https://github.com/kwhi6693-web/photo-finish/releases/latest)下载[安装 ZIP](https://github.com/kwhi6693-web/photo-finish/releases/latest/download/photo-finish.zip)及其 [SHA-256 校验文件](https://github.com/kwhi6693-web/photo-finish/releases/latest/download/photo-finish.zip.sha256)。
2. 验证 ZIP 哈希后，按照宿主**正式支持的安装流程**放置完整的 `photo-finish/` 目录。`SKILL.md`、`runtime/`、`references/`、`scripts/`、`agents/`、`assets/` 必须一起保留。
3. 核对宿主**实际加载版本**及安装后全部原文件字节是否一致。

应下载 GitHub Release **正式附件**，不是 GitHub 自动生成的 Source code ZIP。仓库内的 `dist/photo-finish.zip` 是历史 **v1.5.1** 安装包，**不是 v1.5.3 安装包**。隔离解压成功也不能证明 ChatGPT 真实宿主升级成功。

## 如何使用

```text
使用 $photo-finish 美化这张自然风景照片。
请直接修图、检查、保存并交付我接下来上传的非人像照片。
保留建筑结构和可见文字，只改善光影与色彩。
把已经保存的 V1 稍微处理得更自然，保留原始纹理。
直接读取之前的 V1 文件恢复，不重新渲染。
```

上传非人像照片**可能**在兼容宿主中触发 Skill，但“只上传照片就自动触发”仍取决于**真实宿主行为**，并未证明所有环境均可触发。某些图像工具需要明确代操作授权；仅上传照片、提供审美偏好或出现交互预览，都不能代替授权和正式保存回执。必须遵守工具的 **STOP** 要求。

**默认交付：**一张最终成片，附简洁的版本与真实保存状态。若摄影改善不足、内容保护不合格或无法取得可核验文件，应如实拒绝，不能虚构成功的 V1。

## 处理流程

1. **观察：**检查原片构图、光照、色彩、材质与需要保护的内容。
2. **判断：**结合本次指令、可选长期规则及确实查看过的参考照片，制定专业处理方向。
3. **编辑：**调用真实、已授权的宿主图像工具；要求严格内容保真时优先采用可靠的非生成式路线。
4. **复核：**与原片比较全幅效果和受影响细节，重点核查文字、人物、结构、纹理及边缘伪影。
5. **交付：**只在质量与内容保护通过后，按真实文件字节、保存回执和版本关系确认正式交付。

内置控制器负责流程和证据管理，**本身不渲染照片，也不自动认证审美质量**。[运行指南](docs/runtime.md) · [交付接口](references/delivery-adapter.md)。

## 能力与限制

| 方向 | 已具备的能力 | 必须如实说明的边界 |
|---|---|---|
| 光影与调色 | 已有真实非生成式全局调整及部分自然、建筑、旅行单样本成功案例 | 单样本通过不等于所有场景质量保证 |
| 构图与内容保护 | 专业方向判断、原片对照、建筑文字与自然纹理等内容检查 | 生成重建无法保证逐像素保真 |
| 局部精修 | 宿主实际可用且经过核验时使用选区或 `maskURI` | 复杂天空/树冠交界、羽化及非目标保护仍受限制 |
| 个人风格库 | 明确授权后收藏、命名、分组、搜索及选取最多三张参考 | 不自动收藏；引用参考不代表质量提升 |
| 自定义指令 | 可选全局、场景规则、当次覆盖与修改撤销 | 临时要求不会自动写入长期偏好或授予工具权限 |
| 版本交付 | 真实文件 SHA-256、V1/V2 修订、前后对比、旧文件回退与保存核验 | 预览、质量接受、持久保存和版本登记是不同事实 |
| 私有归档（v1.5.3） | 限定范围归档、完整哈希回读、独立会话**只读**取回、新私有位置的版本视图恢复 | 需要可验证的宿主交接凭据与**单写入者** |

**尚未证实具有普遍效果：**专业独立降噪、真正去模糊、超分辨率、复杂夜景天空恢复与精密边缘抠图。自动测试与 CI 证明软件契约，不等于真实照片审美保证。[v1.5.2 质量证据](docs/QUALITY_STATUS_1_5_2.md) · [验证范围](docs/validation.md)。

### 恢复的支持边界

v1.5.3 的归档与恢复能力仅在**真实可验证的宿主凭据、准确文件身份和单写入者**条件下成立。上传结果未知、凭据丢失、身份冲突或目标不属于当前任务时必须安全停止，不盲目重传或覆盖历史。

仍明确排除两个宿主级 P0：**全部本地操作状态及交接凭据丢失后的权威对账**，以及**跨会话同系列的多写入者协调**。不承诺无人值守后台归档、无限期存储或第五阶段完整长期稳定性。**第五阶段整体仍为 NO-GO。**[更新记录](CHANGELOG.md) · [历史发行准备证据](docs/RELEASE_1_5_3_PREPARATION.md)。

### 宿主兼容性

真实宿主必须具备看图、调用获授权的图像编辑工具、读取正式输出字节以及可信保存回执的能力。仅安装 Python 依赖不会得到云端图像编辑服务或长期存储。

此前真实 ChatGPT 宿主尝试升级时，`assets/icon.svg` 在内容物化过程中由 **1,210 字节变为 1,619 字节**，实际安装仍为 **v1.5.1**。直到上传、物化、安装和实际加载全链路都能证明**所有原始字节一致**，**v1.5.3 的真实宿主升级仍为 NO-GO**。不得修改原 SVG 或放松哈希规则绕过此问题。

## 个人风格规则与隐私

这些都是**可选功能**。私人风格库为空或没有适用参考时，仍可直接根据原片作专业判断。

- **风格库：**“把这张收藏为「柔光木质」，喜欢它的自然光线。”只有明确授权才能收藏。[风格库说明](references/personal-style-library.md)。
- **个人规则：**“记住我偏好自然的明暗层次。”一次性调整不会自动成为长期规则。[自定义指令](references/custom-instructions.md)。
- **私人备份：**按需导出、检查和导入照片、元数据、个人规则与修改历史。[备份与恢复](references/private-backup.md)。

个人照片、风格、偏好、账本、凭据和私人 Library ID **不进入公开仓库或 Skill 安装目录**。持久保存取决于真实宿主能力及回执；临时路径或展示的附件不能单独证明长期保存。Skill 不内置云同步、遥测或用户账号服务。[安全说明](SECURITY.md)。

## 开发者说明

```bash
git clone https://github.com/kwhi6693-web/photo-finish.git
cd photo-finish
python -m venv .venv
# 按终端环境正常激活虚拟环境。
python -m pip install -r requirements.txt
python tools/doctor.py
```

开发、测试与发布细节见[贡献指南](CONTRIBUTING.md)、[验证说明](docs/validation.md)及[发布流程](docs/releasing.md)。不得把私人照片或账本写入公开测试资料。

## 技术文档

| 需要了解 | 资料 |
|---|---|
| 功能与产品范围 | [架构](docs/architecture.md) · [非人像范围](references/product-scope.md) |
| 执行与交付接口 | [运行指南](docs/runtime.md) · [交付协议](references/delivery-adapter.md) |
| 摄影美学与内容保护 | [光影色彩依据](references/tone-color-foundations.md) · [保真精修](references/fidelity-and-retouch.md) |
| 参考风格与个性规则 | [风格库](references/personal-style-library.md) · [自定义指令](references/custom-instructions.md) |
| 私人迁移与恢复 | [备份恢复](references/private-backup.md) |
| 发行、验证和安全 | [更新记录](CHANGELOG.md) · [验证](docs/validation.md) · [安全说明](SECURITY.md) |

## 许可证

[MIT](LICENSE) © 2026 kwhi。[第三方声明](THIRD_PARTY_NOTICES.md)。用户照片及第三方素材各自保留原有权利。
