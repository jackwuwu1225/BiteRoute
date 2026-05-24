import os
import time
import json
import requests
from dotenv import load_dotenv

# 載入 .env 裡的 API KEY
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
BASE_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

# 擴增搜尋矩陣：利用多種關鍵字把東區塞滿
SEARCH_MATRIX = {
    "dessert": ["台南市東區 甜點", "台南市東區 冰品", "台南市東區 蛋糕"],
    "cafe": ["台南市東區 咖啡廳", "台南市東區 下午茶", "台南市東區 獨立咖啡"],
    "local": ["台南市東區 牛肉湯", "台南市東區 傳統小吃", "台南市東區 意麵", "台南市東區 肉燥飯"],
    "bistro": ["台南市東區 餐酒館"],
    "bar": ["台南市東區 酒吧", "台南市東區 居酒屋", "台南市東區 啤酒吧"],
    "midnight": ["台南市東區 宵夜", "台南市東區 串燒", "台南市東區 鹹酥雞"]
}

def fetch_massive_data():
    all_restaurants = []
    seen_place_ids = set() # 用來記錄抓過的店，防止不同關鍵字抓到同一家
    current_id = 1

    print("🚀 開始火力全開抓取東區餐廳資料...")

    for theme, queries in SEARCH_MATRIX.items():
        for query in queries:
            print(f"🔍 正在搜尋關鍵字: {query}")
            params = {
                "query": query,
                "key": API_KEY,
                "language": "zh-TW"
            }

            while True:
                response = requests.get(BASE_URL, params=params)
                if response.status_code != 200:
                    print(f"❌ API 請求失敗: {response.status_code}")
                    break

                data = response.json()
                results = data.get("results", [])

                for place in results:
                    place_id = place.get("place_id")
                    
                    # 1. 檢查是否已經抓過這家店 (去重複)
                    if place_id in seen_place_ids:
                        continue
                    
                    # 2. 嚴格品質控管：評價數低於 50 或是沒評分的，不要！
                    total_ratings = place.get("user_ratings_total", 0)
                    rating = place.get("rating", 0)
                    if total_ratings < 50 or rating < 3.5:
                        continue

                    # 3. 處理價格 (Google 價格等級 0-4，若無則預設為 2)
                    price_level = place.get("price_level", 2)
                    # 簡單估算客單價 (可自行調整係數)
                    estimated_price = price_level * 150 if price_level > 0 else 200

                    restaurant = {
                        "id": current_id,
                        "name": place.get("name"),
                        "lat": place.get("geometry", {}).get("location", {}).get("lat"),
                        "lng": place.get("geometry", {}).get("location", {}).get("lng"),
                        "theme": [theme], # 標記所屬主題
                        "price": estimated_price,
                        "rating": rating,
                        "user_ratings_total": total_ratings
                    }
                    
                    all_restaurants.append(restaurant)
                    seen_place_ids.add(place_id)
                    current_id += 1

                # 4. 處理自動翻頁 (Pagination)
                next_page_token = data.get("next_page_token")
                if not next_page_token:
                    break # 這一組關鍵字抓到底了
                
                print("   ⏳ 發現下一頁，等待 2 秒後繼續抓取...")
                time.sleep(2) # Google 強制要求翻頁 token 產生後需要等一小段時間
                params = {
                    "pagetoken": next_page_token,
                    "key": API_KEY
                }

    # 5. 寫入本地 JSON 檔案
    os.makedirs("data", exist_ok=True)
    file_path = "data/restaurant.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(all_restaurants, f, ensure_ascii=False, indent=2)

    print(f"✅ 抓取完成！總共成功收錄了 {len(all_restaurants)} 家精選餐廳，已存入 {file_path}")

if __name__ == "__main__":
    fetch_massive_data()