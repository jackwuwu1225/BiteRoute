import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

print(f"正在測試的 API KEY: {API_KEY[:5]}... (只顯示前5碼確認有讀到)")

url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
params = {
    "query": "台南市東區 甜點",
    "key": API_KEY,
    "language": "zh-TW"
}

response = requests.get(url, params=params)

print("\n--- Google 伺服器回傳結果 ---")
print(f"HTTP 狀態碼: {response.status_code}")
# 直接把 Google 吐回來的原始錯誤訊息印出來！
print(response.json())