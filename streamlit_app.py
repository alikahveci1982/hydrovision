import streamlit as st
import google.generativeai as genai
from PIL import Image
import urllib.parse
from typing import List
from pydantic import BaseModel, field_validator
import io
from datetime import datetime

# ─── DATA MODELS ──────────────────────────────────────────────────────────────
class AnalysisResult(BaseModel):
    parça_adı: str
    malzeme_tanitimi: str
    teknik_ozellikler: List[str]
    arıza_analizi: List[str]
    çözüm_önerisi: List[str]
    bakım_tavsiyesi: List[str]
    sema_analizi: List[str]

    @field_validator('teknik_ozellikler','arıza_analizi','çözüm_önerisi','bakım_tavsiyesi','sema_analizi', mode='before')
    @classmethod
    def ensure_list(cls, v):
        return [v] if isinstance(v, str) else v

class SchemaComponent(BaseModel):
    kod: str
    tip: str
    aciklama: str

class SchemaResult(BaseModel):
    devre_adi: str
    devre_tipi: str
    standart: str
    bilesenler: List[SchemaComponent]
    devre_akisi: List[str]
    basinc_hatlari: List[str]
    tespit_edilen_hatalar: List[str]
    guvenlik_analizi: List[str]
    iyilestirme_onerileri: List[str]

    @field_validator('devre_akisi','basinc_hatlari','tespit_edilen_hatalar','guvenlik_analizi','iyilestirme_onerileri', mode='before')
    @classmethod
    def ensure_list(cls, v):
        return [v] if isinstance(v, str) else v

    @field_validator('bilesenler', mode='before')
    @classmethod
    def ensure_comp_list(cls, v):
        if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
            return v
        return []

# ─── PDF: MALZEME RAPORU ──────────────────────────────────────────────────────
def generate_pdf_report(result: AnalysisResult, lang: str, image: Image.Image = None) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    DARK_BG=colors.HexColor("#050e1a"); CYAN=colors.HexColor("#00d4e8"); ORANGE=colors.HexColor("#ff6b1a")
    GREEN=colors.HexColor("#00e5a0"); LIGHT=colors.HexColor("#e8f4ff"); MID=colors.HexColor("#7aa8cc")
    CARD_BG=colors.HexColor("#0d1f33"); PANEL_BG=colors.HexColor("#091624")

    def S(name, **kw):
        base = dict(fontName="Helvetica", fontSize=9, textColor=MID, leading=13, spaceAfter=3)
        base.update(kw); return ParagraphStyle(name, **base)

    story = []
    now = datetime.now().strftime("%d.%m.%Y  %H:%M")
    hdr = Table([[Paragraph("HYDROVISION PRO", S("t", fontName="Helvetica-Bold", fontSize=20, textColor=CYAN, alignment=TA_CENTER)),
                  Paragraph(now, S("d", fontSize=8, alignment=TA_RIGHT))]], colWidths=["75%","25%"])
    hdr.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),DARK_BG),("ROWPADDING",(0,0),(-1,-1),10),("LINEBELOW",(0,0),(-1,0),1.5,CYAN)]))
    subtitle = "Endustriyel Malzeme Analiz Raporu" if lang=="TR" else "Industrial Material Analysis Report"
    story += [hdr, Paragraph(subtitle, S("sub", alignment=TA_CENTER, spaceAfter=8)), Spacer(1,8)]

    if image:
        ic = image.copy(); ic.thumbnail((160,160))
        ib = io.BytesIO(); ic.save(ib, format="PNG"); ib.seek(0)
        it = Table([[RLImage(ib, width=50*mm, height=50*mm)]])
        it.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),CARD_BG),("ALIGN",(0,0),(-1,-1),"CENTER"),("BOX",(0,0),(-1,-1),0.5,CYAN),("ROWPADDING",(0,0),(-1,-1),6)]))
        story += [it, Spacer(1,8)]

    pt = Table([[Paragraph(result.parça_adı.upper(), S("pn", fontName="Helvetica-Bold", fontSize=15, textColor=LIGHT))]])
    pt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),CARD_BG),("LEFTPADDING",(0,0),(-1,-1),14),("ROWPADDING",(0,0),(-1,-1),10),("LINEBEFORE",(0,0),(0,-1),4,CYAN)]))
    story += [pt, Spacer(1,4)]
    lbl = "Yapi / Malzeme:" if lang=="TR" else "Structure / Material:"
    mt = Table([[Paragraph(f"<b>{lbl}</b>", S("ml", fontName="Helvetica-Bold", fontSize=9, textColor=CYAN)),
                 Paragraph(result.malzeme_tanitimi, S("mb"))]], colWidths=["30%","70%"])
    mt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PANEL_BG),("ROWPADDING",(0,0),(-1,-1),8),("VALIGN",(0,0),(-1,-1),"TOP")]))
    story += [mt, Spacer(1,10)]

    def section(title, items, color, bg, prefix="*"):
        story.append(Paragraph(f"  {title}", S(f"s{title[:4]}", fontName="Helvetica-Bold", fontSize=12, textColor=CYAN, spaceBefore=10, spaceAfter=5)))
        story.append(HRFlowable(width="100%", thickness=0.5, color=color))
        story.append(Spacer(1,4))
        rows = [[Paragraph(f"{prefix}  {i}", S(f"r{i[:6]}", fontSize=9, textColor=color, leading=13, leftIndent=8))] for i in items]
        if rows:
            t = Table(rows, colWidths=["100%"])
            t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),bg),("ROWPADDING",(0,0),(-1,-1),5),("LINEBEFORE",(0,0),(0,-1),3,color)]))
            story.append(t)
        story.append(Spacer(1,4))

    tl = "Teknik Ozellikler" if lang=="TR" else "Technical Specifications"
    section(tl, result.teknik_ozellikler, CYAN, colors.HexColor("#050e1a"), "-")
    fl = "Tespit Edilen Arizalar" if lang=="TR" else "Detected Faults"
    section(fl, result.arıza_analizi, ORANGE, colors.HexColor("#1a0d05"), "!")
    sl = "Cozum Onerileri" if lang=="TR" else "Recommended Actions"
    section(sl, result.çözüm_önerisi, GREEN, colors.HexColor("#051a0f"), "+")
    bl = "Bakim Tavsiyeleri" if lang=="TR" else "Maintenance Advice"
    section(bl, result.bakım_tavsiyesi, CYAN, colors.HexColor("#050e1a"), "-")
    if result.sema_analizi:
        section("ISO 1219 Sema Analizi", result.sema_analizi, CYAN, colors.HexColor("#050e1a"), "-")

    story += [Spacer(1,14), HRFlowable(width="100%",thickness=0.5,color=colors.HexColor("#112540")), Spacer(1,4),
              Paragraph(f"HydroVision Pro | {now} | ISO 1219", S("ft", fontSize=7, alignment=TA_CENTER))]
    doc.build(story); buf.seek(0); return buf.read()

