import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="HydroVision AI Pro", page_icon="⚙️")

st.title("🤖 HYDROVISION AI PRO")
st.write("🔧 **Mühendislik Terminali v2.0**")

# API Anahtarı kutusu (Buraya YENİ anahtarı yapıştıracaksın)
api_key = st.text_input("YENİ Gemini API Anahtarınızı Girin", type="password")

uploaded_file = st.file_uploader("Görsel seç...", type=['jpg', 'png', 'jpeg'])

if uploaded_file is not None and api_key:
    image = Image.open(uploaded_file)
    st.image(image, caption='Analiz Edilecek Görsel', use_container_width=True)
    
    if st.button("🔍 SİSTEMİ ANALİZ ET"):
        try:
            genai.configure(api_key=api_key)
            # En stabil model yolu
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
            
            prompt = "Bu bir hidrolik bileşenidir. Lütfen teknik analizini Türkçe yap."
            
            with st.spinner('Analiz ediliyor...'):
                response = model.generate_content([prompt, image])
                
            st.success("✅ ANALİZ TAMAMLANDI")
            st.markdown(response.text)
            
        except Exception as e:
            st.error(f"Kritik Hata: {str(e)}")
