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
    --border: rgba(
