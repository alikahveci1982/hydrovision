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
@import url('https://fonts.googleapis.com/icon?family=Material+Icons');

:root {
    --bg-base: #0a1728;
    --bg-panel: #13253d;
    --bg-card: #1d3755;
    --bg-elevated: #28466f;
    --accent-cyan: #00e0f5;
    --accent-blue: #0099e6;
    --accent-orange: #ff7c2b;
    --accent-green: #00f2a8;
    --text-primary: #f1f9ff;
    --text-secondary: #89b9e0;
    --text-muted: #4a739f;
    --border: rgba(0,224,245,0.18);
    --glow-cyan: 0 0 28px rgba(0,224,245,0.4);
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-base) !important;
    background-image:
        linear-gradient(rgba(0,224,245,0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,224,245,0.035) 1px, transparent 1px) !important;
    background-size: 40px 40px !important;
    font-family: 'Exo 2', sans-serif !important;
}

[data-testid="stHeader"] {
    background: rgba(10,23,40,0.95) !important;
    border-bottom: 1px solid var(--border);
}

.main .block-container {
    background: transparent !important;
    padding-top: 2rem;
    max-width: 1100px;
}

section[data-testid="stSidebar"] {
    background-color: var(--bg-panel) !important;
    border-right: 1px solid var(--border) !important;
}

h1, h2, h3 {
    color: var(--text-primary) !important;
    font-family: 'Rajdhani', sans-serif !important;
    letter-spacing: 3px !important;
    text-align: center;
}
h1 {
    font-size: 2rem !important;
    background: linear-gradient(90deg, var(--accent-cyan), var(--text-primary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
p, span, label, div, .stMarkdown {
    color: var(--text-secondary) !important;
    font-family: 'Exo 2', sans-serif !important;
}

[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 13px !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: var(--accent-cyan) !important;
    box-shadow: var(--glow-cyan) !important;
}

div.stButton > button {
    width: 100%;
    min-height: 56px !important;
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)) !important;
    color: var(--bg-base) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    letter-spacing: 3px !important;
    text-transform: uppercase !important;
    border: none !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 24px rgba(0,224,245,0.3) !important;
    transition: all 0.25s !important;
    margin-bottom: 8px;
}
div.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 10px 35px rgba(0,224,245,0.45) !important;
}

[data-testid="stCameraInput"] button {
    background: linear-gradient(135deg, var(--accent-orange), #e06b00) !important;
    color: white !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: none !important;
}

[data-testid="stFileUploader"] {
    background: var(--bg-card) !important;
    border: 2px dashed var(--border) !important;
    border-radius: 16px !important;
    padding: 14px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent-cyan) !important;
    box-shadow: var(--glow-cyan) !important;
}

[data-testid="stCameraInput"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    overflow: hidden !important;
}

.info-card {
    background: var(--bg-card);
    padding: 22px 26px;
    border-radius: 16px;
    margin-bottom: 18px;
    border-left: 5px solid var(--accent-cyan);
    box-shadow: 0 6px 20px rgba(0,0,0,0.35);
}
.fault-card {
    background: rgba(255,124,43,0.09);
    padding: 22px 26px;
    border-radius: 16px;
    border: 1px solid rgba(255,124,43,0.28);
    border-left: 5px solid var(--accent-orange);
    margin-bottom: 14px;
}
.solution-card {
    background: rgba(0,242,168,0.08);
    padding: 22px 26px;
    border-radius: 16px;
    border: 1px solid rgba(0,242,168,0.25);
    border-left: 5px solid var(--accent-green);
    margin-bottom: 14px;
}

[data-testid="stStatusWidget"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}

[data-testid="stAlert"] {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text-secondary) !important;
}

[data-testid="stDownloadButton"] button {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    color: var(--accent-cyan) !important;
    font-family: 'Share Tech Mono', monospace !important;
    letter-spacing: 1px !important;
    border-radius: 10px !important;
}
[data-testid="stDownloadButton"] button:hover {
    border-color: var(--accent-cyan) !important;
    box-shadow: var(--glow-cyan) !important;
}

.share-btn {
    display: block;
    width: 100%;
    padding: 16px;
    background: #25D366 !important;
    color: white !important;
    text-align: center;
    border-radius: 12px;
    font-family: 'Rajdhani', sans-serif;
    font-weight: 700;
    font-size: 15px;
    letter-spacing: 2px;
    text-decoration: none;
    margin-top: 12px;
    box-shadow: 0 4px 20px rgba(37,211,102,0.3);
}

/* ── SIDEBAR COLLAPSE BUTTON İKON DÜZELTMESİ ── */
[data-testid="collapsedControl"],
button[kind="header"],
[data-testid="stSidebarCollapsedControl"] {
    font-family: 'Material Icons' !important;
    font-size: 0 !important;
}
[data-testid="collapsedControl"] span,
[data-testid="stSidebarCollapsedControl"] span {
    font-family: 'Material Icons' !important;
    font-size: 24px !important;
    font-style: normal !important;
    letter-spacing: normal !important;
}
/* Yazı olarak çıkan ikon metnini gizle, ok karakteri göster */
button[data-testid="collapsedControl"] p,
[data-testid="stSidebarCollapseButton"] span {
    font-size: 0 !important;
    visibility: hidden !important;
}
[data-testid="stSidebarCollapseButton"] button {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
