import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="HydroVision AI Pro", page_icon="⚙️")

st.title("🤖 HYDROVISION AI PRO")
st.write("🔧 **Mühendislik Terminali v2.0** | ISO 1219 Analiz")

# API Anahtarı
api_key = st.text_input("Gemini API Anahtarınızı Girin", type="password")

uploaded_file = st.file_uploader("Görsel seç...", type=['jpg', 'png', 'jpeg'])

if uploaded_file is not None and api_key:
    image = Image.open(uploaded_file)
    st.image(image, caption='Yüklenen Görsel', use_container_width=True)
    
    if st.button("🔍 SİSTEMİ ANALİZ ET"):
        try:
            genai.configure(api_key=api_key)
            
            # 1. ADIM: API'den aktif modelleri sorgula (404 hatasını bitiren nokta)
            active_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # 2. ADIM: En uygun modeli otomatik seç
            if "models/gemini-1.5-flash" in active_models:
                model_to_use = "models/gemini-1.5-flash"
            elif "models/gemini-1.5-pro" in active_models:
                model_to_use = "models/gemini-1.5-pro"
            else:
                model_to_use = active_models[0] # Listede ne varsa onu kullan

            model = genai.GenerativeModel(model_name=model_to_use)
            
            prompt = """
            Sen uzman bir hidrolik mühendisisin. Bu görseldeki bileşeni analiz et:
            - Elemanın adı ve tipi (Örn: Çift etkili silindir)
            - Fiziksel detaylar (Mafsallar, portlar, mil yapısı)
            - ISO 1219 teknik sembol açıklaması
            - Mühendislik notu (Bakım/Montaj tavsiyesi)
            Lütfen yanıtı profesyonel bir Türkçe ile ver.
            """
            
            with st.spinner(f'⚙️ {model_to_use} üzerinden analiz ediliyor...'):
                response = model.generate_content([prompt, image])
                
            st.success("✅ ANALİZ TAMAMLANDI")
            st.markdown("---")
            st.markdown(response.text)
            
        except Exception as e:
            st.error(f"❌ Kritik Hata: {str(e)}")
            st.info("İpucu: Eğer 403 hatası alırsanız, yeni bir API Key oluşturun.")
