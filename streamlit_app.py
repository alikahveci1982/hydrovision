import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="HydroVision AI Pro", page_icon="🤖")

st.title("🤖 HYDROVISION AI PRO")
st.write("Mühendislik Terminali · ISO 1219 · Gemini 1.5 Flash")

api_key = st.text_input("Gemini API Anahtarını Girin", type="password")

source = st.radio("Görsel Kaynağı Seçin:", ("Dosya Yükle", "Kamera Kullan"))
if source == "Dosya Yükle":
    uploaded_file = st.file_uploader("Görsel seç...", type=['jpg', 'png', 'jpeg'])
else:
    uploaded_file = st.camera_input("Fotoğraf Çek")

if uploaded_file is not None and api_key:
    image = Image.open(uploaded_file)
    st.image(image, caption='Analiz Edilecek Görsel', use_container_width=True)
    
    if st.button("🔍 ANALİZ ET"):
        try:
            genai.configure(api_key=api_key)
            # Model ismini güncelledik
            model = genai.GenerativeModel('gemini-1.5-flash-latest') 
            
            prompt = """
            Sen kıdemli bir hidrolik mühendisisin. Bu görseldeki elemanı analiz et:
            1. Bu hangi hidrolik bileşendir? (Örn: Çift etkili silindir)
            2. Bağlantı tiplerini ve fiziksel özelliklerini belirt (Örn: Mafsallı yatak, port yerleşimi).
            3. ISO 1219 sembolünü tarif et.
            4. Eğer mümkünse kullanım alanını tahmin et.
            Lütfen teknik ve profesyonel bir dil kullan.
            """
            
            with st.spinner('Analiz ediliyor...'):
                response = model.generate_content([prompt, image])
                
            st.success("✅ ANALİZ TAMAMLANDI")
            st.markdown(response.text)
            
        except Exception as e:
            st.error(f"Hata detayı: {e}")
