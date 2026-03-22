import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
from functools import lru_cache
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import io

# ─── CONFIGURATION & LANGUAGES ───────────────────────────────────────────────
LANGUAGES = {
    "TR": {
        "title": "🤖 HYDROVISION PRO",
        "caption": "🔧 Saha Tipi Arıza Tespit & Akıllı Satın Alma",
        "api_key_label": "🔑 Gemini API Anahtarı",
        "api_key_help": "https://aistudio.google.com/app/apikey adresinden ücretsiz alabilirsiniz",
        "api_key_placeholder": "AIza... şeklinde başlayan anahtarınızı girin",
        "api_key_button": "🔑 Onayla",
        "api_key_info": "👆 Başlamak için API anahtarınızı girin.",
        "api_key_change": "🔄 API Anahtarını Değiştir",
        "model_selection": "🤖 Model Seçimi",
        "model_fast": "Hızlı (Flash 1.5)",
        "model_deep": "Derin (Pro 1.5)",
        "upload_title": "### 📸 Görsel Yükleme / Çekme",
        "camera_input": "📷 FOTOĞRAF ÇEK",
        "file_uploader": "🖼️ GALERİDEN SEÇ",
        "no_image_info": "Lütfen bir görsel yükleyin.",
        "analyze_button": "🔍 ANALİZ ET VE PARÇA BUL",
        "analyzing_status": "⚙️ Analiz ediliyor...",
        "complete_status": "✅ Tamamlandı!",
        "part_label": "🔧 Parça: **{}**",
        "tabs": ["Tanıtım", "Teknik", "Arıza & Çözüm", "Şema Analizi"],
        "material_label": "**Malzeme:** ",
        "faults_label": "Arızalar",
        "solutions_label": "Çözümler & Bakım",
        "purchase_button": "🛒 FİYATLARI ARA",
        "purchase_query": "Hidrolik {} fiyatları",
        "error_label": "Hata: {}",
        "prompt_role": "Sen uzman bir hidrolik sistemler mühendisisin.",
        "prompt_instruction": "Gönderilen görsel bir hidrolik parça fotoğrafı veya bir hidrolik devre şeması olabilir. Eğer parça ise tanımla, arızaları analiz et. Eğer şema ise sembolleri ve devrenin çalışmasını açıkla. Aşağıdaki tam JSON formatında cevap ver:"
    },
    "EN": {
        "title": "🤖 HYDROVISION PRO",
        "caption": "🔧 Field-Ready Fault Diagnosis & Smart Purchasing",
        "api_key_label": "🔑 Gemini API Key",
        "api_key_help": "Get it for free at https://aistudio.google.com/app/apikey",
        "api_key_placeholder": "Enter your key starting with AIza...",
        "api_key_button": "🔑 Confirm",
        "api_key_info": "👆 Please enter your API key to start.",
        "api_key_change": "🔄 Change API Key",
        "model_selection": "🤖 Model Selection",
        "model_fast": "Fast (Flash 1.5)",
        "model_deep": "Deep (Pro 1.5)",
        "upload_title": "### 📸 Upload / Capture Image",
        "camera_input": "📷 CAPTURE PHOTO",
        "file_uploader": "🖼️ CHOOSE FROM GALLERY",
        "no_image_info": "Please upload an image.",
        "analyze_button": "🔍 ANALYZE & FIND PART",
        "analyzing_status": "⚙️ Analyzing...",
        "complete_status": "✅ Completed!",
        "part_label": "🔧 Part: **{}**",
        "tabs": ["Introduction", "Technical", "Fault & Solution", "Schema Analysis"],
        "material_label": "**Material:** ",
        "faults_label": "Faults",
        "solutions_label": "Solutions & Maintenance",
        "purchase_button": "🛒 SEARCH PRICES",
        "purchase_query": "Hydraulic {} price",
        "error_label": "Error: {}",
        "prompt_role": "You are an expert hydraulic systems engineer.",
        "prompt_instruction": "The image sent can be a hydraulic part photo or a hydraulic circuit diagram. If it is a part, identify it and analyze faults. If it is a diagram, explain the symbols and the operation of the circuit. Respond in the following complete JSON format:"
    }
}

