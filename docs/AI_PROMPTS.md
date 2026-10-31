# AI Prompt 使用紀錄｜Skyline Weather 期中專題

> 本專題延續 2026-10-18 的 weather.gov Bad UI 調查與 Redesign。以下 10 組 Prompt 完整對應「前期調查（1–8）」與「本期實作（9–10）」的實際 AI 使用過程。
>
> **繳交前提醒**：課程要求每組 Prompt 都要有「實際 AI 對話截圖」。請在 OpenCode 的歷史對話中截取每一組的 Prompt 與 AI 回覆（不要只截本文件），貼到報告第 6 節；本文件可作為截圖索引與成果對照。

- AI 工具：OpenCode v2.0.28
- 模型：DeepSeek V4.1 Flash
- 前期調查日期：2026-10-18
- 本期實作日期：2026-10-31
- 對應網站：Skyline Weather（Django + Neon PostgreSQL + Render）

---

## Prompt 1｜定義任務範圍與報告架構

**使用目的**：把課程作業規則轉成可執行的交付清單，避免漏掉分析、Persona、Flow、Redesign 與文件格式。

**Prompt（依實際對話整理）**
> 「這是作業規則⋯我們覺得 https://www.weather.gov/ 的 UI 很爛，請幫我們完成作業（依規則產出分析、Persona、Flow、Redesign 與文件）。」

**AI 回覆與結果**：AI 拆解出 8 個章節與交付項目，包含原始截圖、量化分析、8 項 Bad UI 問題、3 個 Persona、3 組 User Story／Scenario／Flow、9 張 Redesign 分鏡與 Prompt 紀錄。

**實際應用成果**：`weather.gov_BadUI_Report.pdf` 的報告架構；本期再延伸為 Skyline Weather 的 5 頁網站與期中報告。

**截圖位置**：前期 OpenCode 對話（2026-10-18），Prompt 1 與 AI 回覆的開頭。

---

## Prompt 2｜擷取原網站操作畫面

**使用目的**：取得第一手證據，而不是只憑印象批評原網站。

**Prompt（依實際對話整理）**
> 「開啟 weather.gov，擷取首頁、輸入地點的搜尋操作、預報結果頁、預報細節與警報頁截圖（1280px 視窗）。」

**AI 回覆與結果**：以內建瀏覽器導航並輸出 6 張原始截圖，涵蓋首頁、搜尋、預報頂部、預報細節、AFD 討論與 Active Alerts。

**實際應用成果**：前期報告圖 1-1～1-6；本期用來定義首頁、城市查詢與警報中心的功能需求。

**截圖位置**：前期 OpenCode 對話的瀏覽器工具呼叫與截圖輸出。

---

## Prompt 3｜量化原網站的可用性問題

**使用目的**：用數據支持 Bad UI 判斷，避免只寫「很亂」、「字很小」。

**Prompt（依實際對話整理）**
> 「統計首頁與預報頁的連結數與文字字級分布；對兩個頁面執行 Lighthouse 稽核，列出失敗項目。」

**AI 回覆與結果**：首頁 113 個連結、3 個搜尋框、77% 文字 ≤12px；預報頁 75% 文字 ≤12px；Lighthouse 效能／無障礙 67、60，SEO 40。

**實際應用成果**：成為本期設計規範的量化依據：內文至少 14px、輔助文字 12.5px、主要連結集中、單一搜尋入口、對比度 ≥4.5:1。

**截圖位置**：前期 OpenCode 對話中的統計與 Lighthouse 輸出。

---

## Prompt 4｜找出並標註 Bad UI 問題

**使用目的**：把問題從「感覺」變成可追蹤的清單，作為 Redesign 與實作的依據。

**Prompt（依實際對話整理）**
> 「依截圖找出至少 5 項 Bad UI 問題，涵蓋資訊層級、導覽、版面、一致性、操作回饋、可讀性，並標註在截圖上。」

**AI 回覆與結果**：產出 8 項問題與 6 張標註圖，包括資訊層級失衡、搜尋不一致、導覽混亂、字級過小、資訊密度過高、技術術語過多、警報與地點脫節、裝飾元素搶焦點。

**實際應用成果**：本期 5 個頁面的設計對應：首頁只留現在／建議／預報／警報；單一搜尋；統一導覽；警報補上影響區域與建議行動。

**截圖位置**：前期 OpenCode 對話與報告圖 2-1～2-6。

---

## Prompt 5｜建立 Target User 與 Persona

**使用目的**：確保改善對象不是「自己覺得好看」，而是有真實情境的使用者。

**Prompt（依實際對話整理）**
> 「建立 3 類 Target User 的 Persona（背景／目標／需求／行為／痛點）、各 1 則 User Story 與 Scenario。」

**AI 回覆與結果**：建立通勤族 Ivy、戶外活動者 Michael、緊急管理人員 Carla 三個 Persona，並各產出一則 User Story 與 Scenario。

**實際應用成果**：本期會員中心保留「預設城市、收藏、通知門檻」；首頁的「最佳外出時段」對應戶外活動者；警報中心對應緊急管理情境。

**截圖位置**：前期 OpenCode 對話的 Persona 產出段落。

---

## Prompt 6｜設計三條 User Flow

**使用目的**：把 Persona 的需求轉成實際操作路徑，檢查每個決策點與完成結果。

**Prompt（依實際對話整理）**
> 「設計 3 組 User Flow，需含起點、步驟、決策點與完成結果，並解決前述 Bad UI 問題。」

**AI 回覆與結果**：Flow A（查現在天氣）、Flow B（規劃週末戶外活動）、Flow C（接收與處理警報），各標示決策點與完成狀態。

**實際應用成果**：本期對應為首頁 → 城市詳情、城市總覽 → 城市詳情 → 7 日、警報中心 → 警報詳情 → 收藏／通知設定。

