# 期中專題：weather.gov Bad UI Redesign 實作（第八組）

根據作業一的 Bad UI 分析與 9 張分鏡，實作可操作的前台網站 + Django 管理後台 + Neon PostgreSQL + 雲端部署。

## 頁面（前台 4 頁 + 後台）

| 頁面 | 路由 | 內容 |
| --- | --- | --- |
| 首頁（Today） | `/` | 在地摘要、單一搜尋、警報 Banner、會員/訪客差異 |
| 7 天預報 | `/city/<slug>/` | 週末標示、降雨柱狀圖、最佳時段、收藏 |
| 警報中心 | `/alerts/` | 嚴重度/地區篩選、建議行動、空狀態 |
| 會員註冊/登入/會員中心 | `/accounts/...` | 登入前後介面差異、偏好設定 |
| Django Admin 後台 | `/admin/` | 城市、預報、警報、會員、收藏管理 |

對應 Bad UI 問題：問題1（首屏四層）、2（單一搜尋）、3（設計系統統一頁首）、4（字級≥14px）、5（等高卡片＋柱狀圖）、6（專業連結收納）、7（地名標題＋空狀態）、8（警報優先）。

## 本機執行

```sh
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py seed_demo
.venv\Scripts\python manage.py createsuperuser   # 建後台帳號
.venv\Scripts\python manage.py runserver
```

- 網站：http://127.0.0.1:8000/
- 後台：http://127.0.0.1:8000/admin/
- 示範會員：demo / Demo1234!（seed_demo 建立，收藏 NY、Miami）

## 切換 Neon PostgreSQL（本機測試）

```powershell
$env:DATABASE_URL = "postgresql://<user>:<password>@<host>/<dbname>?sslmode=require"
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py seed_demo
```

## 部署（Render + Neon）

Render Web Service（Build: `pip install -r requirements.txt && pip install whitenoise gunicorn`；
Start: `gunicorn config.wsgi:application`）並設定環境變數：

```
DATABASE_URL = postgresql://...（Neon 連線字串）
DJANGO_SECRET_KEY = <隨機字串>
DJANGO_DEBUG = 0
DJANGO_ALLOWED_HOSTS = .onrender.com
```

部署後執行一次 Shell：
`python manage.py migrate && python manage.py seed_demo && python manage.py collectstatic --noinput`
（Render 免費方案可於 Build Command 加上 `python manage.py collectstatic --noinput`；seed_demo 建議在首部署後手動執行一次）
