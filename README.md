# BiteRoute

> 以餐廳連成你的美食星座，讓每一次散步都變成一條可探索的路線。

BiteRoute 是一個以 FastAPI 與原生 JavaScript 製作的幾何美食路跑 Web App。使用者選擇路線主題、預算與探索半徑後，系統會根據目前位置從餐廳資料中挑選節點，套用星座幾何模板，產生一張可互動的餐廳地圖。

## 功能特色

- 三種路線主題：甜點路跑、在地老饕、微醺奇航
- 使用瀏覽器 Geolocation 取得使用者位置，無法定位時以台南成大光復校區作為備援位置
- 依探索半徑、預算與當日營業狀態篩選餐廳
- 以 KD-tree 加速候選餐廳搜尋，並用多目標評分挑選最合適的星座節點
- 支援 11 種星座圖形，包括仙后座、北斗七星與北冕座
- 以 Folium 產生深色互動地圖，顯示餐廳評分、順序與 Google Maps 連結
- 可直接開啟 Google Maps 步行導航、分享路線或匯出分享內容
- 可選擇顯示台南 YouBike「接駁星」與即時可借車數
- 支援 PWA manifest 與 Service Worker，可安裝到支援的行動裝置

## 技術架構

```text
BiteRoute/
├── backend/
│   ├── main.py                 # FastAPI 應用程式入口
│   ├── api/routes.py           # 路線生成 API
│   ├── core/
│   │   ├── optimizer.py        # KD-tree 與星座模板最佳化
│   │   ├── renderer.py         # Folium 地圖產生器
│   │   ├── youbike.py          # TDX YouBike 整合與快取
│   │   ├── geo.py              # 地理距離計算
│   │   └── constants.py        # 主題、星座與演算法設定
│   ├── models/schemas.py       # Pydantic request/response schema
│   └── data/restaurant.json    # 本機餐廳資料
└── frontend/
		├── index.html              # 使用者介面
		├── app.js                  # 定位、API 呼叫與互動流程
		├── style.css               # 視覺樣式
		├── manifest.json           # PWA 設定
		└── sw.js                   # Service Worker
```

## 環境需求

- Python 3.10 或更新版本
- 可使用瀏覽器定位功能的現代瀏覽器
- 前端與後端需同時啟動
- 若要使用 YouBike 接駁星，需申請 TDX API 憑證

## 安裝與啟動

### 1. 建立虛擬環境並安裝套件

在專案根目錄執行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install fastapi uvicorn numpy scipy folium branca requests python-dotenv
```

Linux/macOS 可使用：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install fastapi uvicorn numpy scipy folium branca requests python-dotenv
```

### 2. 啟動後端

後端必須從 `backend` 目錄啟動，因為程式會以相對路徑讀取餐廳資料：

```powershell
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

後端位址：`http://127.0.0.1:8000`

FastAPI 互動式文件：`http://127.0.0.1:8000/docs`

### 3. 啟動前端

另開一個終端機，在專案根目錄執行：

```powershell
cd frontend
python -m http.server 3000
```

接著開啟 `http://localhost:3000`。

> 請不要直接雙擊 `index.html`。透過 `http://localhost` 開啟才能正常使用瀏覽器定位權限、模組載入與跨來源請求。

## 使用流程

1. 開啟前端並允許瀏覽器使用定位資訊。
2. 選擇「甜點路跑」、「在地老饕」或「微醺奇航」。
3. 調整總預算與探索半徑，可選填出發時間。
4. 視需要開啟「顯示 YouBike 接駁星」。
5. 按下「生成星圖」，查看餐廳順序、星座形狀與互動地圖。
6. 從結果頁開始步行導航、分享路線，或重新探索。

## API

### `POST /api/v1/generate_route`

請求內容：

```json
{
	"ui_theme": "dessert_run",
	"search_radius_meters": 1500,
	"total_budget": 800,
	"user_lat": 22.9997,
	"user_lng": 120.2185,
	"departure_time": "19:30",
	"current_day": "Friday",
	"current_time": "19:30",
	"show_youbike": false
}
```

欄位說明：

| 欄位 | 類型 | 說明 |
| --- | --- | --- |
| `ui_theme` | string | `dessert_run`、`local_foodie` 或 `drunken_voyage` |
| `search_radius_meters` | number | 搜尋半徑，必須大於 0 |
| `total_budget` | number | 路線總預算，必須大於 0 |
| `user_lat` / `user_lng` | number | 使用者目前緯度與經度 |
| `departure_time` | string/null | `HH:MM` 格式；前端用於顯示與傳遞出發時間 |
| `current_day` | string/null | 例如 `Friday`，用於營業日篩選 |
| `current_time` | string/null | `HH:MM` 格式，參與時間欄位驗證 |
| `show_youbike` | boolean | 是否查詢並顯示接駁星，預設為 `false` |

