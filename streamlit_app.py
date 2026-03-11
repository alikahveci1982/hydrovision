import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse

# UI Ayarları
st.set_page_config(page_title="HydroVision Pro", page_icon="⚙️")
st.markdown("""<style>.main { background-color: #0e1117; color: white; } div.stButton > button { width: 100%; height: 3em; background-color: #ff4b4b; color: white; font-weight: bold; border-radius: 10px; }</style>""", unsafe_allow_html=True)

st.title("🤖 HYDROVISION PRO")
st.caption("🔧 Arıza Tespit & Akıllı Satın Alma")

api_key = st.text_input("🔑 Gemini API Anahtarı", type="password")

t1, t2 = st.tabs(["📸 Fotoğraf Çek", "📂 Dosya Yükle"])
with t1: cam = st.camera_input("Kamerayı Aç")
with t2: file = st.file_uploader("Dosya Seç", type=['jpg', 'png', 'jpeg'])

final_img = cam if cam else file

if final_img and api_key:
    img = Image.open(final_img)
    st.image(img, use_container_width=True)

    if st.button("🔍 ANALİZ ET VE PARÇA BUL"):
        try:
            genai.configure(api_key=api_key)

            # Görsel destekleyen modelleri filtrele
            all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # Sadece görsel destekleyen Gemini modellerini filtrele
            vision_models = [m for m in all_models if 'gemini' in m.lower() and 'embedding' not in m.lower()]
            
            # Öncelik sırası — en güncel ve stabil modeller önce
            PREFERRED = [
                'models/gemini-2.0-flash',
                'models/gemini-2.0-flash-lite',
                'models/gemini-1.5-flash-latest',
                'models/gemini-1.5-flash',
                'models/gemini-1.5-pro-latest',
                'models/gemini-1.5-pro',
                'models/gemini-pro-vision',
            ]
            
            selected_model = None
            for pref in PREFERRED:
                if pref in vision_models:
                    selected_model = pref
                    break
            
            # Hiçbiri yoksa listedeki ilk modeli dene
            if not selected_model:
                selected_model = vision_models[0] if vision_models else None

            if not selected_model:
                st.error("❌ Uygun Gemini modeli bulunamadı. API anahtarınızı kontrol edin.")
                st.stop()

            st.info(f"🤖 Kullanılan model: `{selected_model}`")
            model = genai.GenerativeModel(selected_model)

            prompt = """
            Sen uzman bir hidrolik mühendisisin. Yanıtı şu formatta ver:
            PARÇA_ADI: [Yalın parça ismi]
            ---
            1. ARIZA ANALİZİ: [Olası nedenler]
            2. ÇÖZÜM: [Öneri]
            """

            with st.spinner(f'⚙️ Analiz yapılıyor...'):
                resp = model.generate_content([prompt, img])

            st.success("✅ ANALİZ TAMAMLANDI")
            st.write(resp.text)

            p_name = resp.text.split("---")[0].replace("PARÇA_ADI:", "").strip()
            q = urllib.parse.quote(f"Hidrolik {p_name}")
            st.markdown(f'<a href="https://www.google.com/search?q={q}+fiyatları" target="_blank" style="text-decoration:none;"><button style="width:100%; height:3em; background-color:#4285F4; color:white; border:none; border-radius:10px;">🛒 {p_name} Satın Alma Seçenekleri</button></a>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Hata: {str(e)}")
            st.info("💡 API anahtarınızın geçerli olduğunu ve Google AI Studio'dan alındığını kontrol edin: https://aistudio.google.com/app/apikey")
