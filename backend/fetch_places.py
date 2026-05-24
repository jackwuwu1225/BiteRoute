import os
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

SEARCH_MATRIX = {
    "dessert": ["台南市東區 甜點", "台南市東區 冰品", "台南市東區 蛋糕"],
    "cafe": ["台南市東區 咖啡廳", "台南市東區 下午茶", "台南市東區 獨立咖啡"],
    "local": ["台南市東區 牛肉湯", "台南市東區 傳統小吃", "台南市東區 意麵", "台南市東區 肉燥飯"],
    "bistro": ["台南市東區 餐酒館", "台南市東區 飛鏢吧"],
    "bar": ["台南市東區 酒吧", "台南市東區 居酒屋", "台南市東區 啤酒吧"],
    "midnight": ["台南市東區 宵夜", "台南市東區 串燒", "台南市東區 鹹酥雞"]
}

# 中翻英的星期對照表
DAY_MAPPING = {
    "星期一": "Monday",
    "星期二": "Tuesday",
    "星期三": "Wednesday",
    "星期四": "Thursday",
    "星期五": "Friday",
    "星期六": "Saturday",
    "星期日": "Sunday",
    "星期天": "Sunday"
}

def clean_opening_hours(weekday_text: list) -> list:
    """過濾掉關店時間，只保留開店時間，並將星期與狀態轉換為英文"""
    open_times_only = []
    for day_str in weekday_text:
        
        # 1. 替換星期幾為英文
        for zh_day, en_day in DAY_MAPPING.items():
            if day_str.startswith(zh_day):
                day_str = day_str.replace(zh_day, en_day, 1)
                break

        # 2. 處理特殊狀態 (休息 / 24小時)
        if "休息" in day_str or "Closed" in day_str:
            day_str = day_str.replace("休息", "Closed")
            open_times_only.append(day_str)
            continue
            
        if "24" in day_str:
            open_times_only.append(day_str)
            continue
            
        try:
            # 3. 解析時間區間 (例如 "Monday: 11:00 – 14:00, 17:00 – 21:00")
            day_name, times = day_str.split(":", 1)
            sessions = times.split(",")
            open_sessions = []
            
            for s in sessions:
                # 兼容 Google 可能使用的各種破折號 (–, -, ~) 並切出開始時間
                start_time = s.split("–")[0].split("-")[0].split("~")[0].strip()
                open_sessions.append(start_time)
                
            open_times_only.append(f"{day_name.strip()}: {', '.join(open_sessions)}")
        except:
            # 如果解析失敗，就退回原本的字串防呆
            open_times_only.append(day_str)
            
    return open_times_only


def fetch_massive_data():
    all_restaurants = []
    seen_place_ids = set()
    current_id = 1

    print("🚀 開始抓取東區餐廳資料與開店時間 (英文化版本)...")

    for theme, queries in SEARCH_MATRIX.items():
        for query in queries:
            print(f"🔍 正在搜尋: {query}")
            params = {
                "query": query,
                "key": API_KEY,
                "language": "zh-TW" # 這裡維持 zh-TW 確保時間格式是 24 小時制
            }

            while True:
                response = requests.get(SEARCH_URL, params=params)
                if response.status_code != 200:
                    break

                data = response.json()
                results = data.get("results", [])

                for place in results:
                    place_id = place.get("place_id")
                    
                    if place_id in seen_place_ids:
                        continue
                    
                    total_ratings = place.get("user_ratings_total", 0)
                    rating = place.get("rating", 0)
                    if total_ratings < 50 or rating < 3.5:
                        continue

                    price_level = place.get("price_level", 2)
                    estimated_price = price_level * 150 if price_level > 0 else 200

                    # 呼叫 Details API 取得營業時間
                    details_params = {
                        "place_id": place_id,
                        "fields": "opening_hours",
                        "key": API_KEY,
                        "language": "zh-TW" # 維持抓中文再用自己寫的邏輯翻譯
                    }
                    details_response = requests.get(DETAILS_URL, params=details_params).json()
                    opening_hours = details_response.get("result", {}).get("opening_hours", {})
                    raw_weekday_text = opening_hours.get("weekday_text", [])
                    
                    # 進行時間清理與英文化
                    clean_weekday_text = clean_opening_hours(raw_weekday_text)

                    restaurant = {
                        "id": current_id,
                        "name": place.get("name"),
                        "lat": place.get("geometry", {}).get("location", {}).get("lat"),
                        "lng": place.get("geometry", {}).get("location", {}).get("lng"),
                        "theme": [theme],
                        "price": estimated_price,
                        "rating": rating,
                        "user_ratings_total": total_ratings,
                        "opening_hours": clean_weekday_text
                    }
                    
                    all_restaurants.append(restaurant)
                    seen_place_ids.add(place_id)
                    current_id += 1

                next_page_token = data.get("next_page_token")
                if not next_page_token:
                    break
                
                time.sleep(2)
                params = {
                    "pagetoken": next_page_token,
                    "key": API_KEY
                }

    os.makedirs("data", exist_ok=True)
    file_path = "data/restaurant.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(all_restaurants, f, ensure_ascii=False, indent=2)

    print(f"✅ 抓取完成！總共收錄了 {len(all_restaurants)} 家餐廳。")

if __name__ == "__main__":
    fetch_massive_data()