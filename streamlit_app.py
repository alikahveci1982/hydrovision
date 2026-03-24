import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import urllib.parse
from typing import List
from pydantic import BaseModel

# ─── CONFIGURATION & LANGUAGES ───────────────────────────────────────────────
LANGUAGES = {
    "TR": {
        "title": "🤖 HYDROVISION PRO",
        "caption": "🔧 Endüstriyel Arıza Analizi & Akıllı Sistem",
        "upload_title": "### 📸 Analiz İçin Görsel Seçin",
        "analyze_button": "🔍 ANALİZİ BAŞLAT",
        "pdf_button": "📥 PDF RAPORU İNDİR",
        "fault_title": "⚠️ Tespit Edilen Kritik Hatalar",
        "solution_title": "✅ Önerilen Aksiyon Planı",
        "system_prompt": "Sen kıdemli bir hidrolik mühendisisin. JSON formatında teknik cevap ver.",
        "user_prompt": "Görseli ISO 1219 standartlarına göre analiz et."
    },
    "EN": {
        "title": "🤖 HYDROVISION PRO",
        "caption": "🔧 Industrial Fault Analysis & Smart System",
        "upload_title": "### 📸 Select Image for Analysis",
        "analyze_button": "🔍 START ANALYSIS",
        "pdf_button": "📥 DOWNLOAD PDF REPORT",
        "fault_title": "⚠️ Detected Critical Faults",
        "solution_title": "✅ Recommended Action Plan",
        "system_prompt": "You are a senior hydraulic engineer. Respond in JSON format.",
        "user_prompt": "Analyze the image based on ISO 1219 standards."
    },
    "DE": {
        "title": "🤖 HYDROVISION PRO",
        "caption": "🔧 Industrielle Fehleranalyse & Intelligentes System",
        "upload_title": "### 📸 Bild für Analyse auswählen",
        "analyze_button": "🔍 ANALYSE STARTEN",
        "pdf_button": "📥 PDF-BERICHT HERUNTERLADEN",
        "fault_title": "⚠️ Erkannte kritische Fehler",
        "solution_title": "✅ Empfohlener Aktionsplan",
        "system_prompt": "Sie sind ein erfahrener Hydraulikingenieur. Antworten Sie im JSON-Format.",
        "user_prompt": "Analysieren Sie das Bild nach ISO 1219 Standards."
    },
    "ES": {
        "title": "🤖 HYDROVISION PRO",
        "caption": "🔧 Análisis de Fallas Industriales",
        "upload_title": "### 📸 Seleccionar imagen para análisis",
        "analyze_button": "🔍 INICIAR ANÁLISIS",
        "pdf_button": "📥 DESCARGAR INFORME PDF",
        "fault_title": "⚠️ Fallos Críticos Detectados",
        "solution_title": "✅ Plan de Acción Recomendado",
        "system_prompt": "Eres un ingeniero hidráulico senior. Responde en formato JSON.",
        "user_prompt": "Analice la imagen según los estándares ISO 1219."
    }
}

# ─── SAYFA AYARLARI ───────────────────────────────────────────────────────────
st.set_page_config(page_title="HydroVision Pro", page_icon="⚙️", layout="wide", initial_sidebar_state="collapsed")

# ─── SECRETS VE API ───────────────────────────────────────────────────────────
if "api_key" not in st.session_state:
    st.session_state.api_key = st.secrets.get("GEMINI_API_KEY", "")

if st.session_state.api_key:
    genai.configure(api_key=st.session_state.api_key)

# ─── PDF OLUŞTURUCU ───────────────────────────────────────────────────────────
def create_pdf(res, lang_code):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="HYDROVISION PRO - TECHNICAL REPORT", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt=f"Component: {res.parca}", ln=True)
    pdf.ln(5)
    pdf.set_text_color(255, 0, 0)
    pdf.cell(200, 10, txt="Detected Faults:", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 10, txt=res.hata)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0, 128, 0)
    pdf.cell(200, 10, txt="Recommended Solutions:", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 10, txt=res.cozum)
    return pdf.output(dest='S').encode('latin-1')

