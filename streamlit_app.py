import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
from functools import lru_cache
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, field_validator
import json
import io

# ─── CONFIGURATION & LANGUAGES ───────────────────────────────────────────────
LANGUAGES = {
    "TR": {
        "title": "🤖 HYDROVISION PRO",
        "caption": "🔧 Endüstriyel Arıza Analizi & Akıllı Sistem",
        "api_key_label": "🔑 Gemini API Anahtarı",
        "api_key_help": "https://aistudio.google.com/app/apikey",
        "api_key_placeholder": "Anahtarınızı buraya yapıştırın...",
        "api_key_button": "🔑 Sisteme Bağlan",
        "api_key_info": "💡 Başlamak için lütfen API anahtarınızı girin.",
        "api_key_change": "🔄 Anahtarı Güncelle",
        "model_selection": "🤖 Yapay Zeka Modeli",
        "upload_title": "### 📸 Analiz İçin Görsel Seçin",
        "camera_input": "📷 FOTOĞRAF ÇEK",
        "file_uploader": "🖼️ GALERİDEN YÜKLE",
        "no_image_info": "Analiz için henüz bir görsel seçilmedi.",
        "analyze_button": "🔍 ANALİZİ BAŞLAT",
        "analyzing_status": "⚙️ Görüntü işleniyor ve analiz ediliyor...",
        "complete_status": "✅ Analiz Tamamlandı",
        "tabs": ["🏠 Özet", "📊 Teknik", "⚠️ Arıza & Çözüm", "📂 Şema"],
        "material_label": "**Yapı/Malzeme:** ",
        "faults_label": "Tespit Edilen Arızalar",
        "solutions_label": "Çözüm ve Bakım Önerileri",
        "purchase_button": "🛒 PARÇA FİYATLARINI ARAŞTIR",
        "purchase_query": "Hidrolik {} fiyatları",
        "error_label": "Sistem Hatası: {}",
        "system_prompt": "Sen kıdemli bir hidrolik mühendisisin. Teknik, net ve yapılandırılmış JSON formatında cevap verirsin.",
        "user_prompt": "Görseli ISO 1219 standartlarına göre analiz et. Profesyonel bir rapor hazırla."
    },
    "EN": {
        "title": "🤖 HYDROVISION PRO",
        "caption": "🔧 Industrial Fault Analysis & Smart System",
        "api_key_label": "🔑 Gemini API Key",
        "api_key_help": "https://aistudio.google.com/app/apikey",
        "api_key_placeholder": "Paste your key here...",
        "api_key_button": "🔑 Connect System",
        "api_key_info": "💡 Please enter your API key to start.",
        "api_key_change": "🔄 Update Key",
        "model_selection": "🤖 AI Model",
        "upload_title": "### 📸 Select Image for Analysis",
        "camera_input": "📷 CAPTURE PHOTO",
        "file_uploader": "🖼️ UPLOAD FROM GALLERY",
        "no_image_info": "No image selected for analysis.",
        "analyze_button": "🔍 START ANALYSIS",
        "analyzing_status": "⚙️ Processing and analyzing image...",
        "complete_status": "✅ Analysis Completed",
        "tabs": ["🏠 Summary", "📊 Technical", "⚠️ Fault & Solution", "📂 Schema"],
        "material_label": "**Structure/Material:** ",
        "faults_label": "Detected Faults",
        "solutions_label": "Solutions & Maintenance",
        "purchase_button": "🛒 SEARCH PART PRICES",
        "purchase_query": "Hydraulic {} price",
        "error_label": "System Error: {}",
        "system_prompt": "You are a senior hydraulic engineer. Provide technical, clear, and structured JSON responses.",
        "user_prompt": "Analyze the image based on ISO 1219 standards. Prepare a professional report."
    }
}

# ─── SAYFA AYARLARI ───────────────────────────────────────────────────────────
st.set_page_config(page_title="HydroVision Pro", page_icon="⚙️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Share+Tech+Mono&family=Exo+2:wght@300;400;600&display=swap');

:root {
    --bg-base: #050e1a;
    --bg-panel: #091624;
    --bg-card: #0d1f33;
    --bg-elevated: #112540;
    --accent-cyan: #00d4e8;
    --accent-blue: #0088cc;
    --accent-orange: #ff6b1a;
    --accent-green: #00e5a0;
    --text-primary: #e8f4ff;
    --text-secondary: #7aa8cc;
    --text-muted: #3d6080;
    --border: rgba(0,212,232,0.15);
    --glow-cyan: 0 0 20px rgba(0,212,232,0.3);
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-base) !important;
    background-image:
        linear-gradient(rgba(0,212,232,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,212,232,0.03) 1px, transparent 1px) !important;
    background-size: 40px 40px !important;
    font-family: 'Exo 2', sans-serif !important;
}

[data-testid="stHeader"] {
    background: rgba(5,14,26,0.9) !important;
    border-bottom: 1px solid var(--border);
}

