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
    layout="centered",
    initial_sidebar_state="auto"
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
</style>
""", unsafe_allow_html=True)

st.title("🤖 HYDROVISION PRO")
st.caption("🔧 Arıza Tespit & Akıllı Satın Alma")

# ─── API ANAHTARI YÖNETİMİ (session_state ile kalıcı) ──────────────────────────
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

api_key = st.text_input(
    "🔑 Gemini API Anahtarı",
    type="password",
    value=st.session_state.api_key,
    placeholder="AIza... şeklinde başlayan anahtarınızı girin",
    help="https://aistudio.google.com/app/apikey adresinden ücretsiz alabilirsiniz"
)

if api_key:
    st.session_state.api_key = api_key
    genai.configure(api_key=api_key)
else:
    st.info("👆 Başlamak için Gemini API anahtarınızı girin.")
    st.stop()

# ─── MODEL ÖNCELİK LİSTESİ (2026 Mart gerçekçi durum) ──────────────────────────
PREFERRED_MODELS = [
    "models/gemini-3.1-pro-preview",       # En güçlü (2026)
    "models/gemini-2.5-pro",
    "models/gemini-2.5-flash",
    "models/gemini-2.5-flash-lite",
    "models/gemini-3-flash",
]

@lru_cache(maxsize=1)
def get_available_models() -> List[str]:
    """Cache'lenmiş model listesi (saatte bir yenilenir)"""
    try:
        models = genai.list_models()
        return [
            m.name for m in models
            if "generateContent" in m.supported_generation_methods
            and "gemini" in m.name.lower()
            and not any(x in m.name.lower() for x in ["embedding", "tts"])
        ]
    except Exception as e:
        st.error(f"Model listesi alınamadı: {e}")
        return []

def get_best_model() -> str:
    available = get_available_models()
    if not available:
        raise ValueError("Hiç kullanılabilir Gemini modeli bulunamadı. API anahtarını kontrol edin.")
    for pref in PREFERRED_MODELS:
        if pref in available:
            return pref
    return available[0]  # fallback

# ─── STRUCTURED ÇIKTI MODELİ (Pydantic) ───────────────────────────────────────
class AnalysisResult(BaseModel):
    parça_adı: str = Field(description="Kısa ve net parça ismi, örn: Yön Kontrol Valfi")
    arıza_analizi: List[str] = Field(description="Olası arıza nedenleri")
    çözüm_önerisi: List[str] = Field(description="Yapılması gereken adımlar")
    bakım_tavsiyesi: List[str] = Field(description="Önleyici bakım önerileri")

# ─── ANALİZ FONKSİYONU ────────────────────────────────────────────────────────
def analyze_image(img: Image.Image) -> tuple[str, AnalysisResult]:
    model_name = get_best_model()
    model = genai.GenerativeModel(model_name)

    prompt = """
Sen uzman bir hidrolik / hidrolik sistemler mühendisisin.
Görseli çok dikkatli incele ve aşağıdaki JSON yapısına tam uyan cevap ver.
Ekstra metin, açıklama veya JSON dışı hiçbir şey yazma.
"""

    try:
        response = model.generate_content(
            contents=[prompt, img],
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                response_schema=AnalysisResult.model_json_schema(),
                temperature=0.2,
                top_p=0.95,
            ),
            safety_settings={
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            }
        )
        result = AnalysisResult.model_validate_json(response.text)
        return model_name, result

    except Exception as e:
        raise RuntimeError(f"Analiz sırasında hata: {str(e)}")

# ─── GÖRSEL YÜKLEME ───────────────────────────────────────────────────────────
st.markdown("### 📸 Görsel Yükleme / Çekme")
col1, col2 = st.columns(2)
with col1:
    camera_input = st.camera_input("📷 Kamerayı Aç")
with col2:
    uploaded_file = st.file_uploader("📂 Dosya Seç", type=["jpg", "jpeg", "png", "webp"])

final_file = camera_input or uploaded_file

if not final_file:
    st.info("Lütfen analiz etmek istediğiniz hidrolik parça / sistem görselini yükleyin veya kamera ile çekin.")
    st.stop()

# Görseli aç + resize (Gemini kota ve hız için)
img = Image.open(final_file)
if img.size[0] > 2000 or img.size[1] > 2000:
    img.thumbnail((2000, 2000), Image.Resampling.LANCZOS)

st.image(img, caption="Yüklenen / Çekilen Görsel", use_container_width=True)

# ─── ANALİZ BUTONU ────────────────────────────────────────────────────────────
if st.button("🔍 ANALİZ ET VE PARÇA BUL", type="primary"):
    try:
        with st.status("⚙️ Görsel analiz ediliyor...", expanded=True) as status:
            status.write("Model seçiliyor...")
            model_name = get_best_model()
            status.write(f"Kullanılan model: **{model_name}**")

            status.write("Gemini API'ye gönderiliyor...")
            model_name, result = analyze_image(img)

            status.update(label="✅ Analiz Tamamlandı!", state="complete")

        # Sonuçları güzel göster
        st.subheader(f"🔧 Parça: **{result.parça_adı}**")
        st.markdown("**1. ARIZA ANALİZİ**")
        for item in result.arıza_analizi:
            st.markdown(f"• {item}")

        st.markdown("**2. ÇÖZÜM ÖNERİSİ**")
        for item in result.çözüm_önerisi:
            st.markdown(f"• {item}")

        st.markdown("**3. BAKIM TAVSİYESİ**")
        for item in result.bakım_tavsiyesi:
            st.markdown(f"• {item}")

        # Satın alma linki
        query = urllib.parse.quote(f"Hidrolik {result.parça_adı} fiyatları")
        st.markdown(
            f"""
            <a href="https://www.google.com/search?q={query}" target="_blank" style="text-decoration:none;">
                <button style="width:100%; background:#4285F4; color:white; border:none; border-radius:10px; padding:12px; font-size:16px; cursor:pointer;">
                    🛒 {result.parça_adı} Satın Alma Seçenekleri (Google'da Ara)
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )

    except Exception as e:
        st.error(f"❌ Hata oluştu: {str(e)}")
        if "429" in str(e):
            st.warning("Kota limitine ulaşıldı. Birkaç dakika bekleyin veya billing etkinleştirin.")
        elif "invalid" in str(e).lower() or "key" in str(e).lower():
            st.warning("API anahtarı geçersiz görünüyor. Yeni anahtar deneyin.")
