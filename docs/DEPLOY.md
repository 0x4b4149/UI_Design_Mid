# 部署 Runbook｜Skyline Weather

目標：在 **Neon PostgreSQL** 建立資料庫，把 **Django 前台 + 管理後台** 部署到 **Render**，並取得可驗收的連結。

## 目前部署狀態（2026-11-01）

| 項目 | 內容 |
| --- | --- |
| 前台 | <https://skyline-weather-gqoc.onrender.com/> |
| 後台 | <https://skyline-weather-gqoc.onrender.com/admin/> |
| 健康檢查 | <https://skyline-weather-gqoc.onrender.com/healthz/> → `{"status": "ok", "database": "up"}` |
| GitHub | <https://github.com/0x4b4149/UI_Design_Mid> |
| Render Blueprint | `skyline-weather-group8`（服務 `skyline-weather`） |
| Neon 專案 | `claimable-29d8654a5ed1`（已 claim 到 `0x4b4149`，region `aws-us-east-2`） |
| 測試帳號 | 會員 `demo / Demo1234!`；管理員 `admin / Admin1234!` |

> Neon 的 temporary project 被 claim 後，角色密碼會輪替一次，Render 的 `DATABASE_URL` 必須同步更新，否則 `/healthz/` 會回 503。本次已更新並重新部署驗證。

---

## 0. 你需要準備的帳號

