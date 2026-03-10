import streamlit as st
import google.generativeai as genai
from PIL import Image

# Profesyonel Arayüz Ayarları
st.set_page_config(page_title="HydroVision AI Pro", page_icon="⚙️", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 HYDROVISION AI PRO")
st.write("🔧 **Mühendislik Terminali v2.0** | ISO 1219 Standart Analizi")

# API Anahtarı Girişi
api_key = st.text_input("Google Gemini API Anahtarınızı Girin", type="password", help="aistudio.google.com adresinden alınır.")

# Dosya Yükleme
uploaded_file = st.file_uploader("Analiz edilecek hidrolik şema veya parça görselini seçin...", type=['jpg', 'png', 'jpeg'])

if uploaded_file is not None and api_key:
    image = Image.open(uploaded_file)
    st.image(image, caption='Yüklenen Görsel', use_container_width=True)
    
    if st.button("🔍 SİSTEMİ ANALİZ ET"):
        try:
            genai.configure(api_key=api_key)
            
            # Dinamik Model Seçimi (Hata Almamak İçin En Güvenli Yol)
            # Sistem önce flash-latest, sonra flash, sonra pro dener.
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            target_model = "models/gemini-1.5-flash-latest"
            if target_model not in available_models:
                target_model = "models/gemini-1.5-flash"
                if target_model not in available_models:
                    target_model = [m for m in available_models if "gemini" in m][0]

            model = genai.GenerativeModel(model_name=target_model)
            
            prompt = """
            Sen kıdemli bir hidrolik mühendisisin. Bu görseli teknik standartlara göre analiz et:
            1. BİLEŞEN TANIMI: Bu tam olarak nedir? (Örn: Çift etkili silindir, yön valfi vb.)
            2. TEKNİK DETAYLAR: Görseldeki portlar, mafsallar, miller ve varsa etiket bilgilerini açıkla.
            3. ISO 1219: Bu elemanın devre şemasındaki teknik sembolünü tarif et.
            4. MÜHENDİS NOTU: Montaj, bakım veya çalışma prensibi hakkında uzman tavsiyesi ver.
            
            Yanıtını tamamen Türkçe, profesyonel ve teknik bir dille ver.
            """
            
            with st.spinner(f'⚙️ {target_model} üzerinden analiz ediliyor...'):
                response = model.generate_content([prompt, image])
                
            st.success("✅ ANALİZ TAMAMLANDI")
            st.markdown("---")
            st.markdown(response.text)
            
        except Exception as e:
            st.error(f"❌ Kritik Hata: {str(e)}")
            st.info("Lütfen API anahtarınızın doğru olduğundan ve internet bağlantınızın stabil olduğundan emin olun.")
