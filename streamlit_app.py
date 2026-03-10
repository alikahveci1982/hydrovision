import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse

# Sayfa Yapılandırması ve Mobil Tasarım (CSS)
st.set_page_config(page_title="HydroVision Pro", page_icon="⚙️", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    div.stButton > button:first-child {
        background-color: #007bff; color: white; border-radius: 10px;
        height: 60px; width: 100%; font-size: 20px; font-weight: bold;
        border: none; margin-top: 20px; box-shadow: 0px 4px 10px rgba(0,123,255,0.3);
    }
    .stTextInput>div>div>input { background-color: #161b22; color: white; border: 1px solid #30363d; }
    .result-card { 
        background-color: #161b22; padding: 20px; border-radius: 15px; 
        border: 1px solid #30363d; margin-bottom: 20px;
    }
    .link-btn {
        display: inline-block; padding: 10px 20px; margin: 5px;
        border-radius: 8px; text-decoration: none; font-weight: bold;
        text-align: center; color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 HYDROVISION AI")
st.caption("🚀 Hidrolik Arıza & Yedek Parça Terminali")

# API Anahtarı
api_key = st.text_input("🔑 Gemini API Anahtarı", type="password", placeholder="Buraya yapıştırın...")

# Görsel Kaynağı (Mobil için Kamera Öncelikli)
source = st.radio("📸 Görsel Kaynağı:", ("Kamera Kullan", "Dosya Yükle"), horizontal=True)

if source == "Kamera Kullan":
    uploaded_file = st.camera_input("Parçayı Fotoğrafla")
else:
    uploaded_file = st.file_uploader("Galeriden Seç", type=['jpg', 'png', 'jpeg'])

if uploaded_file and api_key:
    image = Image.open(uploaded_file)
    st.image(image, caption='Analiz Hazır', use_container_width=True)
    
    if st.button("🔍 DERİN ANALİZİ BAŞLAT"):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = """
            Sen kıdemli bir hidrolik mühendisisin. Görseli analiz et:
            1. BİLEŞEN: Parçanın tam teknik adı.
            2. ARIZA TESPİTİ: Görseldeki belirtilere göre (yağ sızıntısı, aşınma, renk değişimi) olası 3 arıza nedeni.
            3. TEKNİK ÖNERİ: Tamir mi edilmeli, değişim mi gerekli?
            4. SATIN ALMA: Parçanın piyasa standart kodu (Örn: NG6, Cetop 3 vb.).
            Yanıtı kısa, öz ve profesyonel Türkçe ile ver.
            """
            
            with st.spinner('⚙️ Yapay Zeka Analiz Ediyor...'):
                response = model.generate_content([prompt, image])
                res = response.text
                
            st.markdown(f'<div class="result-card">{res}</div>', unsafe_allow_html=True)
            
            # Akıllı Satın Alma Linkleri
            st.subheader("🛒 Parça Tedarik Kanalları")
            query = "Hidrolik " + res.split('\n')[0].replace("1. BİLEŞEN:", "").strip()
            encoded = urllib.parse.quote(query)
            
            st.markdown(f"""
                <div style="text-align: center;">
                    <a href="https://www.google.com/search?q={encoded}+satın+al" class="link-btn" style="background-color: #4285F4;">Google Ara</a>
                    <a href="https://www.google.com/search?q={encoded}+fiyatları" class="link-btn" style="background-color: #FF6000;">Fiyat Karşılaştır</a>
                    <a href="https://www.google.com/search?q={encoded}+catalog+pdf" class="link-btn" style="background-color: #28a745;">Teknik Katalog</a>
                </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Hata: {str(e)}")
