# 📷 Photo Finish

> 從專業攝影與藝術指導出發，讓照片的構圖、光色與材質表達更充分，同時保留可信的攝影質感。

[English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md)

[![Agent Skill](https://img.shields.io/badge/Type-Agent%20Skill-3f4856?style=flat-square)](SKILL.md)
[![Version](https://img.shields.io/badge/Release-1.4.2-c45a2f?style=flat-square)](https://github.com/kwhi6693-web/photo-finish/releases/latest)
[![Validation](https://github.com/kwhi6693-web/photo-finish/actions/workflows/validate.yml/badge.svg)](https://github.com/kwhi6693-web/photo-finish/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-2f855a?style=flat-square)](LICENSE)

![Photo Finish — 方向、處理、複核](docs/assets/photo-finish.svg)

## ⚡ 快速開始

從[最新正式發布頁](https://github.com/kwhi6693-web/photo-finish/releases/latest)下載 [最新技能安裝包](https://github.com/kwhi6693-web/photo-finish/releases/latest/download/photo-finish.zip)與 [SHA-256 校驗檔](https://github.com/kwhi6693-web/photo-finish/releases/latest/download/photo-finish.zip.sha256)。上述下載連結會持續指向最新正式版。核對雜湊後，安裝解壓得到的 `photo-finish/` 目錄。GitHub 自動產生的 Source code 壓縮檔包含整個儲存庫；技能安裝包是 `photo-finish.zip`。版本變化與升級說明見[更新記錄](CHANGELOG.md)。

將整個儲存庫作為 `photo-finish` 技能安裝。`SKILL.md`、`references/`、`scripts/`、`agents/`、`assets/` 與 **`runtime/` 必須一起保留**。執行包已包含，不需個人資料庫或額外還原包。

```text
使用 $photo-finish 處理這張照片。
```

預設逐張僅輸出最終成片，不附原片、前後對比、參數或說明。內部原片對照、實際看圖驗收與記錄持續執行；當次明確要求優先。

```bash
git clone https://github.com/kwhi6693-web/photo-finish.git
cd photo-finish
python -m venv .venv
# 依所用終端啟用虛擬環境。
python -m pip install -r requirements.txt
python tools/doctor.py
```

宿主必須提供看圖、真實影像編輯與檔案存取能力。Python 依賴不包含影像生成服務；技能不收集 API Key，也不隱式安裝外部工具。

**先檢索風格，再確定方向：**觀察原片並讀取可選全域指令，檢索並查看個人風格參考，再結合專業攝影後期美學確定最終方向。沒有自訂指令時專業自主處理；只限定部分要求時，其餘自主判斷。首版的創作自由、內容保護、實際複核與成片交付要求保留。

## ✨ 核心能力

| 專業方向 | 實際處理 | 品質複核 | 交付 |
|---|---|---|---|
| 從原片建立意圖，按需採用授權參考 | 自由構圖、光影、調色、局部精修與材質 | 全幅表達與受影響原生細節 | 逐張僅輸出成片，驗收與儲存分開記錄 |

- 表達預設明顯更充分，主動處理主次、層次、色彩關係與質感。
- 保留、最佳化、重構構圖同等可選，不限制輕裁、固定畫幅或統一暖金色。
- 保留去 AI 味，檢查空間、反射、透視、塑膠感、塗抹、假紋理與光暈。
- 書畫題字依原圖可見內容保持，模糊處不猜寫；嚴格逐筆或像素保真僅在明確要求時使用。
- **個人照片風格庫**：主動收藏喜歡的照片，記錄名稱、標籤與喜歡之處；每次修圖自動檢索最多三張適用參考，可用關鍵字或收藏 ID 指定，並支援查看、搜尋與刪除。
- 公開參考索引預設空，個人庫沒有適用案例時直接依原片作專業判斷。
- 綁定原片與成片雜湊、真實參數、保護方案、實際複核與計時。

## 可選全域指令與專業判斷

使用者可以保存長期修圖規則與審美偏好，並查看、修改、刪除單條或清空。每次調用先讀取個人設定，再結合原片建立處理方向；當次要求優先，暫時嘗試不會自動改寫長期喜好。

```text
以後按這些規則修圖，並記住我喜歡的光影與質感。
查看我的修圖規則與偏好。
這次使用另一種色彩，不改變我的長期偏好。
```

使用主入口 `profile-show / profile-set / profile-reset`，個人設定與圖庫一樣獨立私有保存，不進入公開倉庫。詳見[自訂指令介面](references/custom-instructions.md)。

## 管理、場景適配與備份

- 參考照片支援修改名稱/標籤/備註、分組、置頂與指定借鑑範圍，列表支援篩選及翻頁，原始照片保持不變。
- 規則可依場景生效，支援啟停、結構化衝突提示與最近 20 次修改撤銷；完整清空會刪除撤銷歷史並保留圖庫。
- 私人照片、資料、規則與修改歷史可匯出、檢查與匯入。預設合併保留既有內容，空目錄可完整恢復；備份不進入公開倉庫。

詳見[風格庫介面](references/personal-style-library.md)、[場景規則](references/custom-instructions.md)、[備份恢復](references/private-backup.md)。管理操作按需執行，不增加日常全庫處理。

## 個人照片風格庫

```text
把這張收藏到我的風格庫，命名「柔光木質」，我喜歡它的光影與質感。
使用 $photo-finish 美化這張新照片，參考我的風格庫。
這張按風格庫裡的「柔光木質」處理。
```

收藏、查看與刪除使用主入口的 `style-add / style-list / style-remove`，修圖沿用原有四步流程。僅明確收藏才入庫。私人照片與偏好保存在技能/Git 目錄之外；跨裝置同步由宿主提供，暫時環境需指定持久位置。詳見[風格庫介面](references/personal-style-library.md)。

## 🧭 執行與能力邊界

`prepare → submit → returned → review` 合併日常記錄。控制器不提供影像渲染，也不自動完成審美驗收。請參閱[執行指南](docs/runtime.md)、[完整規則](runtime/我的照片美化偏好与修图标准.md)與[介面欄位](references/delivery-adapter.md)。核心要求為 Python 3.10+、Pillow 與宿主影像工具。

Pillow 範圍為 `>=12.3,<14`，pip 會為 Python 3.10 選擇相容的 12.x，並允許 Python 3.11+ 使用 13.x。NumPy、SciPy 保持可選，現有版本範圍已允許相容的新版。

生成重繪不保證逐像素保真。嚴格文字、身分、列印、RAW 與色準任務依實際能力驗證。附帶預設與 XMP 僅為可選設計起點，未宣稱完成 Adobe 匯入、全場景實修或膚色校準。展示、品質接受與持久儲存分別記錄。

## 🔒 隱私與驗證

不包含私人照片、個人生成圖、資料庫識別碼、工作記錄、Token 或機器專屬路徑。影像、工作帳本、簽名 URL 與儲存回執放在技能目錄之外。使用獨立的新 Git 歷史、發布檢查與確定性封裝；檢查不代表排除所有潛在漏洞。

```bash
python tools/doctor.py
python tools/check_publication.py
python tools/run_tests.py
python tools/build_release.py --output dist/photo-finish.zip
```

合成測試不冒充真實照片品質證明。詳見[驗證記錄](docs/validation.md)、[安全說明](SECURITY.md)、[發布審計](docs/security-audit.md)及[貢獻指南](CONTRIBUTING.md)。

## 資料導覽

| 需要了解 | 資料 |
|---|---|
| 主要功能、架構與全部管理入口 | [架構與資料地圖](docs/architecture.md) |
| 明暗、色彩、主次與影片理論轉化 | [攝影美化判斷依據](references/tone-color-foundations.md) |
| 實際執行與介面欄位 | [執行指南](docs/runtime.md) · [主介面](references/delivery-adapter.md) |
| 個人風格與可選全域指令 | [風格庫](references/personal-style-library.md) · [自訂指令](references/custom-instructions.md) |
| 私人資料備份和遷移 | [備份恢復](references/private-backup.md) |
| 更新、驗證與發布 | [更新記錄](CHANGELOG.md) · [驗證記錄](docs/validation.md) · [發布流程](docs/releasing.md) |
| 隱私邊界與貢獻 | [安全說明](SECURITY.md) · [發布審計](docs/security-audit.md) · [貢獻指南](CONTRIBUTING.md) |

## 授權條款

[MIT](LICENSE)，copyright © 2026 kwhi。[方法來源](THIRD_PARTY_NOTICES.md)保留歸屬說明。使用者照片與第三方服務各自遵守其權利與條款。
