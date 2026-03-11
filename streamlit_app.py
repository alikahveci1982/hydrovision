import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse

# ─── SAYFA AYARLARI ───────────────────────────────────────────────────────────
st.set_page_config(page_title="HydroVision Pro", page_icon="⚙️", layout="centered")

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
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 HYDROVISION PRO")
st.caption("🔧 Arıza Tespit & Akıllı Satın Alma")

# ─── API ANAHTARI ─────────────────────────────────────────────────────────────
api_key = st.text_input("🔑 Gemini API Anahtarı", type="password",
                        placeholder="AIza... şeklinde başlayan anahtarınızı girin")

# ─── MODEL ÖNCELİK LİSTESİ ────────────────────────────────────────────────────
# En yeniden eskiye sıralı — hesabınızda hangisi varsa otomatik seçilir
PREFERRED_MODELS = [
    "models/gemini-2.5-pro-preview-03-25",
    "models/gemini-2.5-pro",
    "models/gemini-2.0-flash-lite",
    "models/gemini-1.5-pro-latest",
    "models/gemini-1.5-flash-latest",
    "models/gemini-1.5-pro",
    "models/gemini-1.5-flash",
]

# ─── MODEL SEÇİCİ ─────────────────────────────────────────────────────────────
def get_best_model(key: str) -> str:
    """API'den mevcut modelleri alır, en uygununu döner."""
    genai.configure(api_key=key)
    try:
        available = [
            m.name for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
            and "gemini" in m.name.lower()
            and "embedding" not in m.name.lower()
        ]
    except Exception as e:
        raise Exception(f"Model listesi alınamadı: {e}")

    if not available:
        raise Exception("Hiç kullanılabilir model bulunamadı. API anahtarını kontrol edin.")

    # Öncelik listesinden ilk eşleşeni al
    for pref in PREFERRED_MODELS:
        if pref in available:
            return pref

    # Listede yoksa mevcut ilk modeli kullan
    return available[0]


# ─── ANALİZ FONKSİYONU ────────────────────────────────────────────────────────
def analyze_image(key: str, img: Image.Image) -> tuple[str, str]:
    """Görseli analiz eder. (model_adı, sonuç_metni) döner."""
    model_name = get_best_model(key)

    prompt = """
Sen uzman bir hidrolik mühendisisin. Görseli dikkatlice incele ve
aşağıdaki formatta yanıt ver:

PARÇA_ADI: [Kısa ve net parça ismi, örn: Yön Kontrol Valfi]
---
1. ARIZA ANALİZİ:
   - [Olası arıza nedeni 1]
   - [Olası arıza nedeni 2]

2. ÇÖZÜM ÖNERİSİ:
   - [Yapılması gereken adım 1]
   - [Yapılması gereken adım 2]

3. BAKIM TAVSİYESİ:
   - [Önleyici bakım önerisi]
"""
    model = genai.GenerativeModel(model_name)
    response = model.generate_content([prompt, img])
    return model_name, response.text


# ─── GÖRSEL YÜKLEME ───────────────────────────────────────────────────────────
t1, t2 = st.tabs(["📸 Fotoğraf Çek", "📂 Dosya Yükle"])
with t1:
    cam = st.camera_input("Kamerayı Aç")
with t2:
    file = st.file_uploader("Dosya Seç", type=["jpg", "png", "jpeg"])

final_img = cam if cam else file

# ─── ANA AKIŞ ─────────────────────────────────────────────────────────────────
if not api_key:
    st.info("👆 Başlamak için Gemini API anahtarınızı girin.")
    st.stop()

if not final_img:
    st.info("📷 Analiz etmek istediğiniz görseli yükleyin veya çekin.")
    st.stop()

# Görsel önizleme
img_pil = Image.open(final_img)
st.image(img_pil, caption="Yüklenen Görsel", use_container_width=True)
st.success("✅ Analiz Hazır")

if st.button("🔍 ANALİZ ET VE PARÇA BUL"):
    try:
        with st.spinner("⚙️ Görsel analiz ediliyor, lütfen bekleyin..."):
            model_name, result_text = analyze_image(api_key, img_pil)

        st.info(f"🤖 Kullanılan model: `{model_name}`")
        st.success("✅ ANALİZ TAMAMLANDI")
        st.write(result_text)

        # Parça adını çıkar ve arama linki oluştur
        parts = result_text.split("---")
        p_name = parts[0].replace("PARÇA_ADI:", "").strip()
        if not p_name:
            p_name = "hidrolik parça"

        q = urllib.parse.quote(f"Hidrolik {p_name}")
        st.markdown(
            f'<a href="https://www.google.com/search?q={q}+fiyatları" target="_blank" style="text-decoration:none;">'
            f'<button style="width:100%; height:3em; background-color:#4285F4; color:white; '
            f'border:none; border-radius:10px; font-size:16px; cursor:pointer; margin-top:10px;">'
            f'🛒 {p_name} Satın Alma Seçenekleri</button></a>',
            unsafe_allow_html=True
        )

    except Exception as e:
        err = str(e)
        st.error(f"❌ Hata: {err}")

        # Hata tipine göre yönlendirme
        if "429" in err:
            st.warning("⚠️ Kota doldu. Birkaç dakika bekleyip tekrar deneyin.")
            st.info("💡 Kota artırmak için: https://console.cloud.google.com/billing")
        elif "404" in err or "not found" in err.lower():
            st.warning("⚠️ Bu model hesabınızda mevcut değil. Sistem başka model aradı ama bulamadı.")
            st.info("💡 Yeni API anahtarı alın: https://aistudio.google.com/app/apikey")
        elif "403" in err or "api_key" in err.lower():
            st.warning("⚠️ API anahtarı geçersiz veya yetersiz izne sahip.")
            st.info("💡 Anahtarı kontrol edin: https://aistudio.google.com/app/apikey")
        elif "quota" in err.lower():
            st.warning("⚠️ Günlük istek limitine ulaşıldı.")
            st.info("💡 Billing ekleyerek limiti kaldırın: https://console.cloud.google.com/billing")
