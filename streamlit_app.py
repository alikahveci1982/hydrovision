import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
import re

# Sayfa Yapılandırması
st.set_page_config(page_title="HydroVision Pro", page_icon="⚙️", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    div.stButton > button:first-child {
        background-color: #ff4b4b; color: white; border-radius: 12px;
        height: 60px; width: 100%; font-size: 20px; font-weight: bold;
    }
    .result-card { 
        background-color: #161b22; padding: 20px; border-radius: 15px; 
        border: 1px solid #30363d; margin-top: 20px;
    }
    .buy-btn {
        display: block; padding: 15px; margin: 10px 0; border-radius: 10px;
        text-decoration: none; font-weight: bold; text-align: center; color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 HYDROVISION PRO")
st.caption("🔧 Arıza Tespit & Akıllı Satın Alma Terminali")

api_key = st.text_input("🔑 Gemini API Anahtarı", type="password")
uploaded_file = st.camera_input("Parçayı Fotoğrafla") # Sahada kullanım için kamera öncelikli

if uploaded_file and api_key:
    image = Image.open(uploaded_file)
    
    if st.button("🔍 ANALİZ ET VE PARÇA BUL"):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Satın alma hatasını çözen özel prompt formatı
            prompt = """
            Sen bir hidrolik mühendisisin. Yanıtı ŞU FORMATTA ver:
            PARÇA_ADI: [Buraya sadece parçanın en yalın ismini yaz, örn: Hidrolik Silindir]
            ---
            1. ARIZA ANALİZİ: [Arıza nedenleri]
            2. ÇÖZÜM: [Tamir önerisi]
            3. TEKNİK KOD: [Olası model kodu]
            """
            
            with st.spinner('⚙️ Mühendislik zekası devrede...'):
                response = model.generate_content([prompt, image])
                full_text = response.text
                
                # Parça ismini ayıran yazılım mantığı
                parts = full_text.split("---")
                item_name = parts[0].replace("PARÇA_ADI:", "").strip()
                analysis = parts[1] if len(parts) > 1 else full_text

            st.success(f"✅ Tespit Edilen: {item_name}")
            st.markdown(f'<div class="result-card">{analysis}</div>', unsafe_allow_html=True)
            
            # --- HATASIZ SATIN ALMA LİNKLERİ ---
            st.subheader("🛒 Doğru Yedek Parça Tedariği")
            clean_query = urllib.parse.quote(item_name)
            
            st.markdown(f"""
                <a href="https://www.google.com/search?q={clean_query}+fiyatları+satın+al" class="buy-btn" style="background-color: #4285F4;">🛒 {item_name} Fiyatlarını Gör</a>
                <a href="https://www.google.com/search?q={clean_query}+teknik+katalog+pdf" class="buy-btn" style="background-color: #28a745;">📄 Teknik Katalog ve Ölçüler</a>
                <a href="https://www.google.com/search?tbm=shop&q={clean_query}" class="buy-btn" style="background-color: #F4B400;">🛍️ Google Alışveriş Sonuçları</a>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Hata: {str(e)}")