# ─── PDF: ŞEMA RAPORU ─────────────────────────────────────────────────────────
def generate_schema_pdf(result: SchemaResult, lang: str, image: Image.Image = None) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    DARK_BG=colors.HexColor("#050e1a"); CYAN=colors.HexColor("#00d4e8"); ORANGE=colors.HexColor("#ff6b1a")
    GREEN=colors.HexColor("#00e5a0"); YELLOW=colors.HexColor("#f0c040"); LIGHT=colors.HexColor("#e8f4ff")
    MID=colors.HexColor("#7aa8cc"); CARD_BG=colors.HexColor("#0d1f33"); PANEL_BG=colors.HexColor("#091624")
    HDR_BG=colors.HexColor("#091e30")

    def S(name, **kw):
        base = dict(fontName="Helvetica", fontSize=9, textColor=MID, leading=13, spaceAfter=3)
        base.update(kw); return ParagraphStyle(name, **base)

    story = []
    now = datetime.now().strftime("%d.%m.%Y  %H:%M")
    hdr = Table([[Paragraph("HYDROVISION PRO", S("t", fontName="Helvetica-Bold", fontSize=20, textColor=CYAN, alignment=TA_CENTER)),
                  Paragraph(now, S("d", fontSize=8, alignment=TA_RIGHT))]], colWidths=["75%","25%"])
    hdr.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),DARK_BG),("ROWPADDING",(0,0),(-1,-1),10),("LINEBELOW",(0,0),(-1,0),1.5,CYAN)]))
    subtitle = "Hidrolik Devre Semasi Analiz Raporu" if lang=="TR" else "Hydraulic Circuit Schema Analysis Report"
    story += [hdr, Paragraph(subtitle, S("sub", alignment=TA_CENTER, spaceAfter=8)), Spacer(1,8)]

    if image:
        ic = image.copy(); ic.thumbnail((500,350))
        ib = io.BytesIO(); ic.save(ib, format="PNG"); ib.seek(0)
        ratio = ic.width / ic.height
        w = min(150, ratio * 90); h = w / ratio
        it = Table([[RLImage(ib, width=w*mm, height=h*mm)]])
        it.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),CARD_BG),("ALIGN",(0,0),(-1,-1),"CENTER"),("BOX",(0,0),(-1,-1),0.5,CYAN),("ROWPADDING",(0,0),(-1,-1),6)]))
        story += [it, Spacer(1,8)]

    dt = Table([[Paragraph(result.devre_adi.upper(), S("dn", fontName="Helvetica-Bold", fontSize=15, textColor=LIGHT))]])
    dt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),CARD_BG),("LEFTPADDING",(0,0),(-1,-1),14),("ROWPADDING",(0,0),(-1,-1),10),("LINEBEFORE",(0,0),(0,-1),4,CYAN)]))
    story += [dt, Spacer(1,4)]

    l1 = "Devre Tipi:" if lang=="TR" else "Circuit Type:"
    l2 = "Standart:" if lang=="TR" else "Standard:"
    info = Table([[Paragraph(f"<b>{l1}</b>", S("il", fontName="Helvetica-Bold", fontSize=9, textColor=CYAN)),
                   Paragraph(result.devre_tipi, S("iv")),
                   Paragraph(f"<b>{l2}</b>", S("il2", fontName="Helvetica-Bold", fontSize=9, textColor=CYAN)),
                   Paragraph(result.standart, S("iv2"))]], colWidths=["20%","30%","20%","30%"])
    info.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PANEL_BG),("ROWPADDING",(0,0),(-1,-1),8)]))
    story += [info, Spacer(1,12)]

    # Bileşenler tablosu
    ctitle = "Tespit Edilen Bilesenler" if lang=="TR" else "Identified Components"
    story.append(Paragraph(f"  {ctitle}", S("cs", fontName="Helvetica-Bold", fontSize=12, textColor=CYAN, spaceBefore=6, spaceAfter=5)))
    story.append(HRFlowable(width="100%", thickness=0.5, color=CYAN))
    story.append(Spacer(1,4))
    hk="Kod"; ht="Tip" if lang=="TR" else "Type"; ha="Aciklama" if lang=="TR" else "Description"
    comp_data = [[Paragraph(f"<b>{hk}</b>", S("ch1", fontName="Helvetica-Bold", fontSize=8, textColor=LIGHT)),
                  Paragraph(f"<b>{ht}</b>", S("ch2", fontName="Helvetica-Bold", fontSize=8, textColor=LIGHT)),
                  Paragraph(f"<b>{ha}</b>", S("ch3", fontName="Helvetica-Bold", fontSize=8, textColor=LIGHT))]]
    for c in result.bilesenler:
        comp_data.append([Paragraph(c.kod, S(f"ck{c.kod}", fontSize=8, textColor=CYAN, fontName="Helvetica-Bold")),
                          Paragraph(c.tip, S(f"ct{c.kod}", fontSize=8, textColor=MID)),
                          Paragraph(c.aciklama, S(f"ca{c.kod}", fontSize=8, textColor=MID))])
    if len(comp_data) > 1:
        ct = Table(comp_data, colWidths=["12%","30%","58%"])
        ct.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),HDR_BG),
                                ("ROWBACKGROUNDS",(0,1),(-1,-1),[DARK_BG,CARD_BG]),
                                ("ROWPADDING",(0,0),(-1,-1),6),("LINEBELOW",(0,0),(-1,0),1,CYAN),
                                ("LINEBELOW",(0,1),(-1,-1),0.3,colors.HexColor("#112540")),
                                ("VALIGN",(0,0),(-1,-1),"TOP")]))
        story.append(ct)
    story.append(Spacer(1,10))

    def section(title, items, color, bg, prefix=">"):
        story.append(Paragraph(f"  {title}", S(f"sc{title[:4]}", fontName="Helvetica-Bold", fontSize=12, textColor=CYAN, spaceBefore=8, spaceAfter=4)))
        story.append(HRFlowable(width="100%", thickness=0.5, color=color)); story.append(Spacer(1,4))
        rows = [[Paragraph(f"{prefix}  {i}", S(f"ri{i[:6]}", fontSize=9, textColor=color, leading=13, leftIndent=8))] for i in items]
        if rows:
            t = Table(rows, colWidths=["100%"])
            t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),bg),("ROWPADDING",(0,0),(-1,-1),5),("LINEBEFORE",(0,0),(0,-1),3,color)]))
            story.append(t)
        story.append(Spacer(1,4))

    al = "Devre Akis Sirasi" if lang=="TR" else "Circuit Flow Sequence"
    section(al, result.devre_akisi, CYAN, colors.HexColor("#050e1a"), "->")
    pl = "Basinc Hatlari" if lang=="TR" else "Pressure Lines"
    section(pl, result.basinc_hatlari, YELLOW, colors.HexColor("#1a1505"), "=")
    fl = "Tespit Edilen Hatalar" if lang=="TR" else "Detected Faults"
    section(fl, result.tespit_edilen_hatalar, ORANGE, colors.HexColor("#1a0d05"), "!")
    gl = "Guvenlik Analizi" if lang=="TR" else "Safety Analysis"
    section(gl, result.guvenlik_analizi, ORANGE, colors.HexColor("#1a0d05"), "!")
    il = "Iyilestirme Onerileri" if lang=="TR" else "Improvement Suggestions"
    section(il, result.iyilestirme_onerileri, GREEN, colors.HexColor("#051a0f"), "+")

    story += [Spacer(1,14), HRFlowable(width="100%",thickness=0.5,color=colors.HexColor("#112540")), Spacer(1,4),
              Paragraph(f"HydroVision Pro | {now} | ISO 1219", S("ft", fontSize=7, alignment=TA_CENTER))]
    doc.build(story); buf.seek(0); return buf.read()