# ─── SAYFA AYARLARI ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HydroVision Pro",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Field-Ready UI (Big Buttons, Dark Mode)
st.markdown("""
<style>
    /* Global Styles */
    .main { background-color: #0e1117; color: white; }
    
    /* Force Wide Layout on Mobile */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    
    /* Huge Buttons for Field Mode */
    div.stButton > button {
        width: 100%;
        min-height: 4.5em;
        background-color: #ff4b4b;
        color: white !important;
        font-weight: bold;
        border-radius: 15px;
        font-size: 1.2rem;
        margin: 10px 0;
        border: none;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3);
    }
    div.stButton > button:hover {
        background-color: #d33;
        transform: translateY(-2px);
    }
    
    /* Card-like Analysis Sections */
    .info-card {
        background-color: #1e2129;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        border-left: 5px solid #ff4b4b;
    }
    .fault-card {
        background-color: #2d1a1a;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        border-left: 5px solid #ff4b4b;
    }
    .solution-card {
        background-color: #1a2d1a;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        border-left: 5px solid #4CAF50;
    }

    header { visibility: hidden; }
    footer { visibility: hidden !important; }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR & LANGUAGE SELECTION ──────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "TR"

with st.sidebar:
    st.session_state.lang = st.selectbox("🌐 Language / Dil", ["TR", "EN"], index=0 if st.session_state.lang == "TR" else 1)
    L = LANGUAGES[st.session_state.lang]
    
    st.title("⚙️ Settings")
    
    if "api_key" not in st.session_state:
        try:
            st.session_state.api_key = st.secrets.get("GEMINI_API_KEY", "")
        except:
            st.session_state.api_key = ""
    
    if "api_key_ok" not in st.session_state:
        st.session_state.api_key_ok = bool(st.session_state.api_key)

    api_key_input = st.text_input(
        L["api_key_label"], type="password",
        value=st.session_state.api_key,
        placeholder=L["api_key_placeholder"]
    )
    
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        st.session_state.api_key_ok = False

    if not st.session_state.api_key_ok and api_key_input:
        if st.button(L["api_key_button"]):
            st.session_state.api_key_ok = True
            st.rerun()
            
    if st.session_state.api_key_ok:
        st.success("API Key OK ✅")
        if st.button(L["api_key_change"]):
            st.session_state.api_key_ok = False
            st.rerun()

    st.divider()
    model_opt = st.radio(L["model_selection"], [L["model_fast"], L["model_deep"]], index=0)
    # Corrected Model Names
    PREFERRED_MODEL = "gemini-1.5-pro" if model_opt == L["model_deep"] else "gemini-1.5-flash"

# Main Page Header
st.title(L["title"])
st.caption(L["caption"])

if not st.session_state.api_key_ok:
    st.warning(L["api_key_info"])
    st.stop()

genai.configure(api_key=st.session_state.api_key)

# ─── MODELS & IMAGE PROCESSING ────────────────────────────────────────────────
class AnalysisResult(BaseModel):
    parça_adı: str
    malzeme_tanitimi: str
    teknik_ozellikler: List[str]
    arıza_analizi: List[str]
    çözüm_önerisi: List[str]
    bakım_tavsiyesi: List[str]
    sema_analizi: List[str]

def compress_image(image: Image.Image, max_size: int = 1024) -> Image.Image:
    if max(image.size) > max_size:
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    return image

def analyze_image(img: Image.Image, lang: str) -> AnalysisResult:
    L = LANGUAGES[lang]
    
    # Denenecek model isimleri (Öncelik sırasına göre)
    trial_models = [
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
        "gemini-1.5-pro-latest",
        "gemini-1.5-pro",
        "gemini-pro-vision"
    ]
    
    last_error = ""
    for model_name in trial_models:
        try:
            model = genai.GenerativeModel(model_name)
            prompt = f"""
{L['prompt_role']}
{L['prompt_instruction']}
{{
    "parça_adı": "...",
    "malzeme_tanitimi": "...",
    "teknik_ozellikler": ["...", "..."],
    "arıza_analizi": ["...", "..."],
    "çözüm_önerisi": ["...", "..."],
    "bakım_tavsiyesi": ["...", "..."],
    "sema_analizi": ["...", "..."]
}}
IMPORTANT: Respond ONLY with valid JSON.
"""
            response = model.generate_content(
                contents=[prompt, img],
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json", 
                    temperature=0.1
                )
            )
            raw_text = response.text.strip()
            return AnalysisResult.model_validate_json(raw_text)
        except Exception as e:
            last_error = str(e)
            if "404" in last_error or "not found" in last_error.lower():
                continue # Diğer modeli dene
            else:
                raise e # 404 dışındaki hataları (örn: Kota) fırlat
                
    raise Exception(f"Hiçbir model (Flash/Pro) yanıt vermedi. Son hata: {last_error}")

# ─── SIDEBAR DIAGNOSTICS ─────────────────────────────────────────────────────
with st.sidebar:
    st.divider()
    if st.checkbox("🔍 Sistem Tanılama (Diagnostics)"):
        st.write("### Mevcut Modelleriniz:")
        try:
            available_models = [m.name for m in genai.list_models()]
            for m in available_models:
                st.code(m)
        except Exception as e:
            st.error(f"Modeller listelenemedi: {e}")

# ─── VISUAL UPLOAD (FIELD MODE LAYOUT) ─────────────────────────────────────────
st.markdown(L["upload_title"])

# Huge Field Buttons
camera_input = st.camera_input(L["camera_input"])
uploaded_file = st.file_uploader(L["file_uploader"], type=["jpg", "jpeg", "png", "webp"])

final_file = camera_input or uploaded_file
if not final_file:
    st.info(L["no_image_info"])
    st.stop()

optimized_img = compress_image(Image.open(final_file))
st.image(optimized_img, caption="Analyzed View", width='stretch')

# ─── ANALYSIS & RESULTS ────────────────────────────────────────────────────────
if st.button(L["analyze_button"], type="primary"):
    try:
        with st.status(L["analyzing_status"], expanded=True) as status:
            result = analyze_image(optimized_img, st.session_state.lang)
            status.update(label=L["complete_status"], state="complete")

        # Result Cards
        st.markdown(f"""
            <div class="info-card">
                <h2 style='margin:0;'>{result.parça_adı.upper()}</h2>
                <p style='margin:5px 0 0 0; opacity:0.8;'>{L['material_label']}{result.malzeme_tanitimi}</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📊 Teknik Özellikler", expanded=True):
            for i in result.teknik_ozellikler: st.markdown(f"• {i}")
        
        st.markdown(f"<div class='fault-card'><h3>⚠️ {L['faults_label']}</h3>", unsafe_allow_html=True)
        for i in result.arıza_analizi: st.markdown(f"• {i}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown(f"<div class='solution-card'><h3>✅ {L['solutions_label']}</h3>", unsafe_allow_html=True)
        for i in result.çözüm_önerisi: st.markdown(f"• {i}")
        st.divider()
        st.markdown("**🛠️ Bakım Tavsiyesi:**")
        for i in result.bakım_tavsiyesi: st.markdown(f"• {i}")
        st.markdown("</div>", unsafe_allow_html=True)

        # Purchasing Button
        query_encoded = urllib.parse.quote(L["purchase_query"].format(result.parça_adı))
        search_url = f"https://www.google.com/search?q={query_encoded}"
        st.markdown(f"""
            <a href="{search_url}" target="_blank" style="text-decoration: none;">
                <div style="width:100%; background:#4285F4; color:white; text-align:center; border-radius:15px; padding:20px; font-weight: bold; font-size: 1.2rem; margin-top: 10px; box-shadow: 0 4px 15px rgba(66, 133, 244, 0.3);">
                    {L['purchase_button']}
                </div>
            </a>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(L["error_label"].format(str(e)))