section[data-testid="stSidebar"] {
    background-color: var(--bg-panel) !important;
    border-right: 1px solid var(--border) !important;
}

h1 {
    font-family: 'Rajdhani', sans-serif !important;
    letter-spacing: 3px !important;
    text-align: center;
    font-size: 2rem !important;
    background: linear-gradient(90deg, var(--accent-cyan), var(--text-primary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* ── SIDEBAR FIXES (MENÜ BUTONU DÜZELTMESİ) ── */
/* Menü kapalıyken solda duran butonu düzenle */
[data-testid="stSidebarCollapsedControl"] {
    background-color: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: 0 8px 8px 0 !important;
    color: var(--accent-cyan) !important;
    width: 45px !important;
    height: 45px !important;
    box-shadow: var(--glow-cyan) !important;
}

/* Yazı olarak çıkan "double_arrow_right" metnini tamamen gizle */
[data-testid="stSidebarCollapsedControl"] span {
    color: transparent !important;
    font-size: 0 !important;
}

/* Kendi ikonumuzu (☰) yerleştir */
[data-testid="stSidebarCollapsedControl"]::after {
    content: '☰';
    position: absolute;
    color: var(--accent-cyan);
    font-size: 22px;
    left: 12px;
}

/* Menü açıkken üstteki kapatma butonunu düzenle */
[data-testid="stSidebarCollapseButton"] button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--accent-cyan) !important;
}

/* Geri kalan standart UI elemanları */
[data-testid="stTextInput"] input {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
}

div.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)) !important;
    color: var(--bg-base) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 24px rgba(0,212,232,0.25) !important;
    transition: all 0.25s !important;
}

.info-card {
    background: var(--bg-card);
    padding: 20px;
    border-radius: 14px;
    border-left: 4px solid var(--accent-cyan);
    margin-bottom: 16px;
}

.fault-card {
    background: rgba(255,107,26,0.08);
    padding: 20px;
    border-radius: 14px;
    border-left: 4px solid var(--accent-orange);
    margin-bottom: 12px;
}

