import streamlit as st
import google.generativeai as genai
from PIL import Image

# Uygulama Başlığı ve Ayarlar
st.set_page_config(page_title="HydroVision AI Pro", page_icon="⚙️")
st.title("🤖 HYDROVISION AI PRO")
st.write("🔧 **Mühendislik Terminali v2.0**")

# API Anahtarı Girişi
api_key = st.text_input("Gemini API Anahtarınızı Girin", type="password")

uploaded_file = st.file_uploader("Hidrolik şema veya parça görseli seçin...", type=['jpg', 'png', 'jpeg'])

if uploaded_file is not None and api_key:
    image = Image.open(uploaded_file)
    st.image(image, caption='Analiz Edilecek Görsel', use_container_width=True)
    
    if st.button("🔍 SİSTEMİ ANALİZ ET"):
        try:
            genai.configure(api_key=api_key)
            
            # Çalışan modelleri otomatik bul
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            model_name = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in models else models[0]
            
            model = genai.GenerativeModel(model_name)
            
            prompt = """
            Sen uzman bir hidrolik mühendisisin. Görseli analiz et:
            1. Bileşen adı ve tipi.
            2. Teknik fiziksel detaylar.
            3. ISO 1219 sembol açıklaması.
            Lütfen yanıtı profesyonel bir Türkçe ile ver.
            """
            
            with st.spinner('Analiz yapılıyor...'):
                response = model.generate_content([prompt, image])
                
            st.success("✅ ANALİZ TAMAMLANDI")
            st.markdown(response.text)
            
        except Exception as e:
            st.error(f"Kritik Hata: {str(e)}")