成功回應：

```json
{
	"status": "success",
	"constellation_matched": "cassiopeia",
	"matched_shape_name": "仙后座",
	"total_price": 750.0,
	"map_html": "<!DOCTYPE html>...",
	"assignments": [
		{"name": "餐廳名稱", "lat": 22.99, "lng": 120.22}
	]
}
```

可能的 `status`：

- `success`：成功產生路線
- `insufficient_restaurants`：符合主題、距離與營業日條件的餐廳少於 3 家
- `no_valid_route`：找不到符合預算與星座模板的餐廳組合

## YouBike 接駁星（選用）

YouBike 資料來自 [TDX 運輸資料流通服務平台](https://tdx.transportdata.tw/)，目前查詢台南市站點。請先在 TDX 取得 Client ID 與 Client Secret，再於啟動後端前設定環境變數：

PowerShell：

```powershell
$env:TDX_CLIENT_ID="你的ClientId"
$env:TDX_CLIENT_SECRET="你的ClientSecret"
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

cmd：

```cmd
set TDX_CLIENT_ID=你的ClientId
set TDX_CLIENT_SECRET=你的ClientSecret
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

接駁站會在每個餐廳節點 400 公尺內尋找最近站點，並依可借車數顯示顏色：綠色代表車多、琥珀色代表車少、紅色代表無車或停駛。站點位置快取約一天，即時車況快取約 60 秒。

未設定 TDX 金鑰、API 連線失敗或查無資料時，YouBike 功能會自動停用，不會影響一般星座路線生成。

## 更新餐廳資料（可選）

`backend/fetch_places.py` 可透過 Google Places API 重新抓取台南東區的餐廳資料。使用前請設定 `GOOGLE_MAPS_API_KEY`：

```powershell
$env:GOOGLE_MAPS_API_KEY="你的GoogleMapsApiKey"
cd backend
python fetch_places.py
```

腳本會將結果寫入 `backend/data/restaurant.json`。此流程會使用 Google Places Text Search 與 Place Details，可能產生 API 費用，請確認 Google Cloud 專案已啟用對應服務與計費設定。

餐廳資料至少需要下列欄位：

```json
{
	"id": 1,
	"name": "餐廳名稱",
	"lat": 22.99,
	"lng": 120.22,
	"theme": ["dessert"],
	"price": 300,
	"rating": 4.7,
	"user_ratings_total": 167,
	"opening_hours": ["Friday: 11:00, 17:00"]
}
```

## 設計與演算法概念

1. 依 UI 主題映射到餐廳標籤，例如 `dessert_run` 對應 `dessert` 與 `cafe`。
2. 使用 Haversine 距離過濾探索半徑，並依 `current_day` 排除休息中的餐廳。
3. 以餐廳座標建立 KD-tree，為每個星座幾何節點找出附近候選餐廳。
4. 使用 beam search，在不重複餐廳且不超過預算的前提下評估候選組合。
5. 綜合預算貼近度、評分、評論數與星座形狀貼合度，選出最終路線。
6. 由 Folium 產生地圖 HTML，前端以 iframe 嵌入結果。

## 目前限制

- 餐廳資料是隨專案附帶的本機 JSON，不是即時餐廳資料庫。
- 路線導航會開啟 Google Maps，但實際步行路徑與交通狀況由 Google Maps 計算。
- YouBike 接駁星目前固定查詢台南市，若要支援其他城市需調整 `backend/core/constants.py`。
- 後端目前開啟寬鬆 CORS，適合本機展示與開發；正式部署前應限制允許的來源。
- 專案目前未附自動化測試與鎖定版本的 `requirements.txt`，建議部署前補齊依賴鎖定與測試流程。

## 授權與資料來源

本專案使用的外部資料與服務包括：

- 餐廳資料：Google Places API（由 `fetch_places.py` 取得）
- YouBike 站點與即時車況：[TDX 運輸資料流通服務平台](https://tdx.transportdata.tw/)
- 地圖圖磚與地圖渲染：Folium / Leaflet / CartoDB
- 前端字型與圖示：Google Fonts / Font Awesome / Tailwind CDN