# ─── GÖRSEL CSS (TASARIMI GERİ GETİRİYORUZ) ───────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=Exo+2:wght@400;600&display=swap');

:root {
    --bg-base: #050e1a;
    --accent-cyan: #00d4e8;
    --border: rgba(0,212,232,0.15);
    --glow: 0 0 15px rgba(0,212,232,0.2);
}

html, body, .stApp {
    background-color: var(--bg-base) !important;
    background-image: linear-gradient(rgba(0,212,232,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,232,0.02) 1px, transparent 1px) !important;
    background-size: 30px 30px !important;
    font-family: 'Exo 2', sans-serif !important;
}

h1 { font-family: 'Rajdhani', sans-serif !important; color: var(--accent-cyan) !important; text-align: center; letter-spacing: 3px; }

.info-card { background: #0d1f33; padding: 20px; border-radius: 12px; border-left: 5px solid var(--accent-cyan); margin-bottom: 15px; box-shadow: var(--glow); }
.fault-card { background: rgba(255,107,26,0.05); padding: 20px; border-radius: 12px; border-left: 5px solid #ff6b1a; border: 1px solid rgba(255,107,26,0.2); margin-bottom: 12px; }
.sol-card { background: rgba(0,229,160,0.05); padding: 20px; border-radius: 12px; border-left: 5px solid #00e5a0; border: 1px solid rgba(0,229,160,0.2); margin-bottom: 12px; }

div.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, var(--accent-cyan), #0088cc) !important;
    color: #050e1a !important;
    font-weight: 700 !important;
    border: none !important;
    padding: 15px !important;
    border-radius: 8px !important;
}

/* Sidebar Buton Fix */
[data-testid="stSidebarCollapsedControl"] { background: #112540 !important; border-radius: 0 8px 8px 0 !important; color: var(--accent-cyan) !important; }
[data-testid="stSidebarCollapsedControl"]::after { content: '☰'; font-size: 20px; position: absolute; left: 12px; }
[data-testid="stSidebarCollapsedControl"] span { display: none; }
</style>
""", unsafe_allow_html=True)

# ─── UI ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ CONFIG")
    lang_key = st.selectbox("Language", list(LANGUAGES.keys()))
    L = LANGUAGES[lang_key]
    user_api = st.text_input("Override API Key", type="password")
    if user_api: 
        genai.configure(api_key=user_api)
        st.session_state.api_key = user_api

st.markdown(f"<h1>{L['title']}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center; color:#7aa8cc;'>{L['caption']}</p>", unsafe_allow_html=True)

if not st.session_state.api_key:
    st.info("💡 Lütfen Secrets kısmına API anahtarınızı ekleyin veya ayarlardan girin.")
    st.stop()

class AnalysisRes(BaseModel):
    parca: str
    hata: str
    cozum: str

# 📸 GÖRSEL YÜKLEME
st.markdown(L["upload_title"])
cam = st.camera_input("Camera")
file = st.file_uploader("Gallery", type=["jpg", "png"])
final = cam or file

if final:
    img = Image.open(final)
    st.image(img, use_container_width=True)
    
    if st.button(L["analyze_button"]):
        with st.status("⚙️ Analyzing...") as s:
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=L["system_prompt"])
            prompt = f"{L['user_prompt']} Return JSON: {{'parca':'','hata':'','cozum':''}}"
            resp = model.generate_content([prompt, img], generation_config={"response_mime_type": "application/json"})
            res = AnalysisRes.model_validate_json(resp.text)
            s.update(label="✅ Complete!", state="complete")

        st.markdown(f'<div class="info-card"><h3>📍 {res.parca}</h3></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="fault-card"><h4>{L["fault_title"]}</h4><p>{res.hata}</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="sol-card"><h4>{L["solution_title"]}</h4><p>{res.cozum}</p></div>', unsafe_allow_html=True)
        
        # PDF İNDİRME
        pdf_data = create_pdf(res, lang_key)
        st.download_button(L["pdf_button"], data=pdf_data, file_name=f"Report_{res.parca}.pdf", mime="application/pdf")
