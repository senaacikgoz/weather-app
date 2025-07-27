from datetime import datetime
import streamlit as st
import requests
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import base64
import json
from streamlit_folium import st_folium
import folium

def load_translations(lang):
    try:
        with open("translations.json", "r", encoding="utf-8") as f:
            return json.load(f)[lang]
    except FileNotFoundError:
        
        return {
            "page_title": "Hava Durumu Uygulaması", "description": "Konumunuzu girerek veya haritadan seçerek hava durumunu öğrenin.",
            "location_name": "Konum Adı", "get_weather": "Hava Durumunu Getir", "enter_location_warning": "⚠️ Lütfen bir konum adı girin.",
            "location_not_found": "❌ Konum bulunamadı veya API hatası oluştu.", "api_error": "API isteği sırasında bir hata oluştu",
            "weather_for": "için hava durumu", "results": "📊 Sonuçlar", "temperature": "Sıcaklık", "feels_like": "Hissedilen",
            "humidity": "Nem", "wind": "Rüzgar", "pressure": "Basınç", "sunrise": "Güneş Doğuşu", "sunset": "Güneş Batışı",
            "next_24h_temp": "Sonraki 24 Saatlik Sıcaklık Değişimi", "next_24h_temp_forecast": "Sonraki 24 Saat İçin Sıcaklık Tahmini",
            "next_24h_humidity": "Sonraki 24 Saatlik Nem Değişimi", "next_24h_humidity_forecast": "Sonraki 24 Saat İçin Nem Tahmini",
            "next_24h_wind": "Sonraki 24 Saatlik Rüzgar Değişimi", "next_24h_wind_forecast": "Sonraki 24 Saat İçin Rüzgar Hızı Tahmini",
            "5_day_forecast": "📅 5 Günlük Tahmin", "day_mode": "Gündüz Moduna Geç", "night_mode": "Gece Moduna Geç",
            "settings": "Ayarlar", "select_location_map": "Haritadan Konum Seçin"
        }


if 'lang' not in st.session_state:
    st.session_state.lang = 'tr'

translations = load_translations(st.session_state.lang)


load_dotenv()
API_KEY = os.getenv("API_KEY")

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
REVERSE_GEO_URL = "http://api.openweathermap.org/geo/1.0/reverse"

if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'forecast_data' not in st.session_state:
    st.session_state.forecast_data = None

THEMES = {
    'dark': {
        "bg_color": "#0E1117", "text_color": "#FAFAFA", "secondary_text_color": "#808080",
        "card_bg_color": "#161B22", "border_color": "#30363D",
        "theme_button_text": "☀️ " + translations.get("day_mode", "Gündüz Moduna Geç"),
        "button": {"bg_color": "#161B22", "text_color": "#FAFAFA", "border_color": "#30363D"}
    },
    'light': {
        "bg_color": "#F0F2F6", "text_color": "#0E1117", "secondary_text_color": "#5A5A5A",
        "card_bg_color": "#FFFFFF", "border_color": "#D1D1D1",
        "theme_button_text": "🌙 " + translations.get("night_mode", "Gece Moduna Geç"),
        "button": {"bg_color": "#FFFFFF", "text_color": "#0E1117", "border_color": "#D1D1D1"}
    }
}


def ipden_sehir_bul():
    try:
        response = requests.get("https://ipinfo.io/json", timeout=5)
        if response.status_code == 200:
            return response.json().get("city")
    except requests.RequestException:
        return None
    return None

def konum_detay_getir(lat, lon):
    params = {"lat": lat, "lon": lon, "limit": 1, "appid": API_KEY}
    response = requests.get(REVERSE_GEO_URL, params=params)
    if response.status_code == 200 and response.json():
        return response.json()[0].get('name')
    return None

def fetch_weather_data(sehir=None, lat=None, lon=None):
    try:
        if sehir:
            params = {"q": sehir, "appid": API_KEY, "units": "metric", "lang": st.session_state.lang}
        elif lat and lon:
            params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric", "lang": st.session_state.lang}
        else:
            return

        weather_response = requests.get(BASE_URL, params=params)
        forecast_response = requests.get(FORECAST_URL, params=params)

        if weather_response.status_code == 200 and forecast_response.status_code == 200:
            st.session_state.weather_data = weather_response.json()
            st.session_state.forecast_data = forecast_response.json()
        else:
            st.session_state.weather_data = None
            st.session_state.forecast_data = None
            st.error(translations["location_not_found"])
    except requests.RequestException as e:
        st.error(f"{translations['api_error']}: {e}")

