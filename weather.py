import os
from dotenv import load_dotenv
import requests

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

def hava_durumu_getir(sehir):
    params = {
        "q": sehir,
        "appid": API_KEY,
        "units": "metric",
        "lang": "tr"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if response.status_code == 200:
        print(f"\n📍 Şehir: {data['name']}")
        print(f"🌡️ Sıcaklık: {data['main']['temp']}°C")
        print(f"☁️ Durum: {data['weather'][0]['description']}")
    else:
        print("⚠️ Şehir bulunamadı veya hata oluştu.")

if __name__ == "__main__":
    sehir = input("Hava durumunu öğrenmek istediğiniz şehir: ")
    hava_durumu_getir(sehir)
