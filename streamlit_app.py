import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse

# Profesyonel Mobil Arayüz Ayarları (CSS)
st.set_page_config(page_title="HydroVision Pro", page_icon="⚙️", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    div.stButton > button:first-child {
        background-color: #ff4b4b; color: white; border-radius: 12px;
        height: 70px; width: 100%; font-size: 22px; font-weight: bold;
        border: none; margin-top: 10px; box-shadow: 0px 4px 15px rgba(255,75,75,0.4);
    }
    .result-card { 
        background-color: #161b22; padding: 20px; border-radius: 15px; 
        border: 1px solid #30363d; margin-top: 20px; font-size: 16px;
    }
    .link-btn {
        display: block; padding: 15px; margin: 10px 0; border-radius: 10px;
        text-decoration: none; font-weight: bold; text-align: center; color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 HYDROVISION PRO")
st.caption("🚀 Mobil Arıza Tespit & Yedek Parça Terminali")

# API Girişi
api_key = st.text_input("🔑 Gemini API Anahtarı", type="password")

# S24 Ultra için Kamera Öncelikli Giriş
source = st.radio("📸 Giriş Yöntemi:", ("Kamera Kullan", "Galeriden Seç"), horizontal=True)
uploaded_file = st.camera_input("Parçayı Fotoğrafla") if source == "Kamera Kullan" else st.file_uploader("Dosya Seç", type=['jpg', 'png', 'jpeg'])

if uploaded_file and api_key:
    image = Image.open(uploaded_file)
    st.image(image, caption='Analiz Hazır', use_container_width=True)
    
    if st.button("🔍 DERİN ANALİZİ BAŞLAT"):
        try:
            genai.configure(api_key=api_key)
            
            # --- 404 HATASINI ÇÖZEN OTOMATİK MODEL SEÇİCİ ---
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            model_path = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available_models else available_models[0]
            
            model = genai.GenerativeModel(model_name=model_path)
            
            prompt = """
            Sen uzman bir hidrolik mühendisisin. Bu görseli analiz et:
            1. BİLEŞEN: Parçanın tam adı.
            2. ARIZA ANALİZİ: Görseldeki aşınma, sızıntı veya yapıya göre olası 3 arıza nedeni.
            3. ÇÖZÜM: Tamir/Değişim önerisi.
            4. SATIN ALMA: Piyasa kodu (Örn: NG10, 1/2" BSP vb.).
            Yanıtı profesyonel Türkçe ile teknik rapor formatında ver.
            """
            
            with st.spinner(f'⚙️ {model_path} Veri İşliyor...'):
                response = model.generate_content([prompt, image])
                res = response.text
                
            st.success("✅ ANALİZ TAMAMLANDI")
            st.markdown(f'<div class="result-card">{res}</div>', unsafe_allow_html=True)
            
            # Dinamik Arama Linkleri
            comp_name = res.split('\n')[0].replace("1. BİLEŞEN:", "").strip()
            encoded = urllib.parse.quote(f"Hidrolik {comp_name}")
            
            st.subheader("🛒 Yedek Parça & Katalog")
            st.markdown(f"""
                <a href="https://www.google.com/search?q={encoded}+fiyatı" class="link-btn" style="background-color: #4285F4;">Google'da Fiyat Ara</a>
                <a href="https://www.google.com/search?q={encoded}+yedek+parça" class="link-btn" style="background-color: #FF6000;">Yedek Parça Tedarik</a>
                <a href="https://www.google.com/search?q={encoded}+pdf+catalog" class="link-btn" style="background-color: #28a745;">Teknik Katalog İndir</a>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Sistem Hatası: {str(e)}")