def tema_degistir():
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'

@st.cache_data
def icon_to_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return None

def get_icon(weather_main, is_day):
    main = weather_main.lower()
    if "clear" in main:
        return icon_to_base64("icon/sun.svg") if is_day else icon_to_base64("icon/moon.svg")
    elif "clouds" in main:
        return icon_to_base64("icon/cloudy.svg")
    elif "rain" in main or "drizzle" in main:
        return icon_to_base64("icon/rainy.svg")
    elif "wind" in main:
        return icon_to_base64("icon/windy.svg")
    else:
        return icon_to_base64("icon/cloudy.svg")


st.set_page_config(page_title="☁️ " + translations["page_title"], page_icon="🌦️", layout="centered")
active_theme = THEMES[st.session_state.theme]

st.markdown(f"""
<style>
.stApp {{ background-color: {active_theme['bg_color']}; }}
h1, h3, p, strong, span, div {{ color: {active_theme['text_color']}; }}
.stTextInput > div > div > input {{
    color: {active_theme['text_color']};
    background-color: {active_theme['card_bg_color']};
}}
.stButton > button {{
    color: {active_theme['button']['text_color']};
    background-color: {active_theme['button']['bg_color']};
    border: 1px solid {active_theme['button']['border_color']};
}}
.stButton > button:hover {{
    border-color: #FF6347;
    color: #FF6347;
}}
</style>
""", unsafe_allow_html=True)


with st.sidebar:
    st.title(translations["settings"])


    def set_language():
        st.session_state.lang = 'en' if st.session_state.lang == 'tr' else 'tr'

    st.button("🇹🇷 Türkçe / 🇬🇧 English", on_click=set_language)


    st.subheader(translations["select_location_map"])
    m = folium.Map(location=[41.0082, 28.9784], zoom_start=6)
    map_data = st_folium(m, height=400, use_container_width=True)

    if map_data and map_data["last_clicked"]:
        lat, lon = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]
        fetch_weather_data(lat=lat, lon=lon)


st.markdown(f"<h1 style='text-align: center;'>☁️ {translations['page_title']}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: {active_theme['secondary_text_color']}'>{translations['description']}</p>", unsafe_allow_html=True)

default_city = ipden_sehir_bul() or "İstanbul"
sehir_input = st.text_input(translations["location_name"], value=default_city, key="sehir_input_key")

if st.button(translations["get_weather"]):
    if not sehir_input:
        st.warning(translations["enter_location_warning"])
    else:
        fetch_weather_data(sehir=sehir_input)

