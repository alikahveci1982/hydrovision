import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
from typing import List, Dict, Any
from pydantic import BaseModel, field_validator

# ─── GENİŞLETİLMİŞ DİL DESTEĞİ (TR, EN, DE, ES) ──────────────────────────────
LANGUAGES = {
    "TR": {
        "caption": "Endüstriyel Arıza Analizi & Akıllı Sistem",
        "api_info": "Sistem Hazır. Görsel yükleyerek başlayın.",
        "upload_title": "### 📸 Analiz İçin Görsel Seçin",
        "camera_input": "📷 FOTOĞRAF ÇEK",
        "file_uploader": "🖼️ GALERİDEN YÜKLE",
        "analyze_button": "🔍 ANALİZİ BAŞLAT",
        "analyzing": "⚙️ Görüntü işleniyor...",
        "material_label": "**Yapı/Malzeme:** ",
        "purchase_button": "🛒 PARÇA FİYATLARINI ARAŞTIR",
        "purchase_query": "Hidrolik {} fiyatları",
        "system_prompt": "Sen kıdemli bir hidrolik mühendisisin. JSON formatında teknik cevap ver.",
        "user_prompt": "Görseli ISO 1219 standartlarına göre analiz et."
    },
    "EN": {
        "caption": "Industrial Fault Analysis & Smart System",
        "api_info": "System Ready. Start by uploading an image.",
        "upload_title": "### 📸 Select Image for Analysis",
        "camera_input": "📷 CAPTURE PHOTO",
        "file_uploader": "🖼️ UPLOAD FROM GALLERY",
        "analyze_button": "🔍 START ANALYSIS",
        "analyzing": "⚙️ Processing...",
        "material_label": "**Structure/Material:** ",
        "purchase_button": "🛒 SEARCH PART PRICES",
        "purchase_query": "Hydraulic {} price",
        "system_prompt": "You are a senior hydraulic engineer. Respond in JSON format.",
        "user_prompt": "Analyze the image based on ISO 1219 standards."
    },
    "DE": { # Almanca - Hidrolik sektöründe çok kritik
        "caption": "Industrielle Fehleranalyse & Intelligentes System",
        "api_info": "System bereit. Laden Sie ein Bild hoch.",
        "upload_title": "### 📸 Bild für Analyse auswählen",
        "camera_input": "📷 FOTO AUFNEHMEN",
        "file_uploader": "🖼️ AUS GALERIE HOCHLADEN",
        "analyze_button": "🔍 ANALYSE STARTEN",
        "analyzing": "⚙️ Verarbeitung läuft...",
        "material_label": "**Struktur/Material:** ",
        "purchase_button": "🛒 ERSATZTEILPREISE PRÜFEN",
        "purchase_query": "Hydraulik {} preis",
        "system_prompt": "Sie sind ein erfahrener Hydraulikingenieur. Antworten Sie im JSON-Format.",
        "user_prompt": "Analysieren Sie das Bild nach ISO 1219 Standards."
    },
    "ES": { # İspanyolca - Amerika ve İspanya pazarı için
        "caption": "Análisis de Fallas Industriales y Sistema Inteligente",
        "api_info": "Sistema listo. Sube una imagen para empezar.",
        "upload_title": "### 📸 Seleccionar imagen para análisis",
        "camera_input": "📷 TOMAR FOTO",
        "file_uploader": "🖼️ SUBIR DE GALERÍA",
        "analyze_button": "🔍 INICIAR ANÁLISIS",
        "analyzing": "⚙️ Procesando...",
        "material_label": "**Estructura/Material:** ",
        "purchase_button": "🛒 BUSCAR PRECIOS DE PIEZAS",
        "purchase_query": "Hidráulico {} precio",
        "system_prompt": "Eres un ingeniero hidráulico senior. Responde en formato JSON.",
        "user_prompt": "Analice la imagen según los estándares ISO 1219."
    }
}

