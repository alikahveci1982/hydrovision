# 
# **URL:** https://raw.githubusercontent.com/alikahveci1982/hydrovision/main/streamlit_app.py
# 
# ---

import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
from functools import lru_cache
from typing import List
from pydantic import BaseModel, Field

# ─── SAYFA AYARLARI ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HydroVision Pro",
    page_icon="⚙️",
    layout="wide", # Tam genişlik
    initial_sidebar_state="expanded" # Sidebar varsayılan olarak açık
 )

st.markdown("""
<style>
    .main { background-color: #0e1117; color: white; }
    div.stButton > button {
        width: 100%;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        font-size: 16px;
        margin: 10px 0;
    }
    .stSuccess { background-color: #1e3a2f; }
    
    /* Streamlit'in kendi padding/margin'lerini sıfırla */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Üst menü/toolbar'ı gizle (mobil wrapper'da yardımcı olur) */
    header { visibility: hidden; }
    .stApp > header { display: none; }
    
    /* Footer'ı tamamen gizle */
    footer { visibility: hidden !important; }
    
    /* Tam ekran hissi için body margin sıfırla */
    body, html, [data-testid="stAppViewContainer"] {
        margin: 0 !important;
        padding: 0 !important;
        overflow-x: hidden !important;
    }
    
    /* Görseller ve içerikler tam genişlik */
    .stImage, .stPlotlyChart, .element-container {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Sekmeler için stil */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: nowrap;
        border-top-left-radius: 7px;
        border-top-right-radius: 7px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        padding-left: 20px;
        padding-right: 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ff4b4b;
        color: white;
    }
    .stTabs [aria-selected="false"] {
        background-color: #0e1117;
        color: #aaaaaa;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 HYDROVISION PRO")
st.caption("🔧 Arıza Tespit & Akıllı Satın Alma")

# ─── API ANAHTARI YÖNETİMİ ────────────────────────────────────────────────────
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "api_key_ok" not in st.session_state:
    st.session_state.api_key_ok = False

if not st.session_state.api_key_ok:
    api_key = st.text_input(
        "🔑 Gemini API Anahtarı",
        type="password",
        value=st.session_state.api_key,
        placeholder="AIza... şeklinde başlayan anahtarınızı girin",
        help="https://aistudio.google.com/app/apikey adresinden ücretsiz alabilirsiniz"
     )
    if api_key:
        st.session_state.api_key = api_key
        if st.button("🔑 API Anahtarını Onayla", type="primary"):
            genai.configure(api_key=api_key)
            st.session_state.api_key_ok = True
            st.rerun()
    else:
        st.info("👆 Başlamak için Gemini API anahtarınızı girin ve onaylayın.")
        st.stop()
else:
    genai.configure(api_key=st.session_state.api_key)
    if st.sidebar.button("🔄 API Anahtarını Değiştir"):
        st.session_state.api_key_ok = False
        st.rerun()

# ─── MODEL ÖNCELİK LİSTESİ ────────────────────────────────────────────────────
PREFERRED_MODELS = [
    "models/gemini-3.1-pro-preview",
    "models/gemini-2.5-pro",
    "models/gemini-2.5-flash",
    "models/gemini-2.5-flash-lite",
    "models/gemini-3-flash",
]

@lru_cache(maxsize=1)
def get_available_models() -> List[str]:
    try:
        models = genai.list_models()
        return [m.name for m in models if "generateContent" in m.supported_generation_methods and "gemini" in m.name.lower()]
    except Exception:
        return []

def get_best_model() -> str:
    available = get_available_models()
    for pref in PREFERRED_MODELS:
        if pref in available: return pref
    return available[0] if available else "models/gemini-pro"

# ─── STRUCTURED ÇIKTI MODELİ ──────────────────────────────────────────────────
class AnalysisResult(BaseModel):
    parça_adı: str
    malzeme_tanitimi: str
    teknik_ozellikler: List[str]
    arıza_analizi: List[str]
    çözüm_önerisi: List[str]
    bakım_tavsiyesi: List[str]
    sema_analizi: List[str]

def analyze_image(img: Image.Image) -> tuple[str, AnalysisResult]:
    model_name = get_best_model()
    model = genai.GenerativeModel(model_name)
    prompt = """
Sen uzman bir hidrolik sistemler mühendisisin. Gönderilen görsel bir hidrolik parça fotoğrafı veya bir hidrolik devre şeması olabilir. 
Eğer parça ise tanımla, arızaları analiz et. Eğer şema ise sembolleri ve devrenin çalışmasını açıkla.
Aşağıdaki tam JSON formatında cevap ver:
{
    "parça_adı": "...",
    "malzeme_tanitimi": "...",
    "teknik_ozellikler": ["...", "..."],
    "arıza_analizi": ["...", "..."],
    "çözüm_önerisi": ["...", "..."],
    "bakım_tavsiyesi": ["...", "..."],
    "sema_analizi": ["...", "..."]
}
"""
    response = model.generate_content(
        contents=[prompt, img],
        generation_config=genai.types.GenerationConfig(response_mime_type="application/json", temperature=0.1)
    )
    import json
    return model_name, AnalysisResult.model_validate(json.loads(response.text.strip()))

# ─── GÖRSEL YÜKLEME ───────────────────────────────────────────────────────────
st.markdown("### 📸 Görsel Yükleme / Çekme")
col1, col2 = st.columns(2)
with col1: camera_input = st.camera_input("📷 Kamerayı Aç")
with col2: uploaded_file = st.file_uploader("📂 Dosya Seç", type=["jpg", "jpeg", "png", "webp"])

final_file = camera_input or uploaded_file
if not final_file:
    st.info("Lütfen bir görsel yükleyin.")
    st.stop()

img = Image.open(final_file)
st.image(img, caption="Analiz Edilecek Görsel", use_container_width=True)

# ─── ANALİZ BUTONU ────────────────────────────────────────────────────────────
if st.button("🔍 ANALİZ ET VE PARÇA BUL", type="primary"):
    try:
        with st.status("⚙️ Analiz ediliyor...", expanded=True) as status:
            model_name, result = analyze_image(img)
            status.update(label="✅ Tamamlandı!", state="complete")

        st.subheader(f"🔧 Parça: **{result.parça_adı}**")
        t1, t2, t3, t4 = st.tabs(["Tanıtım", "Teknik", "Arıza & Çözüm", "Şema Analizi"])
        with t1: st.markdown(f"**Malzeme:** {result.malzeme_tanitimi}")
        with t2: 
            for i in result.teknik_ozellikler: st.markdown(f"• {i}")
        with t3:
            st.markdown("**Arızalar:**")
            for i in result.arıza_analizi: st.markdown(f"• {i}")
            st.markdown("**Çözümler:**")
            for i in result.çözüm_önerisi: st.markdown(f"• {i}")
        with t4:
            for i in result.sema_analizi: st.markdown(f"• {i}")

        query = urllib.parse.quote(f"Hidrolik {result.parça_adı} fiyatları")
        st.markdown(f'<a href="https://www.google.com/search?q={query}" target="_blank"><button style="width:100%; background:#4285F4; color:white; border:none; border-radius:10px; padding:12px; cursor:pointer;">🛒 Satın Alma Seçenekleri</button></a>', unsafe_allow_html=True )
    except Exception as e:
        st.error(f"Hata: {str(e)}")