# ─── AI FONKSİYONLAR ─────────────────────────────────────────────────────────
def analyze_material(img: Image.Image, model_name: str, lang: str) -> AnalysisResult:
    L = LANGUAGES[lang]
    model = genai.GenerativeModel(model_name=model_name, system_instruction=L["system_prompt"])
    prompt = (f"{L['user_prompt']}\nZORUNLU JSON:\n"
              '{"parça_adı":"...","malzeme_tanitimi":"...","teknik_ozellikler":["..."],'
              '"arıza_analizi":["..."],"çözüm_önerisi":["..."],"bakım_tavsiyesi":["..."],"sema_analizi":["..."]}')
    resp = model.generate_content(contents=[prompt, img],
                                  generation_config=genai.types.GenerationConfig(response_mime_type="application/json", temperature=0.1))
    return AnalysisResult.model_validate_json(resp.text.strip())

def analyze_schema(img: Image.Image, model_name: str, lang: str) -> SchemaResult:
    sys_p = ("Sen ISO 1219 hidrolik devre standartlarinda uzman kademli bir hidrolik muhendisisin. "
             "Devre semalarini analiz eder, sembolleri tanir, akis yonlerini ve basinc hatlarini belirlersin. "
             "Her zaman teknik, net ve yapilandirilmis JSON formatinda cevap verirsin."
             if lang=="TR" else
             "You are a senior hydraulic engineer specialized in ISO 1219 hydraulic circuit standards. "
             "You analyze circuit diagrams, identify symbols, determine flow directions and pressure lines. "
             "Always respond in technical, clear, structured JSON format.")
    model = genai.GenerativeModel(model_name=model_name, system_instruction=sys_p)
    prompt = (("Bu hidrolik devre semasini ISO 1219 standartlarina gore detayli analiz et. "
               "Tum sembolleri tani, devre akisini cikar, hatalari ve guvenlik risklerini belirle.\n"
               if lang=="TR" else
               "Analyze this hydraulic circuit diagram in detail according to ISO 1219 standards. "
               "Identify all symbols, extract circuit flow, determine faults and safety risks.\n") +
              "ZORUNLU JSON FORMAT:\n"
              '{"devre_adi":"...","devre_tipi":"Acik/Kapali merkez vb.","standart":"ISO 1219-1",'
              '"bilesenler":[{"kod":"P1","tip":"Sabit deplasmanli pompa","aciklama":"..."}],'
              '"devre_akisi":["P1 -> V1 -> C1"],"basinc_hatlari":["Yuksek basinc: P1 cikisi"],'
              '"tespit_edilen_hatalar":["..."],"guvenlik_analizi":["..."],"iyilestirme_onerileri":["..."]}')
    resp = model.generate_content(contents=[prompt, img],
                                  generation_config=genai.types.GenerationConfig(response_mime_type="application/json", temperature=0.1))
    return SchemaResult.model_validate_json(resp.text.strip())

