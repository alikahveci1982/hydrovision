import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
from typing import List
from pydantic import BaseModel

# ─── DİL VE TASARIM AYARLARI ────────────────────────────────────────────────
LANGUAGES = {
    "TR": {
        "title": "🤖 HYDROVISION PRO",
        "caption": "🔧 Endüstriyel Arıza Analizi & Akıllı Sistem",
        "analyze_button": "🔍 ANALİZİ BAŞLAT",
        "pdf_button": "📥 PDF RAPORU İNDİR",
        "system_prompt": "Sen kıdemli bir hidrolik mühendisisin. Yanıtlarını JSON formatında ver.",
        "user_prompt": "Görseldeki hidrolik komponenti ISO 1219 standartlarına göre analiz et."
    },
    "EN": {
        "title": "🤖 HYDROVISION PRO",
        "caption": "🔧 Industrial Fault Analysis",
        "analyze_button": "🔍 START ANALYSIS",
        "pdf_button": "📥 DOWNLOAD PDF REPORT",
        "system_prompt": "You are a senior hydraulic engineer. Respond in JSON format.",
        "user_prompt": "Analyze the hydraulic component in the image based on ISO 1219 standards."
    }
}

st.set_page_config(page_title="HydroVision Pro", layout="wide", initial_sidebar_state="collapsed")

# ─── API AYARI (TEMİZLEME EKLEDİM) ───────────────────────────────────────────
if "api_key" not in st.session_state:
    st.session_state.api_key = st.secrets.get("GEMINI_API_KEY", "").strip()

if st.session_state.api_key:
    genai.configure(api_key=st.session_state.api_key)

# ─── MODEL LİSTESİ (FALLBACK SİSTEMİ) ────────────────────────────────────────
def analyze_with_fallback(image, lang_data):
    # Google bazen 'models/' ön eki olmadan NotFound hatası verebiliyor
    models_to_try = [
        "models/gemini-1.5-flash", 
        "models/gemini-1.5-pro",
        "gemini-1.5-flash"
    ]
    
    last_err = None
    for m_name in models_to_try:
        try:
            model = genai.GenerativeModel(
                model_name=m_name, 
                system_instruction=lang_data["system_prompt"]
            )
            prompt = f"{lang_data['user_prompt']} Return JSON: {{'parca':'','hata':'','cozum':''}}"
            resp = model.generate_content([prompt, image], generation_config={"response_mime_type": "application/json"})
            if resp.text:
                return AnalysisRes.model_validate_json(resp.text)
        except Exception as e:
            last_err = e
            continue
    raise last_err

# ─── CSS TASARIMI ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    :root { --accent: #00d4e8; --bg: #050e1a; }
    html, body, .stApp { background-color: var(--bg) !important; color: #e8f4ff !important; }
    .info-card { background: #0d1f33; padding: 20px; border-radius: 12px; border-left: 5px solid var(--accent); margin-bottom: 15px; }
    div.stButton > button { width: 100%; background: linear-gradient(135deg, var(--accent), #0088cc) !important; color: #050e1a !important; font-weight: 700; border: none; padding: 15px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ─── UI ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ CONFIG")
    lang_key = st.selectbox("Language", list(LANGUAGES.keys()))
    L = LANGUAGES[lang_key]

st.markdown(f"<h1>{L['title']}</h1>", unsafe_allow_html=True)

class AnalysisRes(BaseModel):
    parca: str
    hata: str
    cozum: str

upload = st.file_uploader("📸 Görsel Yükleyin", type=["jpg", "png"])
if upload:
    img = Image.open(upload)
    st.image(img, use_container_width=True)
    
    if st.button(L["analyze_button"]):
        with st.status("⚙️ Teknik Analiz Yapılıyor...") as s:
            try:
                res = analyze_with_fallback(img, L)
                s.update(label="✅ Analiz Başarılı!", state="complete")
                
                st.markdown(f'<div class="info-card"><h3>📍 {res.parca}</h3><p><b>Hata:</b> {res.hata}</p><p><b>Çözüm:</b> {res.cozum}</p></div>', unsafe_allow_html=True)
            except Exception as e:
                s.update(label="❌ Hata Oluştu!", state="error")
                st.error(f"Sistem hatası: {str(e)}")