**截圖位置**：前期 OpenCode 對話的 Mermaid／Flow 輸出。

---

## Prompt 7｜建立一致的設計系統與 9 張分鏡

**使用目的**：讓 3 條 Flow 的畫面看起來是同一個產品，而不是 9 張各自風格的 mockup。

**Prompt（依實際對話整理）**
> 「以一致的設計系統製作 Redesign 分鏡：3 組流程各 3 張、共 9 張，需標示畫面名稱與操作行為，色彩／字體／按鈕／導覽／版面一致；以 HTML/CSS 製作並輸出截圖。」

**AI 回覆與結果**：產出 Design Tokens（#1567D3、#0F2438、#35B6E8、溫度色、AQI 色、警示色）、字級、按鈕與 9 張分鏡（A1–A3、B1–B3、C1–C3）。

**實際應用成果**：本期直接沿用同一套 tokens 實作 `static/css/app.css`，9 張分鏡轉成 5 個 Django 頁面與會員中心。

**截圖位置**：前期 OpenCode 對話的 HTML/CSS 產出與故事板截圖。

---

## Prompt 8｜整理前期報告並輸出 PDF

**使用目的**：把調查、分析、設計與 AI 紀錄整理成可繳交的文件。

**Prompt（依實際對話整理）**
> 「整理為完整報告：分組名單、AI 聲明、8 項分析、Persona／Story／Scenario／Flow、分鏡、前後比較表與 Prompt 紀錄，輸出 PDF。」

**AI 回覆與結果**：產生 HTML 排版並輸出 38 頁 PDF，含封面、目錄、8 項問題、3 個 Persona、3 條 Flow、9 張分鏡與 Prompt 紀錄。

**實際應用成果**：`weather.gov_BadUI_Report.pdf`；本期以其問題與分鏡為需求基線。

**截圖位置**：前期 OpenCode 對話的 PDF 產生過程。

---

## Prompt 9｜閱讀期中專題規範

**使用目的**：確認期中專題的必交項目、頁面數量、後台與資料庫要求、評分方式與截止時間。

**Prompt（本次對話原文）**
> 「幫我讀一下這份文件，協助我完成介面設計的期中專題
> Attached file: C:\Users\user\Downloads\期中專題.pptx」

**AI 回覆與結果**：整理出 10 頁規範：5 個前台頁面、登入前後差異、多元查詢、Django 後台、Neon PostgreSQL、雲端部署、至少 10 組 AI Prompt、報告 8 大段落、Demo 30%／報告 70%、11/01 23:59 截止。

**實際應用成果**：本專案的 README 需求對照表、5 個頁面、部署檔案、測試與報告章節皆依此規範建立。

**截圖位置**：本次 OpenCode 對話（2026-10-31）的第一則訊息與 AI 回覆。

---

## Prompt 10｜延續 Bad UI 作業，實作可操作網站

**使用目的**：把 homework 的 weather.gov 調查與 9 張 Redesign 分鏡，從靜態 mockup 變成可操作的 Django 網站。

**Prompt（本次對話原文）**
> 「之前做的 badui homework C:\Users\user\Desktop\bad-ui-homework」

**AI 回覆與結果**：AI 讀取 homework 的原始截圖、Redesign HTML 與報告，將設計系統轉成 Skyline Weather：12 個城市、5 個前台頁面、會員登入／收藏／通知偏好、Django 管理後台、Neon 連線設定、Render 部署檔、12 個測試與 Selenium 截圖。

**實際應用成果**：
- 前台：`/`、`/locations/`、`/locations/new-york-ny/`、`/alerts/`、`/dashboard/`
- 後台：`/admin/`（城市、觀測、預報、警報、會員）
- 程式：`forecast/models.py`、`views.py`、`admin.py`、`templates/`、`static/css/app.css`
- 部署：`render.yaml`、`build.sh`、`.env.example`
- 成果截圖：`docs/screenshots/`

**截圖位置**：本次 OpenCode 對話（2026-10-31）的第二則訊息、AI 讀取 homework 的過程、建立專案與測試通過的輸出。

---

## 附錄：Prompt 與頁面成果對照

| # | Prompt 主題 | 主要成果 | 報告頁面 |
| --- | --- | --- | --- |
| 1 | 任務範圍與報告架構 | 8 章節交付清單 | 前期報告 |
| 2 | 原網站截圖 | 6 張原始畫面 | 前期報告圖 1-1～1-6 |
| 3 | 量化分析 | 113 連結、77% 小字、Lighthouse 67/40 | 前期報告 |
| 4 | 8 項 Bad UI 問題 | 6 張標註圖 | 前期報告圖 2-1～2-6 |
| 5 | Persona | Ivy／Michael／Carla | 前期報告第 III 節 |
| 6 | User Flow | Flow A／B／C | 前期報告圖 3-1～3-3 |
| 7 | Design System + 9 分鏡 | Tokens 與 A1–C3 | 前期報告圖 4-1～4-10 |
| 8 | 前期報告 PDF | 38 頁 PDF | 前期報告 |
| 9 | 期中規範 | 需求對照與 5 頁規劃 | 本期報告第 1–3 節 |
| 10 | 延續作業實作 | Django 全端網站、後台、部署、測試 | 本期報告第 4–7 節 |

## 備註：AI 回覆的使用方式

- Persona、Flow、文案與程式碼均由 AI 產生初稿，組員依實際情況調整後採用。
- 所有氣象資料為模擬資料，依 NWS 公開欄位結構建立，不代表官方即時預報。
- 截圖與測試結果皆来自實際執行的網站，不是設計圖。
- 部署後記得更改 `demo` 與 `admin` 的展示密碼，避免任何人都能進入後台。
