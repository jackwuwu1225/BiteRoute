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
    "dessert": [
        "台南市東區 甜點", "台南市東區 冰品", "台南市東區 蛋糕", 
        "台南市東區 豆花", "成大商圈 甜點", "台南市東區 宵夜甜點"
    ],
    "cafe": [
        "台南市東區 咖啡廳", "台南市東區 下午茶", "台南市東區 獨立咖啡", 
        "成大附近 咖啡", "台南市東區 讀書咖啡廳", "台南市東區 甜點咖啡"
    ],
    "local": [
        "台南市東區 牛肉湯", "台南市東區 傳統小吃", "台南市東區 意麵", 
        "台南市東區 肉燥飯", "育樂街 美食", "台南市東區 勝利路 小吃", 
        "成大 美食", "台南市東區 鍋燒意麵", "台南市東區 滷味"
    ],
    "bistro": [
        "台南市東區 餐酒館", "台南市東區 飛鏢吧", "成大 餐酒館", 
        "台南市東區 西班牙小酒館"
    ],
    "bar": [
        "台南市東區 酒吧", "台南市東區 居酒屋", "台南市東區 啤酒吧", 
        "東區 運動酒吧", "台南市東區 調酒", "台南市東區 精釀啤酒"
    ],
    "midnight": [
        "台南市東區 宵夜", "台南市東區 串燒", "台南市東區 鹹酥雞", 
        "東區 深夜食堂", "育樂街 宵夜", "台南市東區 熱炒", "台南市東區 燒烤"
    ]
}

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
    open_times_only = []
    for day_str in weekday_text:
        for zh_day, en_day in DAY_MAPPING.items():
            if day_str.startswith(zh_day):
                day_str = day_str.replace(zh_day, en_day, 1)
                break

        if "休息" in day_str or "Closed" in day_str:
            day_str = day_str.replace("休息", "Closed")
            open_times_only.append(day_str)
            continue
            
        if "24" in day_str:
            open_times_only.append(day_str)
            continue
            
        try:
            day_name, times = day_str.split(":", 1)
            sessions = times.split(",")
            open_sessions = []
            
            for s in sessions:
                start_time = s.split("–")[0].split("-")[0].split("~")[0].strip()
                open_sessions.append(start_time)
                
            open_times_only.append(f"{day_name.strip()}: {', '.join(open_sessions)}")
        except:
            open_times_only.append(day_str)
            
    return open_times_only

def fetch_massive_data():
    all_restaurants = []
    seen_place_ids = set()
    current_id = 1

    print("🚀 開始抓取東區餐廳資料與開店時間 (高容錯隱藏神店版)...")

    for theme, queries in SEARCH_MATRIX.items():
        for query in queries:
            print(f"🔍 正在搜尋: {query}")
            params = {
                "query": query,
                "key": API_KEY,
                "language": "zh-TW" 
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
                    
                    # === 關鍵修改點：放寬評論數，死守高星級 ===
                    if total_ratings < 15 or rating < 3.8:
                        continue

                    price_level = place.get("price_level", 2)
                    estimated_price = price_level * 150 if price_level > 0 else 200

                    details_params = {
                        "place_id": place_id,
                        "fields": "opening_hours",
                        "key": API_KEY,
                        "language": "zh-TW" 
                    }
                    details_response = requests.get(DETAILS_URL, params=details_params).json()
                    opening_hours = details_response.get("result", {}).get("opening_hours", {})
                    raw_weekday_text = opening_hours.get("weekday_text", [])
                    
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