.solution-card {
    background: rgba(0,229,160,0.07);
    padding: 20px;
    border-radius: 14px;
    border-left: 4px solid var(--accent-green);
    margin-bottom: 12px;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-thumb { background: var(--accent-blue); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR & LOGIC ──────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "TR"

with st.sidebar:
    st.markdown("### ⚙️ Gemini Settings")
    if "api_key" not in st.session_state:
        try:
            st.session_state.api_key = st.secrets.get("GEMINI_API_KEY", "")
        except:
            st.session_state.api_key = ""

    api_key_input = st.text_input("🔑 API Key", type="password", value=st.session_state.api_key)
    if api_key_input:
        st.session_state.api_key = api_key_input
        genai.configure(api_key=api_key_input)
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            display_models = [m for m in available_models if 'flash' in m.lower() or 'pro' in m.lower()]
            selected_model = st.selectbox("Active AI Engine", display_models if display_models else available_models)
        except:
            selected_model = "gemini-1.5-flash"

# ─── MAIN UI ──────────────────────────────────────────────────────────────────
st.markdown("<h1>⚙️ HYDROVISION PRO</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center; font-size:1.1rem; margin-top:-15px; font-family: Share Tech Mono, monospace; letter-spacing:2px;'>🔧 {LANGUAGES[st.session_state.lang]['caption']}</p>", unsafe_allow_html=True)

col_l, col_r = st.columns([8, 2])
with col_r:
    st.session_state.lang = st.selectbox("", ["TR", "EN"], index=0 if st.session_state.lang == "TR" else 1, label_visibility="collapsed")
L = LANGUAGES[st.session_state.lang]

if not st.session_state.get("api_key"):
    st.info(L["api_key_info"])
    st.stop()

# ─── MODELS & DATA ────────────────────────────────────────────────────────────
class AnalysisResult(BaseModel):
    parça_adı: str
    malzeme_tanitimi: str
    teknik_ozellikler: List[str]
    arıza_analizi: List[str]
    çözüm_önerisi: List[str]
    bakım_tavsiyesi: List[str]
    sema_analizi: List[str]

    @field_validator('teknik_ozellikler', 'arıza_analizi', 'çözüm_önerisi', 'bakım_tavsiyesi', 'sema_analizi', mode='before')
    @classmethod
    def ensure_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v

def analyze_image(img: Image.Image, model_name: str, lang: str) -> AnalysisResult:
    L = LANGUAGES[lang]
    model = genai.GenerativeModel(model_name=model_name, system_instruction=L["system_prompt"])
    prompt = f"{L['user_prompt']}\nZORUNLU JSON FORMATI:\n{{\"parça_adı\": \"...\", \"malzeme_tanitimi\": \"...\", \"teknik_ozellikler\": [\"...\"], \"arıza_analizi\": [\"...\"], \"çözüm_önerisi\": [\"...\"], \"bakım_tavsiyesi\": [\"...\"], \"sema_analizi\": [\"...\"]}}"
    response = model.generate_content(
        contents=[prompt, img],
        generation_config=genai.types.GenerationConfig(response_mime_type="application/json", temperature=0.1)
    )
    return AnalysisResult.model_validate_json(response.text.strip())

# ─── UI ───────────────────────────────────────────────────────────────────────
st.markdown(L["upload_title"])
c1, c2 = st.columns(2)
with c1:
    cam = st.camera_input(L["camera_input"])
with c2:
    upload = st.file_uploader(L["file_uploader"], type=["jpg", "png", "webp"])

final_file = cam or upload
if final_file:
    img = Image.open(final_file)
    if max(img.size) > 1024:
        img.thumbnail((1024, 1024))
    st.image(img, use_container_width=True)

    if st.button(L["analyze_button"], type="primary"):
        try:
            with st.status(L["analyzing_status"]) as status:
                result = analyze_image(img, selected_model, st.session_state.lang)
                status.update(label=L["complete_status"], state="complete")

            st.markdown(f'<div class="info-card"><h2 style="color:var(--text-primary) !important; margin:0;">{result.parça_adı.upper()}</h2><p style="margin-top:5px;">{L["material_label"]}{result.malzeme_tanitimi}</p></div>', unsafe_allow_html=True)

            st.markdown("### 📍 Teknik Özet")
            for i in result.teknik_ozellikler:
                st.markdown(f"🔹 {i}")

            st.markdown('<div class="fault-card"><h4 style="color:var(--accent-orange) !important; margin-bottom:10px;">⚠️ Tespit Edilen Kritik Hatalar</h4>', unsafe_allow_html=True)
            for i in result.arıza_analizi:
                st.markdown(f"• {i}")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="solution-card"><h4 style="color:var(--accent-green) !important; margin-bottom:10px;">✅ Önerilen Aksiyon Planı</h4>', unsafe_allow_html=True)
            for i in result.çözüm_önerisi:
                st.markdown(f"• {i}")
            st.markdown(f"<br><b>🔧 Bakım:</b> {', '.join(result.bakım_tavsiyesi)}", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            if result.sema_analizi:
                st.markdown('<div class="info-card" style="border-left-color: var(--accent-cyan);"><h4 style="color:var(--accent-cyan) !important; margin-bottom:10px;">🔍 ISO 1219 Şema Analizi</h4>', unsafe_allow_html=True)
                for i in result.sema_analizi:
                    st.markdown(f"• {i}")
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("---")

            report_text = "HYDROVISION PRO ANALİZ RAPORU\n"
            report_text += "---------------------------\n"
            report_text += f"Parça: {result.parça_adı}\n"
            report_text += f"Malzeme: {result.malzeme_tanitimi}\n\n"
            report_text += "Teknik Özellikler:\n" + "\n".join([f"- {i}" for i in result.teknik_ozellikler]) + "\n\n"
            report_text += "Arıza Analizi:\n" + "\n".join([f"- {i}" for i in result.arıza_analizi]) + "\n\n"
            report_text += "Çözüm Önerileri:\n" + "\n".join([f"- {i}" for i in result.çözüm_önerisi]) + "\n\n"
            report_text += f"Bakım Tavsiyesi: {', '.join(result.bakım_tavsiyesi)}\n"

            st.download_button(
                label="📥 RAPORU İNDİR (TXT)",
                data=report_text,
                file_name=f"hydrovision_{result.parça_adı.lower().replace(' ', '_')}.txt",
                mime="text/plain"
            )

            whatsapp_msg = f"*HydroVision Pro Analiz Raporu*\n\n"
            whatsapp_msg += f"*Parça:* {result.parça_adı}\n"
            whatsapp_msg += f"*Arıza:* {result.arıza_analizi[0] if result.arıza_analizi else '-'}\n"
            whatsapp_msg += f"*Çözüm:* {result.çözüm_önerisi[0] if result.çözüm_önerisi else '-'}"
            wa_link = f"https://wa.me/?text={urllib.parse.quote(whatsapp_msg)}"
            st.markdown(f'<a href="{wa_link}" target="_blank" class="share-btn" style="display:block; width:100%; padding:16px; background:#25D366; color:white; text-align:center; border-radius:10px; text-decoration:none; font-weight:700;">📱 WHATSAPP İLE PAYLAŞ</a>', unsafe_allow_html=True)

            query = urllib.parse.quote(L["purchase_query"].format(result.parça_adı))
            st.markdown(f'<a href="https://www.google.com/search?q={query}" target="_blank" style="text-decoration:none;"><div style="width:100%; background:linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)); color:var(--bg-base); text-align:center; border-radius:10px; padding:16px; font-weight:700; margin-top:10px;"> {L["purchase_button"]} </div></a>', unsafe_allow_html=True)

        except Exception as e:
            st.error(L["error_label"].format(str(e)))
else:
    st.info(L["no_image_info"])
