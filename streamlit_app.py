import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="HydroVision AI Pro", page_icon="🤖")

st.title("🤖 HYDROVISION AI PRO")
st.write("Mühendislik Terminali · ISO 1219 · Gemini 1.5 PRO")

# API Anahtarı Girişi (Google AI Studio'dan aldığın anahtar)
api_key = st.text_input("Gemini API Anahtarını Girin", type="password")

source = st.radio("Görsel Kaynağı Seçin:", ("Dosya Yükle", "Kamera Kullan"))
if source == "Dosya Yükle":
    uploaded_file = st.file_uploader("Şema veya Parça Görseli seç...", type=['jpg', 'png', 'jpeg'])
else:
    uploaded_file = st.camera_input("Fotoğraf Çek")

if uploaded_file is not None and api_key:
    image = Image.open(uploaded_file)
    st.image(image, caption='Analiz Edilecek Görsel', use_container_width=True)
    
    if st.button("🔍 ANALİZ ET"):
        try:
            # Gemini Yapılandırması
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash') # Hızlı ve stabil model
            
            # Mühendislik Odaklı Prompt
            prompt = """
            Sen uzman bir hidrolik mühendisisin. Bu görseli analiz et:
            1. ISO 1219 sembollerini tek tek tanımla.
            2. Eğer gerçek bir parçaysa marka/model tahmini yap.
            3. Sistemin çalışma mantığını ve akış yollarını Türkçe açıkla.
            4. Varsa arıza yapabilecek noktaları belirt.
            """
            
            with st.spinner('Zeka işleniyor...'):
                response = model.generate_content([prompt, image])
                
            st.success("✅ ANALİZ TAMAMLANDI")
            st.markdown(response.text)
            
        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")