if st.session_state.weather_data and st.session_state.forecast_data:
    data = st.session_state.weather_data
    forecast_data = st.session_state.forecast_data

    ilce = data['name']
    sehir_ana = konum_detay_getir(data['coord']['lat'], data['coord']['lon'])
    konum_gosterim = f"{ilce}, {sehir_ana}" if sehir_ana and ilce.lower() != sehir_ana.lower() else ilce
    st.success(f"{konum_gosterim} {translations['weather_for']}")

    st.button(active_theme['theme_button_text'], on_click=tema_degistir, key="theme_button")

    is_day = data['sys']['sunrise'] < datetime.now().timestamp() < data['sys']['sunset']
    weather_icon_b64 = get_icon(data['weather'][0]['main'], is_day)

    st.markdown(f"""
    <div style='background-color: {active_theme['card_bg_color']}; border: 1px solid {active_theme['border_color']}; padding: 20px; border-radius: 10px; margin-top: 20px;'>
        <h3>📊 {translations['results']}</h3>
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <img src="data:image/svg+xml;base64,{weather_icon_b64}" width="50" height="50" style="margin-right: 15px;">
            <p style="font-size: 1.2em; margin: 0;"><strong>{data['weather'][0]['description'].capitalize()}</strong></p>
        </div>
        <p><strong>🌡️ {translations['temperature']}:</strong> {data['main']['temp']}°C</p>
        <p><strong>{translations['feels_like']}:</strong> {data['main']['feels_like']}°C</p>
        <p><strong>{translations['humidity']}:</strong> {data['main']['humidity']}%</p>
        <p><strong>{translations['wind']}:</strong> {data['wind']['speed']} m/s</p>
        <p><strong>{translations['pressure']}:</strong> {data['main']['pressure']} hPa</p>
        <p><strong>{translations['sunrise']}:</strong> {datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M')}</p>
        <p><strong>{translations['sunset']}:</strong> {datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M')}</p>
    </div>
    """, unsafe_allow_html=True)


    tab1, tab2, tab3 = st.tabs([f"🌡️ {translations['temperature']}", f"💧 {translations['humidity']}", f"💨 {translations['wind']}"])

    sonraki_tahminler = forecast_data['list'][:8]
    zamanlar = [datetime.strptime(t['dt_txt'], "%Y-%m-%d %H:%M:%S").strftime("%a %H:%M") for t in sonraki_tahminler]

    with tab1:
        st.markdown(f"<h3>🌡️ {translations['next_24h_temp']}</h3>", unsafe_allow_html=True)
        sicakliklar = [t['main']['temp'] for t in sonraki_tahminler]
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor(active_theme['bg_color'])
        ax.set_facecolor(active_theme['card_bg_color'])
        ax.plot(zamanlar, sicakliklar, marker="o", color="#FF6347", linestyle='-')
        ax.tick_params(axis='x', colors=active_theme['text_color'])
        ax.tick_params(axis='y', colors=active_theme['text_color'])
        for spine in ax.spines.values(): spine.set_edgecolor(active_theme['border_color'])
        ax.set_title(translations['next_24h_temp_forecast'], color=active_theme['text_color'])
        st.pyplot(fig)

    with tab2:
        st.markdown(f"<h3>💧 {translations['next_24h_humidity']}</h3>", unsafe_allow_html=True)
        nem_oranlari = [t['main']['humidity'] for t in sonraki_tahminler]
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor(active_theme['bg_color'])
        ax.set_facecolor(active_theme['card_bg_color'])
        ax.plot(zamanlar, nem_oranlari, marker="o", color="#1E90FF", linestyle='-')
        ax.tick_params(axis='x', colors=active_theme['text_color'])
        ax.tick_params(axis='y', colors=active_theme['text_color'])
        for spine in ax.spines.values(): spine.set_edgecolor(active_theme['border_color'])
        ax.set_title(translations['next_24h_humidity_forecast'], color=active_theme['text_color'])
        st.pyplot(fig)

    with tab3:
        st.markdown(f"<h3>💨 {translations['next_24h_wind']}</h3>", unsafe_allow_html=True)
        ruzgar_hizlari = [t['wind']['speed'] for t in sonraki_tahminler]
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor(active_theme['bg_color'])
        ax.set_facecolor(active_theme['card_bg_color'])
        ax.plot(zamanlar, ruzgar_hizlari, marker="o", color="#32CD32", linestyle='-')
        ax.tick_params(axis='x', colors=active_theme['text_color'])
        ax.tick_params(axis='y', colors=active_theme['text_color'])
        for spine in ax.spines.values(): spine.set_edgecolor(active_theme['border_color'])
        ax.set_title(translations['next_24h_wind_forecast'], color=active_theme['text_color'])
        st.pyplot(fig)

    
    st.markdown(f"<h3>📅 {translations['5_day_forecast']}</h3>", unsafe_allow_html=True)
    gunluk = {}
    for i in forecast_data["list"]:
        tarih = i["dt_txt"].split(" ")[0]
        temp = i["main"]["temp"]
        gunluk.setdefault(tarih, {"min": temp, "max": temp})
        gunluk[tarih]["min"] = min(gunluk[tarih]["min"], temp)
        gunluk[tarih]["max"] = max(gunluk[tarih]["max"], temp)

    gunluk_listesi = list(gunluk.items())[:5]
    if len(gunluk) > 5 and datetime.now().hour > 12:
        gunluk_listesi = list(gunluk.items())[1:6]

    for tarih, deger in gunluk_listesi:
        gun_adi = datetime.strptime(tarih, '%Y-%m-%d').strftime('%a')
        formatli_tarih = datetime.strptime(tarih, '%Y-%m-%d').strftime('%d %b')
        st.markdown(f"""
        <div style="background-color: {active_theme['card_bg_color']}; border: 1px solid {active_theme['border_color']}; padding: 12px; border-radius: 10px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="font-size: 1.1em;">{gun_adi} <span style="color: {active_theme['secondary_text_color']}; font-size: 0.9em;">({formatli_tarih})</span></strong>
                <div>
                    <span style="color: #66b2ff; font-weight: bold;">Min: {round(deger['min'])}°C</span>
                    <span style="margin-left: 15px; color: #ff6666; font-weight: bold;">Max: {round(deger['max'])}°C</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
