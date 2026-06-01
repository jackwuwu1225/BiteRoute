# BiteRoute

以餐廳連成你的美食星座 — 幾何美食路跑 App。

## 啟動方式

### 後端（FastAPI）

```bash
cd backend
python -m uvicorn main:app --reload
# 啟動於 http://127.0.0.1:8000
```

### 前端

```bash
cd frontend
python -m http.server 3000
# 瀏覽器開啟 http://localhost:3000
```

> 請用 `http://localhost` 開啟前端，勿直接雙擊 `index.html`（`file://` 會被瀏覽器封鎖定位權限）。

## YouBike 接駁星（選用功能）

地圖可在每個星座節點旁顯示最近的 YouBike 站點（「接駁星」），並依即時可借車數以顏色標示（綠＝車多／琥珀＝車少／暗紅＝無車或停駛）。前端輸入頁可用「顯示 YouBike 接駁星」開關切換，預設關閉。

資料來源為 [TDX 運輸資料流通服務平台](https://tdx.transportdata.tw/)，需設定 API 金鑰環境變數**後再啟動後端**：

PowerShell：
```powershell
$env:TDX_CLIENT_ID="你的ClientId"
$env:TDX_CLIENT_SECRET="你的ClientSecret"
python -m uvicorn main:app --reload
```

cmd：
```cmd
set TDX_CLIENT_ID=你的ClientId
set TDX_CLIENT_SECRET=你的ClientSecret
python -m uvicorn main:app --reload
```

金鑰可在 TDX 會員中心 → 資料服務金鑰取得。**若未設定金鑰，接駁星功能會自動停用，不影響星座路線生成。**

> 即時性說明：站點位置長快取，可借車數短快取（約 60 秒），marker 會標註資料時間。
