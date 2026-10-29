# 📷 Photo Finish

> 專注**非人像攝影**的自然照片美化：從光影、色彩、真實質感到可核驗的正式交付。

[English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md)

[![Agent Skill](https://img.shields.io/badge/Type-Agent%20Skill-3f4856?style=flat-square)](SKILL.md)
[![Version](https://img.shields.io/badge/Stable-v1.5.3-2f855a?style=flat-square)](https://github.com/kwhi6693-web/photo-finish/releases/tag/v1.5.3)
[![Validation](https://github.com/kwhi6693-web/photo-finish/actions/workflows/validate.yml/badge.svg)](https://github.com/kwhi6693-web/photo-finish/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-2f855a?style=flat-square)](LICENSE)
[![Focus: Non-portrait](https://img.shields.io/badge/Focus-Non--portrait-7c3aed?style=flat-square)](references/product-scope.md)
[![Look: Natural finish](https://img.shields.io/badge/Look-Natural%20finish-0e7490?style=flat-square)](references/tone-color-foundations.md)

![Photo Finish — 攝影方向、處理與複核](docs/assets/photo-finish.svg)

**快速導覽：**[下載安裝](#下載安裝) · [如何使用](#如何使用) · [能力與限制](#能力與限制) · [宿主相容性](#宿主相容性) · [技術文件](#技術文件)

**最新正式發行：[v1.5.3](https://github.com/kwhi6693-web/photo-finish/releases/tag/v1.5.3)。** GitHub 發布新版**不代表**已安裝的 Skill 自動升級。

## 🎯 產品定位

Photo Finish 是 Agent Skill，協助獲得授權的智慧代理理解攝影原片、確定處理方向、使用**真正可用的影像工具**編輯、對照複核，並在宿主支援時交付經過檔案驗證的正式成片。

**適用場景：**自然風光、城市夜景、建築、旅行、靜物、美食與產品攝影。**不處理以人物為主體的專門人像修圖**，不開發磨皮、美顏、五官調整或塑形功能。非人像照片中偶然出現的人物，仍須保留其身分與重要內容。[完整產品定位](references/product-scope.md)。

目標是自然可信的光影、色彩、視覺層次與材質，而非統一濾鏡或保證每張照片都能改善。

## ⚡ 下載安裝

1. 從[最新正式發布頁](https://github.com/kwhi6693-web/photo-finish/releases/latest)下載[安裝 ZIP](https://github.com/kwhi6693-web/photo-finish/releases/latest/download/photo-finish.zip)和 [SHA-256 校驗檔](https://github.com/kwhi6693-web/photo-finish/releases/latest/download/photo-finish.zip.sha256)。
2. 驗證 ZIP 雜湊後，依照宿主**正式支援的安裝流程**安裝完整的 `photo-finish/` 目錄。`SKILL.md`、`runtime/`、`references/`、`scripts/`、`agents/`、`assets/` 必須一併保留。
3. 確認宿主**實際載入版本**及安裝後全部原始檔案位元組一致。

應下載 GitHub Release **正式附件**，不是 GitHub 自動產生的 Source code ZIP。儲存庫中的 `dist/photo-finish.zip` 是歷史 **v1.5.1** 安裝包，**不是 v1.5.3 安裝包**。隔離解壓成功亦無法證明 ChatGPT 真實宿主升級成功。

## 📸 如何使用

```text
使用 $photo-finish 美化這張自然風景照片。
請直接修圖、檢查、儲存並交付我接下來上傳的非人像照片。
保留建築結構與可見文字，只改善光影和色彩。
讓已儲存的 V1 更自然一點，保留原始紋理。
直接讀取舊 V1 檔案恢復，不重新渲染。
```

單獨上傳非人像照片**可能**在相容宿主中觸發 Skill，但「只上傳照片就自動觸發」仍取決於**真實宿主行為**，並未證實所有環境皆可觸發。某些影像工具需要明確代操作授權；僅上傳照片、提供偏好或出現互動預覽，皆不能代替授權和正式儲存回執。必須遵守工具的 **STOP** 要求。

**預設交付：**一張最終成片，附簡潔版本與真實儲存狀態。若攝影改善不足、內容保護不合格或無法取得可核驗檔案，應如實拒絕，不得虛構成功的 V1。

## 🧭 處理流程

1. **觀察：**檢查原片構圖、光照、色彩、材質與需保護的內容。
2. **判斷：**結合本次指令、可選長期規則和確實看過的參考照片，制定專業處理方向。
3. **編輯：**呼叫真實、已授權的宿主影像工具；需要嚴格保真時優先採用可靠的非生成式路線。
4. **複核：**與原片比較全幅效果及受影響細節，重點檢查文字、人物、結構、紋理和邊緣偽影。
5. **交付：**只有品質與內容保護通過後，才以真實檔案位元組、儲存回執和版本關係確認正式交付。

內建控制器管理流程及證據，**本身不渲染照片，也不會自動認證審美品質**。[執行指南](docs/runtime.md) · [交付介面](references/delivery-adapter.md)。

## ✨ 能力與限制

| 方向 | 已具備的能力 | 須如實說明的限制 |
|---|---|---|
| 光影與調色 | 已有真實非生成式全幅調整及部分自然、建築、旅行單樣本成功案例 | 單樣本通過不代表所有場景品質保證 |
| 構圖與內容保護 | 專業方向判斷、原片對照、建築文字與自然紋理等內容檢查 | 生成重建無法保證逐像素保真 |
| 局部精修 | 宿主實際支援並完成驗證時使用選區或 `maskURI` | 複雜天空與樹冠交界、羽化及非目標保護仍受限制 |
| 個人風格庫 | 明確授權後收藏、命名、分組、搜尋及選取最多三張參考 | 不自動收藏；引用參考不代表品質提升 |
| 自訂指令 | 可選全域、場景規則、當次覆蓋及修改撤銷 | 臨時要求不會自動變成長期偏好或授予工具權限 |
| 版本交付 | 真實檔案 SHA-256、V1/V2 修訂、前後對照、舊檔回退與儲存核驗 | 預覽、品質接受、持久儲存及版本登記是不同事實 |
| 私有歸檔（v1.5.3） | 限定範圍歸檔、完整雜湊回讀、獨立會話**唯讀**取回及新私有位置的版本檢視恢復 | 需要可驗證的宿主交接憑據及**單一寫入者** |

**尚未證實具備普遍效果：**專業獨立降噪、真正去模糊、超解析度、複雜夜景天空恢復及精密邊緣去背。自動化測試與 CI 驗證軟體契約，不代表真實照片審美保證。[v1.5.2 品質證據](docs/QUALITY_STATUS_1_5_2.md) · [驗證範圍](docs/validation.md)。

### 恢復的支援邊界

v1.5.3 的歸檔與恢復僅在**真實可驗證的宿主憑據、準確檔案身分與單一寫入者**條件下成立。上傳結果未知、憑據遺失、身分衝突或目標不屬於本次任務時必須安全停止，不盲目重傳或覆寫歷史。

仍明確排除兩項宿主級 P0：**全部本機操作狀態與交接憑據遺失後的權威對帳**，以及**跨會話同系列的多寫入者協調**。不承諾無人值守背景歸檔、無限期儲存或第五階段完整長期穩定性。**第五階段整體仍為 NO-GO。**[更新記錄](CHANGELOG.md) · [歷史發行準備證據](docs/RELEASE_1_5_3_PREPARATION.md)。

### 宿主相容性

真實宿主必須具備看圖、呼叫獲授權影像編輯工具、讀取正式輸出位元組及可信儲存回執的能力。僅安裝 Python 依賴不會取得雲端影像編輯服務或長期儲存。

先前真實 ChatGPT 宿主升級嘗試中，`assets/icon.svg` 在內容物化時由 **1,210 位元組變成 1,619 位元組**，實際安裝仍為 **v1.5.1**。在上傳、物化、安裝與實際載入全路徑皆能證明**全部原始位元組一致**前，**v1.5.3 真實宿主升級仍為 NO-GO**。不得修改原 SVG 或放寬雜湊規則繞過此問題。

## 🎨 個人風格規則與隱私

這些都是**可選功能**。私人風格庫為空或沒有適用參考時，仍可直接根據原片作專業判斷。

- **風格庫：**「把這張收藏為『柔光木質』，我喜歡它的自然光線。」只有明確授權才收藏。[風格庫說明](references/personal-style-library.md)。
- **個人規則：**「記住我偏好自然的明暗層次。」一次性調整不會自動變成長期規則。[自訂指令](references/custom-instructions.md)。
- **私人備份：**依需要匯出、檢查及匯入照片、資料、個人規則與修改歷史。[備份恢復](references/private-backup.md)。

個人照片、風格、偏好、帳本、憑據及私人 Library ID **不得進入公開儲存庫或 Skill 安裝目錄**。持久儲存須有真實宿主支援與回執；暫存路徑或顯示的附件不代表長期儲存。Skill 不內建雲端同步、遙測或使用者帳號服務。[安全說明](SECURITY.md)。

## 🧰 開發者說明

```bash
git clone https://github.com/kwhi6693-web/photo-finish.git
cd photo-finish
python -m venv .venv
# 依終端環境正常啟用虛擬環境。
python -m pip install -r requirements.txt
python tools/doctor.py
```

開發、測試和發行細節請見[貢獻指南](CONTRIBUTING.md)、[驗證說明](docs/validation.md)和[發布流程](docs/releasing.md)。不得將私人照片或帳本寫入公開測試資料。

## 📚 技術文件

| 需要了解 | 資料 |
|---|---|
| 功能與產品範圍 | [架構](docs/architecture.md) · [非人像定位](references/product-scope.md) |
| 執行與交付介面 | [執行指南](docs/runtime.md) · [交付協定](references/delivery-adapter.md) |
| 攝影美學與內容保護 | [光影色彩依據](references/tone-color-foundations.md) · [保真精修](references/fidelity-and-retouch.md) |
| 參考風格與個人規則 | [風格庫](references/personal-style-library.md) · [自訂指令](references/custom-instructions.md) |
| 私人遷移與恢復 | [備份恢復](references/private-backup.md) |
| 發行、驗證與安全 | [更新記錄](CHANGELOG.md) · [驗證](docs/validation.md) · [安全說明](SECURITY.md) |

## 🔒 授權條款

[MIT](LICENSE) © 2026 kwhi。[第三方聲明](THIRD_PARTY_NOTICES.md)。使用者照片及第三方素材各自保留原有權利。
