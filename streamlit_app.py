import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# Sayfa Yapılandırması
st.set_page_config(page_title="HydroVision AI Pro", page_icon="🤖", layout="wide")

st.title("🤖 HYDROVISION AI PRO")
st.subheader("Mühendislik Terminali · ISO 1219 · Gemini 1.5")

# API Anahtarı Girişi
api_key = st.text_input("Google Gemini API Anahtarını Girin", type="password", help="API anahtarınızı Google AI Studio'dan alabilirsiniz.")

# Görsel Kaynağı Seçimi
source = st.radio("Görsel Kaynağı:", ("Dosya Yükle", "Kamera Kullan"), horizontal=True)

if source == "Dosya Yükle":
    uploaded_file = st.file_uploader("Hidrolik şema veya parça görseli seçin...", type=['jpg', 'png', 'jpeg'])
else:
    uploaded_file = st.camera_input("Parçanın fotoğrafını çekin")

if uploaded_file is not None:
    # Görseli ekranda göster
    image = Image.open(uploaded_file)
    st.image(image, caption='Analiz Edilecek Görsel', use_container_width=True)
    
    if st.button("🔍 ANALİZ ET"):
        if not api_key:
            st.error("Lütfen önce geçerli bir API anahtarı girin!")
        else:
            try:
                # API Yapılandırması
                genai.configure(api_key=api_key)
                
                # Test edilmiş en stabil model tanımlaması
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Mühendislik Odaklı Prompt
                prompt = """
                Sen kıdemli bir hidrolik mühendisisin. Bu görseli teknik bir gözle analiz et:
                1. Bileşen Tanımı: Bu tam olarak hangi hidrolik elemandır? (Örn: Çift etkili silindir, emniyet valfi vb.)
                2. Teknik Özellikler: Görseldeki port girişleri, bağlantı tipleri (mafsal, flanş vb.) ve mil yapısı hakkında ne söyleyebilirsin?
                3. ISO 1219 Karşılığı: Bu elemanın devre şemasındaki sembolik gösterimini teknik olarak tarif et.
                4. Bakım Notu: Bu parçanın montajı veya işletilmesi sırasında dikkat edilmesi gereken kritik bir nokta belirt.
                
                Yanıtını tamamen Türkçe ve profesyonel bir mühendislik diliyle ver.
                """
                
                with st.spinner('⚙️ Mühendislik verisi işleniyor, lütfen bekleyin...'):
                    # Analiz süreci
                    response = model.generate_content([prompt, image])
                    
                st.success("✅ ANALİZ TAMAMLANDI")
                st.markdown("---")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"❌ Bir teknik hata oluştu: {str(e)}")
                if "404" in str(e):
                    st.warning("Model isminde bir uyumsuzluk var. Lütfen API anahtarınızın aktif olduğundan emin olun.")