- [GitHub](https://github.com/)（放程式碼）
- [Neon](https://neon.com/)（PostgreSQL）
- [Render](https://render.com/)（部署）

> 三個服務都有免費方案。Render 免費服務閒置會休眠，第一次開啟較慢。

---

## 1. 本機最終檢查

```powershell
python manage.py test forecast
python manage.py check --deploy
```

`check --deploy` 在 `DEBUG=True` 時會出現安全性警告，這是正常的；部署時 `DEBUG=False` 後應只剩 `SECRET_KEY` 或 HTTPS 相關提示。

---

## 2. 建立 Neon 資料庫

1. 登入 Neon → **New Project**。
2. 設定：
   - Project name：`skyline-weather`
   - Database：`neondb`
   - Region：選離台灣最近的區域（例如 Singapore / AWS ap-southeast-1）
3. 在 **Connect** 視窗選擇 **Pooled connection**，複製完整連線字串，長相類似：

   ```text
   postgresql://neondb_owner:AbCdEf123@ep-cool-name-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```

4. 本機 `.env` 加入：

   ```dotenv
   DATABASE_URL=postgresql://...
   ```

5. 寫入資料表與示範資料：

   ```powershell
   python manage.py migrate
   python manage.py seed_demo
   ```

6. 確認 Neon 的 Tables 有 `forecast_location`、`forecast_alert` 等表。

**注意**：Neon 的連線字串只顯示一次密碼；如果忘記，請 Reset password。不要把 `.env` 上傳 GitHub。

---

## 3. 推到 GitHub

此資料夾已是 Git repo（含 `.git`），但本機若沒有 Git CLI，可用 GitHub Desktop 或 SourceTree：

1. Add existing repository → 選擇 `C:\Users\user\Documents\UI_Design_Mid`。
2. 確認 `.env`、`.venv`、`db.sqlite3` 沒有被加入（`.gitignore` 已設定）。
3. Commit：`midterm: Skyline Weather Django app`
4. Publish repository（建議 Private，Render 仍可連）。

若使用 Git CLI：

```powershell
git add .
git commit -m "midterm: Skyline Weather Django app"
git branch -M main
git remote add origin https://github.com/<你的帳號>/skyline-weather.git
git push -u origin main
```

---

## 4. 在 Render 部署

### 4.1 Blueprint（最快）

1. Render Dashboard → **New** → **Blueprint**。
2. 選擇 GitHub repo → Render 讀到 `render.yaml`。
3. 服務名稱可改成 `skyline-weather`（會影響網址）。
4. 填入環境變數 `DATABASE_URL`（貼上 Neon 連線字串）。
5. **Apply / Deploy**。
6. 等待 Build 完成。成功的 log 會看到：

   ```text
   Seeded 12 locations, 84 daily forecasts, 360 hourly forecasts, 8 alerts.
   ...
   Booting worker with pid ...
   ```

### 4.2 手動建立 Web Service

| 設定 | 值 |
| --- | --- |
| Language | Python 3 |
| Build Command | `bash build.sh` |
| Start Command | `gunicorn skyline.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |
| Health Check Path | `/healthz/` |

環境變數：

```text
SECRET_KEY=<generate>
DEBUG=False
DATABASE_URL=postgresql://...neon.tech/neondb?sslmode=require
ALLOWED_HOSTS=.onrender.com
CSRF_TRUSTED_ORIGINS=https://*.onrender.com
SECURE_SSL_REDIRECT=False
PYTHON_VERSION=3.13.7
```

> 若 Render 不支援 `PYTHON_VERSION=3.13.7`，改成 `3.13.5` 或移除，讓 Render 使用預設 Python 3.13。

---

## 5. 部署後驗收

把 `<your-service>` 換成 Render 給的網址：

```text
前台：https://<your-service>.onrender.com/
後台：https://<your-service>.onrender.com/admin/
健康檢查：https://<your-service>.onrender.com/healthz/
```

逐項檢查：

- [ ] `/healthz/` 顯示 `{"status": "ok", "database": "up"}`（代表 Neon 連線成功）
- [ ] 首頁 12 個城市、New York 資料正常
- [ ] 城市總覽搜尋 `Seattle`、區域 `west`、溫度 50–70 → 結果正確
- [ ] 登入 `demo / Demo1234!` → 會員中心顯示 3 個收藏
- [ ] 收藏／移除城市 → 首頁與會員中心同步
- [ ] 登入 `admin / Admin1234!` → `/admin/` 可新增城市、修改警報
- [ ] 手機寬度（390px）導覽與表單可用

把前後台連結、測試帳密填入報告與 TronClass 作業說明。

---

## 6. 常見錯誤

### `DisallowedHost`
`ALLOWED_HOSTS` 沒包含 Render 網域。設定 `.onrender.com` 或完整 hostname。

### `CSRF verification failed`
`CSRF_TRUSTED_ORIGINS` 沒包含 `https://<your-service>.onrender.com`。保留 `https://*.onrender.com` 可涵蓋。

### `could not connect to server` / `SSL required`
`DATABASE_URL` 少了 `?sslmode=require`，或使用 Direct connection 被防火牆擋住；改用 Pooled connection。

### `relation "forecast_location" does not exist`
`migrate` 沒有成功。看 Render Build Log；必要時在 Render Shell 執行：

```bash
python manage.py migrate
python manage.py seed_demo --if-empty
```

### 靜態檔 404
確認 Build Command 有 `python manage.py collectstatic --noinput`，且 `DEBUG=False`、Whitenoise middleware 存在。

### 部署後資料被重置
`build.sh` 使用 `seed_demo --if-empty`，只有在資料庫沒有城市時才會種資料。若你手動執行不帶 `--if-empty` 的 `seed_demo`，預報與警報會重建。

### Render 免費服務休眠
第一次請求可能 30–60 秒。Demo 前先開一次網站喚醒。

---

## 7. 更新流程

```powershell
git add .
git commit -m "update: ..."
git push
```

Render 會自動重新部署。若只改資料，直接在 `/admin/` 修改即可，不需要重新部署。

---

## 8. 交付前 10 分鐘檢查

- [ ] 報告中的前台／後台連結可開啟
- [ ] `demo` 與 `admin` 帳密可登入
- [ ] 報告中的截圖與線上網站一致
- [ ] 已放入至少 10 組 AI Prompt 的實際對話截圖
- [ ] PDF 已上傳 TronClass，檔名含組別
- [ ] 已更改或確認展示帳號密碼（若題目要求公開測試帳號則保留）
