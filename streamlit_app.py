import streamlit as st
from groq import Groq
import base64
from PIL import Image
import io

st.set_page_config(page_title="HydroVision AI Pro", page_icon="🤖")

st.title("🤖 HYDROVISION AI PRO")
st.write("Mühendislik Terminali · ISO 1219 · Llama 3.2 Vision")

# API Anahtarı Girişi
api_key = st.text_input("Groq API Anahtarını Girin", type="password")

# Dosya Yükleme veya Kamera
source = st.radio("Görsel Kaynağı Seçin:", ("Dosya Yükle", "Kamera Kullan"))
if source == "Dosya Yükle":
    uploaded_file = st.file_uploader("Şema veya Parça Görseli seç...", type=['jpg', 'png', 'jpeg'])
else:
    uploaded_file = st.camera_input("Fotoğraf Çek")

if uploaded_file is not None and api_key:
    image = Image.open(uploaded_file)
    st.image(image, caption='Analiz Edilecek Görsel', use_column_width=True)
    
    if st.button("ANALİZ ET"):
        client = Groq(api_key=api_key)
        
        # Görseli hazırla
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        try:
            completion = client.chat.completions.create(
                model="llama-3.2-90b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Sen uzman bir hidrolik mühendisisin. Bu görseldeki ISO 1219 sembollerini veya hidrolik parçayı detaylıca analiz et. Marka, model ve teknik fonksiyon belirt."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                temperature: 0.1
            )
            st.success("✅ ANALİZ TAMAMLANDI")
            st.markdown(completion.choices[0].message.content)
        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")