# ─── SAYFA AYARLARI ───────────────────────────────────────────────────────────
st.set_page_config(page_title="HydroVision Pro", page_icon="⚙️", layout="wide", initial_sidebar_state="collapsed")

# ─── SECRETS VE API AYARI (KRİTİK) ───────────────────────────────────────────
if "api_key" not in st.session_state:
    # Önce Streamlit Cloud Secrets'dan oku
    st.session_state.api_key = st.secrets.get("GEMINI_API_KEY", "")

if st.session_state.api_key:
    genai.configure(api_key=st.session_state.api_key)

# ─── CSS (SADECE GEREKLİ DÜZELTMELER) ──────────────────────────────────────────
st.markdown("""
<style>
    :root { --accent-cyan: #00d4e8; --bg-base: #050e1a; }
    html, body, .stApp { background-color: var(--bg-base) !important; color: #7aa8cc !important; }
    h1 { text-align: center; color: var(--accent-cyan) !important; font-family: 'Rajdhani', sans-serif; }
    
    /* Sidebar Menü Butonu Düzeltmesi */
    [data-testid="stSidebarCollapsedControl"] {
        background: #112540 !important;
        border: 1px solid rgba(0,212,232,0.2) !important;
        color: var(--accent-cyan) !important;
    }
    [data-testid="stSidebarCollapsedControl"]::after { content: '☰'; font-size: 20px; position: absolute; left: 12px; }
    [data-testid="stSidebarCollapsedControl"] span { display: none; }
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")
    st.session_state.lang = st.selectbox("🌍 Language", list(LANGUAGES.keys()))
    L = LANGUAGES[st.session_state.lang]
    
    # Kullanıcı kendi anahtarını girmek isterse (Opsiyonel)
    user_key = st.text_input("🔑 Override API Key", type="password", help="Kendi anahtarınızı kullanmak için buraya yazın.")
    if user_key:
        st.session_state.api_key = user_key
        genai.configure(api_key=user_key)

# ─── ANA EKRAN ────────────────────────────────────────────────────────────────
st.markdown("<h1>⚙️ HYDROVISION PRO</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center;'>{L['caption']}</p>", unsafe_allow_html=True)

if not st.session_state.api_key:
    st.warning("⚠️ API Key bulunamadı. Lütfen ayarlardan girin.")
    st.stop()

# ─── ANALİZ MANTIĞI ───────────────────────────────────────────────────────────
class AnalysisResult(BaseModel):
    parça_adı: str
    malzeme_tanitimi: str
    arıza_analizi: List[str]
    çözüm_önerisi: List[str]

def analyze_image(img: Image.Image, lang: str) -> AnalysisResult:
    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=LANGUAGES[lang]["system_prompt"])
    prompt = f"{LANGUAGES[lang]['user_prompt']} JSON Output: {{\"parça_adı\":\"\",\"malzeme_tanitimi\":\"\",\"arıza_analizi\":[],\"çözüm_önerisi\":[]}}"
    response = model.generate_content([prompt, img], generation_config={"response_mime_type": "application/json"})
    return AnalysisResult.model_validate_json(response.text)

# ─── UI ELEMANLARI ────────────────────────────────────────────────────────────
st.markdown(L["upload_title"])
c1, c2 = st.columns(2)
with c1: cam = st.camera_input(L["camera_input"])
with c2: upload = st.file_uploader(L["file_uploader"], type=["jpg", "png"])

final_file = cam or upload
if final_file:
    img = Image.open(final_file)
    st.image(img, use_container_width=True)
    
    if st.button(L["analyze_button"], type="primary"):
        with st.spinner(L["analyzing"]):
            res = analyze_image(img, st.session_state.lang)
            st.success("✅ Done!")
            st.write(f"### {res.parça_adı}")
            st.write(f"{L['material_label']} {res.malzeme_tanitimi}")
            st.error(f"⚠️ {res.arıza_analizi[0]}")
            st.info(f"✅ {res.çözüm_önerisi[0]}")