# ─── LANGUAGES ────────────────────────────────────────────────────────────────
LANGUAGES = {
    "TR": {
        "caption": "Endüstriyel Arıza Analizi & Akıllı Sistem",
        "api_key_info": "💡 Başlamak için lütfen API anahtarınızı girin.",
        "system_prompt": "Sen kıdemli bir hidrolik mühendisisin. Teknik, net ve yapılandırılmış JSON formatında cevap verirsin.",
        "user_prompt": "Görseli ISO 1219 standartlarına göre analiz et. Profesyonel bir rapor hazırla.",
        "mode_label": "ANALİZ MODU SEÇİN",
        "mode_material": "📷 Malzeme Analizi",
        "mode_schema": "📐 Devre Şeması Analizi",
        "upload_title": "### 📸 Analiz İçin Görsel Seçin",
        "camera_input": "📷 FOTOĞRAF ÇEK",
        "file_uploader": "🖼️ GALERİDEN YÜKLE",
        "no_image_info": "Analiz için henüz bir görsel seçilmedi.",
        "analyze_button": "🔍 ANALİZİ BAŞLAT",
        "schema_analyze_button": "📐 ŞEMA ANALİZİNİ BAŞLAT",
        "analyzing_status": "⚙️ Malzeme analiz ediliyor...",
        "schema_analyzing_status": "⚙️ Devre şeması analiz ediliyor...",
        "complete_status": "✅ Analiz Tamamlandı",
        "material_label": "**Yapı/Malzeme:** ",
        "purchase_button": "🛒 PARÇA FİYATLARINI ARAŞTIR",
        "purchase_query": "Hidrolik {} fiyatları",
        "pdf_button": "📄 PDF RAPOR İNDİR",
        "txt_button": "📥 TXT RAPOR İNDİR",
        "error_label": "Sistem Hatası: {}",
        "schema_tip": "💡 En iyi sonuç için şemayı düz, aydınlık ve net çekin. Çizgiler ve semboller okunaklı olmalı.",
        "comp_table_title": "🔩 Tespit Edilen Bileşenler",
        "flow_title": "🔄 Devre Akış Sırası",
        "pressure_title": "⬛ Basınç Hatları",
        "fault_title": "⚠️ Tespit Edilen Hatalar",
        "safety_title": "🛡️ Güvenlik Analizi",
        "improve_title": "✅ İyileştirme Önerileri",
    },
    "EN": {
        "caption": "Industrial Fault Analysis & Smart System",
        "api_key_info": "💡 Please enter your API key to start.",
        "system_prompt": "You are a senior hydraulic engineer. Provide technical, clear, and structured JSON responses.",
        "user_prompt": "Analyze the image based on ISO 1219 standards. Prepare a professional report.",
        "mode_label": "SELECT ANALYSIS MODE",
        "mode_material": "📷 Material Analysis",
        "mode_schema": "📐 Circuit Schema Analysis",
        "upload_title": "### 📸 Select Image for Analysis",
        "camera_input": "📷 CAPTURE PHOTO",
        "file_uploader": "🖼️ UPLOAD FROM GALLERY",
        "no_image_info": "No image selected for analysis.",
        "analyze_button": "🔍 START ANALYSIS",
        "schema_analyze_button": "📐 START SCHEMA ANALYSIS",
        "analyzing_status": "⚙️ Analyzing material...",
        "schema_analyzing_status": "⚙️ Analyzing circuit schema...",
        "complete_status": "✅ Analysis Completed",
        "material_label": "**Structure/Material:** ",
        "purchase_button": "🛒 SEARCH PART PRICES",
        "purchase_query": "Hydraulic {} price",
        "pdf_button": "📄 DOWNLOAD PDF REPORT",
        "txt_button": "📥 DOWNLOAD TXT REPORT",
        "error_label": "System Error: {}",
        "schema_tip": "💡 For best results, capture the schema flat, well-lit and clear. Lines and symbols must be legible.",
        "comp_table_title": "🔩 Identified Components",
        "flow_title": "🔄 Circuit Flow Sequence",
        "pressure_title": "⬛ Pressure Lines",
        "fault_title": "⚠️ Detected Faults",
        "safety_title": "🛡️ Safety Analysis",
        "improve_title": "✅ Improvement Suggestions",
    }
}

