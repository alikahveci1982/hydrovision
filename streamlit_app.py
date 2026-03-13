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

# ─── ANALİZ FONKSİYONU (Yeni versiyon – schema olmadan) ────────────────────────
def analyze_image(img: Image.Image) -> tuple[str, AnalysisResult]:
    model_name = get_best_model()
    model = genai.GenerativeModel(model_name)

    prompt = """
Sen uzman bir hidrolik sistemler mühendisisin. Görseli çok dikkatli incele.

Aşağıdaki **tam JSON** formatında cevap ver. Ekstra metin, açıklama, markdown veya JSON dışı hiçbir şey yazma!

{
  "parça_adı": "Kısa ve net parça ismi, örn: Yön Kontrol Valfi",
  "arıza_analizi": ["Olası neden 1", "Olası neden 2", ...],
  "çözüm_önerisi": ["Adım 1", "Adım 2", ...],
  "bakım_tavsiyesi": ["Öneri 1", "Öneri 2", ...]
}

Cevabın **sadece geçerli JSON** olsun, başlama veya bitirme işareti koyma.
"""

    try:
        response = model.generate_content(
            contents=[prompt, img],
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",  # Hâlâ bunu kullanabiliriz
                temperature=0.1,  # Düşük tut → daha tutarlı JSON
                top_p=0.95,
                candidate_count=1,
            ),
            safety_settings={
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            }
        )

        # JSON parse et ve Pydantic ile validate et
        import json
        raw_json = response.text.strip()
        data = json.loads(raw_json)
        result = AnalysisResult.model_validate(data)
        return model_name, result

    except json.JSONDecodeError:
        raise RuntimeError("Model JSON formatında cevap vermedi. Tekrar deneyin.")
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


st.markdown("""
<style>
    /* Streamlit'in kendi padding/margin'lerini sıfırla */
    .main .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
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
        overflow: hidden !important;
    }
    
    /* Görseller ve içerikler tam genişlik */
    .stImage, .stPlotlyChart, .element-container {
        width: 100vw !important;
        max-width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)