# ─── SAYFA AYARLARI ───────────────────────────────────────────────────────────
st.set_page_config(page_title="HydroVision Pro", page_icon="⚙️", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Share+Tech+Mono&family=Exo+2:wght@300;400;600&display=swap');
:root{--bg-base:#050e1a;--bg-panel:#091624;--bg-card:#0d1f33;--bg-elevated:#112540;
--accent-cyan:#00d4e8;--accent-blue:#0088cc;--accent-orange:#ff6b1a;--accent-green:#00e5a0;--accent-yellow:#f0c040;
--text-primary:#e8f4ff;--text-secondary:#7aa8cc;--text-muted:#3d6080;
--border:rgba(0,212,232,0.15);--glow-cyan:0 0 20px rgba(0,212,232,0.3);}
html,body,.stApp,[data-testid="stAppViewContainer"]{background-color:var(--bg-base) !important;
background-image:linear-gradient(rgba(0,212,232,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(0,212,232,0.03) 1px,transparent 1px) !important;
background-size:40px 40px !important;font-family:'Exo 2',sans-serif !important;}
[data-testid="stHeader"]{background:rgba(5,14,26,0.9) !important;border-bottom:1px solid var(--border);}
.main .block-container{background:transparent !important;padding-top:2rem;max-width:1100px;}
section[data-testid="stSidebar"]{background-color:var(--bg-panel) !important;border-right:1px solid var(--border) !important;}
h1,h2,h3{color:var(--text-primary) !important;font-family:'Rajdhani',sans-serif !important;letter-spacing:3px !important;text-align:center;}
h1{font-size:2rem !important;background:linear-gradient(90deg,var(--accent-cyan),var(--text-primary));-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
p,span,label,div,.stMarkdown{color:var(--text-secondary) !important;font-family:'Exo 2',sans-serif !important;}
[data-testid="stTextInput"] input,[data-testid="stSelectbox"]>div>div{background:var(--bg-card) !important;border:1px solid var(--border) !important;border-radius:8px !important;color:var(--text-primary) !important;font-family:'Share Tech Mono',monospace !important;font-size:13px !important;}
[data-testid="stTextInput"] input:focus{border-color:var(--accent-cyan) !important;box-shadow:var(--glow-cyan) !important;}
div.stButton>button{width:100%;min-height:56px !important;background:linear-gradient(135deg,var(--accent-cyan),var(--accent-blue)) !important;color:var(--bg-base) !important;font-family:'Rajdhani',sans-serif !important;font-weight:700 !important;font-size:16px !important;letter-spacing:3px !important;text-transform:uppercase !important;border:none !important;border-radius:10px !important;box-shadow:0 4px 24px rgba(0,212,232,0.25) !important;transition:all 0.25s !important;margin-bottom:8px;}
div.stButton>button:hover{transform:translateY(-2px) !important;box-shadow:0 8px 32px rgba(0,212,232,0.4) !important;}
[data-testid="stCameraInput"] button{background:linear-gradient(135deg,var(--accent-orange),#cc3d00) !important;color:white !important;font-family:'Rajdhani',sans-serif !important;font-weight:700 !important;border-radius:8px !important;border:none !important;}
[data-testid="stFileUploader"]{background:var(--bg-card) !important;border:2px dashed var(--border) !important;border-radius:14px !important;padding:12px !important;}
[data-testid="stFileUploader"]:hover{border-color:var(--accent-cyan) !important;box-shadow:var(--glow-cyan) !important;}
[data-testid="stCameraInput"]{background:var(--bg-card) !important;border:1px solid var(--border) !important;border-radius:14px !important;overflow:hidden !important;}
.info-card{background:var(--bg-card);padding:20px 24px;border-radius:14px;margin-bottom:16px;border-left:4px solid var(--accent-cyan);box-shadow:0 4px 16px rgba(0,0,0,0.4);}
.fault-card{background:rgba(255,107,26,0.08);padding:20px 24px;border-radius:14px;border:1px solid rgba(255,107,26,0.25);border-left:4px solid var(--accent-orange);margin-bottom:12px;}
.solution-card{background:rgba(0,229,160,0.07);padding:20px 24px;border-radius:14px;border:1px solid rgba(0,229,160,0.2);border-left:4px solid var(--accent-green);margin-bottom:12px;}
.schema-card{background:rgba(0,212,232,0.05);padding:20px 24px;border-radius:14px;border:1px solid rgba(0,212,232,0.2);border-left:4px solid var(--accent-cyan);margin-bottom:12px;}
.safety-card{background:rgba(255,107,26,0.06);padding:16px 20px;border-radius:12px;border:1px solid rgba(255,107,26,0.2);border-left:4px solid var(--accent-orange);margin-bottom:10px;}
.yellow-card{background:rgba(240,192,64,0.06);padding:16px 20px;border-radius:12px;border:1px solid rgba(240,192,64,0.2);border-left:4px solid var(--accent-yellow);margin-bottom:10px;}
[data-testid="stStatusWidget"]{background:var(--bg-card) !important;border:1px solid var(--border) !important;border-radius:10px !important;}
[data-testid="stAlert"]{background:var(--bg-elevated) !important;border:1px solid var(--border) !important;border-radius:10px !important;color:var(--text-secondary) !important;}
[data-testid="stDownloadButton"] button{background:var(--bg-elevated) !important;border:1px solid var(--border) !important;color:var(--accent-cyan) !important;font-family:'Share Tech Mono',monospace !important;letter-spacing:1px !important;border-radius:8px !important;}
[data-testid="stDownloadButton"] button:hover{border-color:var(--accent-cyan) !important;box-shadow:var(--glow-cyan) !important;}
.share-btn{display:block;width:100%;padding:16px;background:#25D366 !important;color:white !important;text-align:center;border-radius:10px;font-family:'Rajdhani',sans-serif;font-weight:700;font-size:15px;letter-spacing:2px;text-decoration:none;margin-top:10px;box-shadow:0 4px 16px rgba(37,211,102,0.25);}
::-webkit-scrollbar{width:6px;} ::-webkit-scrollbar-track{background:var(--bg-base);} ::-webkit-scrollbar-thumb{background:var(--accent-blue);border-radius:3px;}
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
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
col_l, col_r = st.columns([8, 2])
with col_r:
    st.session_state.lang = st.selectbox("", ["TR","EN"], index=0 if st.session_state.lang=="TR" else 1, label_visibility="collapsed")
L = LANGUAGES[st.session_state.lang]
st.markdown(f"<p style='text-align:center;font-size:1.1rem;margin-top:-15px;font-family:Share Tech Mono,monospace;letter-spacing:2px;'>🔧 {L['caption']}</p>", unsafe_allow_html=True)

if not st.session_state.get("api_key"):
    st.info(L["api_key_info"]); st.stop()

# ─── MOD SEÇİCİ ───────────────────────────────────────────────────────────────
st.markdown(f"<p style='text-align:center;font-size:0.8rem;letter-spacing:4px;color:#3d6080;margin-bottom:4px;'>{L['mode_label']}</p>", unsafe_allow_html=True)
mode = st.radio("", [L["mode_material"], L["mode_schema"]], horizontal=True, label_visibility="collapsed")
is_schema = (mode == L["mode_schema"])

if is_schema:
    st.info(L["schema_tip"])

# ─── GÖRSEL GİRİŞ ─────────────────────────────────────────────────────────────
st.markdown(L["upload_title"])
c1, c2 = st.columns(2)
with c1:
    cam = st.camera_input(L["camera_input"])
with c2:
    upload = st.file_uploader(L["file_uploader"], type=["jpg","png","webp"])

final_file = cam or upload
if final_file:
    img = Image.open(final_file)
    max_px = 1600 if is_schema else 1024
    if max(img.size) > max_px:
        img.thumbnail((max_px, max_px))
    st.image(img, use_container_width=True)

    btn_lbl = L["schema_analyze_button"] if is_schema else L["analyze_button"]
    if st.button(btn_lbl, type="primary"):
        try:
            # ════════════════════════════════════════
            # MALZEME ANALİZİ
            # ════════════════════════════════════════
            if not is_schema:
                with st.status(L["analyzing_status"]) as status:
                    result = analyze_material(img, selected_model, st.session_state.lang)
                    status.update(label=L["complete_status"], state="complete")

                st.markdown(f'<div class="info-card"><h2 style="color:var(--text-primary) !important;margin:0;">{result.parça_adı.upper()}</h2><p style="margin-top:5px;">{L["material_label"]}{result.malzeme_tanitimi}</p></div>', unsafe_allow_html=True)
                st.markdown("### 📍 Teknik Özet")
                for i in result.teknik_ozellikler: st.markdown(f"🔹 {i}")
                st.markdown('<div class="fault-card"><h4 style="color:var(--accent-orange) !important;margin-bottom:10px;">⚠️ Tespit Edilen Kritik Hatalar</h4>', unsafe_allow_html=True)
                for i in result.arıza_analizi: st.markdown(f"• {i}")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('<div class="solution-card"><h4 style="color:var(--accent-green) !important;margin-bottom:10px;">✅ Önerilen Aksiyon Planı</h4>', unsafe_allow_html=True)
                for i in result.çözüm_önerisi: st.markdown(f"• {i}")
                st.markdown(f"<br><b>🔧 Bakım:</b> {', '.join(result.bakım_tavsiyesi)}", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                if result.sema_analizi:
                    st.markdown('<div class="schema-card"><h4 style="color:var(--accent-cyan) !important;margin-bottom:10px;">🔍 ISO 1219 Şema Analizi</h4>', unsafe_allow_html=True)
                    for i in result.sema_analizi: st.markdown(f"• {i}")
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("---")
                d1, d2 = st.columns(2)
                with d1:
                    pdf_b = generate_pdf_report(result, st.session_state.lang, img)
                    st.download_button(L["pdf_button"], pdf_b, f"hydrovision_{result.parça_adı.lower().replace(' ','_')}.pdf", "application/pdf", use_container_width=True)
                with d2:
                    txt = (f"HYDROVISION PRO ANALIZ RAPORU\nTarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                           f"---------------------------\nParca: {result.parça_adı}\nMalzeme: {result.malzeme_tanitimi}\n\n"
                           f"Teknik:\n" + "\n".join([f"- {i}" for i in result.teknik_ozellikler]) +
                           f"\n\nAriza:\n" + "\n".join([f"- {i}" for i in result.arıza_analizi]) +
                           f"\n\nCozum:\n" + "\n".join([f"- {i}" for i in result.çözüm_önerisi]) +
                           f"\n\nBakim: {', '.join(result.bakım_tavsiyesi)}\n")
                    st.download_button(L["txt_button"], txt, f"hydrovision_{result.parça_adı.lower().replace(' ','_')}.txt", "text/plain", use_container_width=True)

                wm = f"*HydroVision Pro*\n*Parca:* {result.parça_adı}\n*Ariza:* {result.arıza_analizi[0] if result.arıza_analizi else '-'}\n*Cozum:* {result.çözüm_önerisi[0] if result.çözüm_önerisi else '-'}"
                st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(wm)}" target="_blank" class="share-btn">📱 WHATSAPP İLE PAYLAŞ</a>', unsafe_allow_html=True)
                q = urllib.parse.quote(L["purchase_query"].format(result.parça_adı))
                st.markdown(f'<a href="https://www.google.com/search?q={q}" target="_blank" style="text-decoration:none;"><div style="width:100%;background:linear-gradient(135deg,var(--accent-cyan),var(--accent-blue));color:var(--bg-base);text-align:center;border-radius:10px;padding:16px;font-family:Rajdhani,sans-serif;font-weight:700;font-size:15px;letter-spacing:2px;margin-top:10px;box-shadow:0 4px 24px rgba(0,212,232,0.25);">{L["purchase_button"]}</div></a>', unsafe_allow_html=True)

            # ════════════════════════════════════════
            # ŞEMA ANALİZİ
            # ════════════════════════════════════════
            else:
                with st.status(L["schema_analyzing_status"]) as status:
                    sr = analyze_schema(img, selected_model, st.session_state.lang)
                    status.update(label=L["complete_status"], state="complete")

                # Devre başlığı
                st.markdown(f'<div class="info-card"><h2 style="color:var(--text-primary) !important;margin:0;">📐 {sr.devre_adi.upper()}</h2><p style="margin-top:6px;">⚙️ <b style="color:var(--accent-cyan);">{sr.devre_tipi}</b> &nbsp;|&nbsp; 📋 {sr.standart}</p></div>', unsafe_allow_html=True)

                # Bileşenler tablosu
                st.markdown(f"### {L['comp_table_title']}")
                if sr.bilesenler:
                    import pandas as pd
                    df = pd.DataFrame([{"Kod": c.kod, "Tip": c.tip, "Açıklama": c.aciklama} for c in sr.bilesenler])
                    st.dataframe(df, use_container_width=True, hide_index=True)

                # Devre akışı
                st.markdown(f"### {L['flow_title']}")
                st.markdown('<div class="schema-card">', unsafe_allow_html=True)
                for i, f in enumerate(sr.devre_akisi): st.markdown(f"**{i+1}.** {f}")
                st.markdown('</div>', unsafe_allow_html=True)

                # Basınç hatları
                if sr.basinc_hatlari:
                    st.markdown(f"### {L['pressure_title']}")
                    st.markdown('<div class="yellow-card">', unsafe_allow_html=True)
                    for p in sr.basinc_hatlari: st.markdown(f"⬛ {p}")
                    st.markdown('</div>', unsafe_allow_html=True)

                # Hatalar
                st.markdown(f"### {L['fault_title']}")
                st.markdown('<div class="fault-card">', unsafe_allow_html=True)
                for f in sr.tespit_edilen_hatalar: st.markdown(f"⚠️ {f}")
                st.markdown('</div>', unsafe_allow_html=True)

                # Güvenlik
                st.markdown(f"### {L['safety_title']}")
                st.markdown('<div class="safety-card">', unsafe_allow_html=True)
                for g in sr.guvenlik_analizi: st.markdown(f"🛡️ {g}")
                st.markdown('</div>', unsafe_allow_html=True)

                # İyileştirmeler
                st.markdown(f"### {L['improve_title']}")
                st.markdown('<div class="solution-card">', unsafe_allow_html=True)
                for i in sr.iyilestirme_onerileri: st.markdown(f"✅ {i}")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("---")
                d1, d2 = st.columns(2)
                with d1:
                    pdf_b = generate_schema_pdf(sr, st.session_state.lang, img)
                    st.download_button(L["pdf_button"], pdf_b, f"schema_{sr.devre_adi.lower().replace(' ','_')}.pdf", "application/pdf", use_container_width=True)
                with d2:
                    comp_txt = "\n".join([f"  {c.kod} | {c.tip} | {c.aciklama}" for c in sr.bilesenler])
                    txt = (f"HYDROVISION PRO - DEVRE SEMASI ANALIZI\n"
                           f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n---------------------------\n"
                           f"Devre: {sr.devre_adi}\nTip: {sr.devre_tipi}\nStandart: {sr.standart}\n\n"
                           f"Bilesenler:\n{comp_txt}\n\n"
                           f"Devre Akisi:\n" + "\n".join([f"- {f}" for f in sr.devre_akisi]) +
                           f"\n\nBasinc Hatlari:\n" + "\n".join([f"- {p}" for p in sr.basinc_hatlari]) +
                           f"\n\nHatalar:\n" + "\n".join([f"- {f}" for f in sr.tespit_edilen_hatalar]) +
                           f"\n\nGuvenlik:\n" + "\n".join([f"- {g}" for g in sr.guvenlik_analizi]) +
                           f"\n\nIyilestirme:\n" + "\n".join([f"- {i}" for i in sr.iyilestirme_onerileri]) + "\n")
                    st.download_button(L["txt_button"], txt, f"schema_{sr.devre_adi.lower().replace(' ','_')}.txt", "text/plain", use_container_width=True)

                wm = (f"*HydroVision Pro - Sema Analizi*\n*Devre:* {sr.devre_adi}\n"
                      f"*Tip:* {sr.devre_tipi}\n*Kritik:* {sr.tespit_edilen_hatalar[0] if sr.tespit_edilen_hatalar else '-'}")
                st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(wm)}" target="_blank" class="share-btn">📱 WHATSAPP İLE PAYLAŞ</a>', unsafe_allow_html=True)

        except Exception as e:
            st.error(L["error_label"].format(str(e)))
            st.markdown('<div class="fault-card"><h4>💡 Ipucu</h4><ul><li>Görseli daha net çekin.</li><li>Şema ise semboller okunaklı olmalı.</li><li>Farklı AI modeli deneyin.</li></ul></div>', unsafe_allow_html=True)
else:
    st.info(L["no_image_info"])
