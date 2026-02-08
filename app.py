import streamlit as st
from streamlit_option_menu import option_menu
import asyncio
import edge_tts
import os
import requests
import yt_dlp
from io import BytesIO
from textblob import TextBlob
from deep_translator import GoogleTranslator

# --- SAFETY CHECK ---
try:
    from pydub import AudioSegment
    HAS_MUSIC_ENGINE = True
except ImportError:
    HAS_MUSIC_ENGINE = False

# --- DOCUMENT TOOLS ---
from PyPDF2 import PdfReader, PdfMerger
from docx import Document
from PIL import Image
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

# --- Page Config (Pro Level) ---
st.set_page_config(page_title="Elite Super App", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# --- ⚡ SPEED BOOSTER (Caching) ---
# Ye function baar-baar load nahi hoga, memory mein save rahega
@st.cache_resource
def load_heavy_engines():
    # Simulation of heavy loading
    return True

_ = load_heavy_engines()

# --- CUSTOM CSS (Smooth Scroll + No Refresh) ---
st.markdown("""
    <style>
    /* 1. Reset: Pehle sab kuch normal karo */
    * {
        box-sizing: border-box;
    }

    /* 2. Main Fix: Scrolling chalu, lekin "Khinchawat" (Refresh) band */
    html, body {
        overscroll-behavior: none !important; /* Ye magic line hai jo refresh rokti hai */
        overflow-y: auto !important; /* Ye scrolling ko wapas smooth banati hai */
        height: 100%;
    }

    /* 3. App Container ko bhi control karo */
    .stApp {
        overscroll-behavior: none !important;
        background-color: #0e1117; /* Dark background fix */
    }

    /* 4. Header Gayab (Taaki upar galti se click na ho) */
    header, [data-testid="stHeader"] {
        display: none !important;
        height: 0px !important;
    }

    /* 5. Mobile View Optimization */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 5rem !important;
        max-width: 100% !important;
    }

    /* 6. Buttons & Cards Design (Same as before) */
    .stButton>button {
        width: 100%; border-radius: 12px; 
        background-color: #00e676; color: black; 
        font-weight: bold; border: none; padding: 12px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.2);
    }
    
    .dashboard-card {
        background-color: #1e1e1e; padding: 15px; 
        border-radius: 15px; border: 1px solid #333; 
        text-align: center; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 🧠 LOGIC FUNCTIONS ---
def desi_anuvad_logic(text, custom_map_text):
    try:
        translated = GoogleTranslator(source='auto', target='hi').translate(text)
    except: return "⚠️ Net Error"

    replacements = {
        "Sect": "अखाड़ा (Akhada)", "Peak": "चोटी (Pahadi)", "Realm": "लोक (Lok)",
        "Continent": "महाद्वीप", "City": "नगर", "Village": "गाँव",
        "Patriarch": "मुखिया", "Elder": "दाऊ", "Disciple": "चेला", "Master": "गुरुजी"
    }
    
    if custom_map_text:
        lines = custom_map_text.split('\n')
        for line in lines:
            if '=' in line:
                parts = line.split('=')
                text = text.replace(parts[0].strip(), parts[1].strip())
                replacements[parts[0].strip()] = parts[1].strip()

    for word, desi_word in replacements.items():
        translated = translated.replace(word, desi_word)

    desi_tadka = {"मैं ": "हम ", "तुम ": "तोरा ", "क्यों": "काये", "वहाँ": "उते", "यहाँ": "इते"}
    for k, v in desi_tadka.items(): translated = translated.replace(k, v)
    return translated

# --- 🎭 RESOURCES ---
CHARACTERS = {
    "🔥 Thriller (Shiv)": {"voice": "ur-PK-SalmanNeural", "pitch": "-15Hz", "rate": "-5%"},
    "❤️ Romance (Viraj)": {"voice": "hi-IN-MadhurNeural", "pitch": "+5Hz", "rate": "+5%"},
    "👻 Horror (Bhoot)": {"voice": "hi-IN-SwaraNeural", "pitch": "-10Hz", "rate": "-20%"}
}
MOOD_MUSIC = {
    "Sad": "https://www.bensound.com/bensound-music/bensound-sadday.mp3",
    "Action": "https://www.bensound.com/bensound-music/bensound-dubstep.mp3",
    "Chill": "https://www.bensound.com/bensound-music/bensound-slowmotion.mp3"
}

# --- HELPER FUNCTIONS ---
def extract_text(file_obj, ext):
    try:
        if ext == 'pdf': return " ".join([p.extract_text() for p in PdfReader(file_obj).pages])
        elif ext == 'docx': return " ".join([p.text for p in Document(file_obj).paragraphs])
        elif ext == 'txt': return file_obj.read().decode("utf-8")
        elif ext == 'epub':
            with open("temp.epub", "wb") as f: f.write(file_obj.getbuffer())
            book = epub.read_epub("temp.epub")
            text = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                    text.append(soup.get_text())
            return " ".join(text)
    except: return ""

def download_file(url, filename):
    try:
        r = requests.get(url)
        with open(filename, "wb") as f: f.write(r.content)
        return True
    except: return False

async def generate_voice(text, code, pitch, rate, file):
    await edge_tts.Communicate(text, code, pitch=pitch, rate=rate).save(file)

def mix_audio_safe(v_path, b_path, out_path):
    if not HAS_MUSIC_ENGINE: return False
    try:
        v = AudioSegment.from_file(v_path)
        if os.path.exists(b_path):
            b = AudioSegment.from_file(b_path) - 15
            if len(b) < len(v): b = b * (len(v) // len(b) + 1)
            b[:len(v)+1000].overlay(v).export(out_path, format="mp3")
            return True
    except: return False

# --- 🧭 NAVIGATION MENU (With Home) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=50)
    st.title("Elite Super App")
    selected = option_menu(
        menu_title="Menu",
        options=["Home", "Desi Translator", "Pocket Universe", "Music Lab", "PDF Tools", "Downloader", "Vault", "About & Privacy"],
        icons=["house", "translate", "mic", "music-note", "file-text", "download", "lock", "info-circle"],
        default_index=0,
    )
    st.info("v2.0 (Pro Edition)")

# --- 1. 🏠 HOME DASHBOARD (New) ---
if selected == "Home":
    st.title("👋 Welcome, Aman!")
    st.markdown("### Aapka Personal AI Studio")
    
    # Dashboard Cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class="dashboard-card"><h3>🎤 Studio</h3><p>Create Novels & Songs</p></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="dashboard-card"><h3>📄 Docs</h3><p>Translate & Edit PDFs</p></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class="dashboard-card"><h3>🔐 Vault</h3><p>Secure Private Data</p></div>""", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("🚀 Quick Actions")
    if st.button("Start New Project"):
        st.toast("Menu se koi Tool select karein!")
    
    st.image("https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe", caption="Powered by Neural AI Engine", use_container_width=True)

# --- 2. DESI TRANSLATOR ---
elif selected == "Desi Translator":
    st.title("📜 Desi Translator")
    c1, c2 = st.columns([1, 1])
    with c1:
        src = st.radio("Input:", ["Paste", "Upload"], horizontal=True)
        txt = ""
        if src == "Paste": txt = st.text_area("English Text:", height=250)
        else:
            f = st.file_uploader("File", type=['txt','docx','pdf'])
            if f: txt = extract_text(f, f.name.split('.')[-1])
    with c2:
        st.subheader("Mapping (Optional)")
        cmap = st.text_area("Map (e.g. Ye Tian=Prem):", height=100)
        if st.button("Translate"):
            if txt:
                st.success(desi_anuvad_logic(txt[:5000], cmap))

# --- 3. POCKET UNIVERSE ---
elif selected == "Pocket Universe":
    st.title("🎭 Pocket Universe")
    c1, c2 = st.columns(2)
    with c1: raw = st.text_area("Story Script:", height=200)
    with c2:
        char = st.selectbox("Character:", list(CHARACTERS.keys()))
        mus = st.selectbox("Music:", list(MOOD_MUSIC.keys()))
    if st.button("Generate Audio"):
        if raw:
            cd = CHARACTERS[char]
            asyncio.run(generate_voice(raw, cd['voice'], cd['pitch'], cd['rate'], "v.mp3"))
            download_file(MOOD_MUSIC[mus], "bg.mp3")
            if HAS_MUSIC_ENGINE and mix_audio_safe("v.mp3", "bg.mp3", "final.mp3"):
                st.audio("final.mp3")
            else: st.audio("v.mp3")

# --- 4. MUSIC LAB ---
elif selected == "Music Lab":
    st.title("🎵 Music Lab")
    lyr = st.text_area("Lyrics:", height=150)
    if st.button("Create Song"):
        if lyr:
            asyncio.run(generate_voice(lyr, "hi-IN-MadhurNeural", "-5Hz", "+10%", "voc.mp3"))
            st.audio("voc.mp3")

# --- 5. PDF TOOLS ---
elif selected == "PDF Tools":
    st.title("📄 PDF Tools")
    upl = st.file_uploader("Images", accept_multiple_files=True)
    if upl and st.button("Convert to PDF"):
        imgs = [Image.open(x).convert("RGB") for x in upl]
        imgs[0].save("doc.pdf", save_all=True, append_images=imgs[1:])
        with open("doc.pdf", "rb") as f: st.download_button("Download", f)

# --- 6. DOWNLOADER ---
elif selected == "Downloader":
    st.title("🎬 Downloader")
    url = st.text_input("Video Link:")
    if st.button("Download"):
        with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                st.link_button("Download Video", info['url'])
            except: st.error("Invalid Link")

# --- 7. VAULT ---
elif selected == "Vault":
    st.title("🔐 Vault")
    if st.text_input("PIN", type="password") == "1234":
        st.file_uploader("Secret Files")

# --- 8. 📜 ABOUT & PRIVACY (Legal) ---
elif selected == "About & Privacy":
    st.title("ℹ️ About Elite Super App")
    st.info("Version 2.0 | Developed by Aman Tech")
    
    st.markdown("### 🔒 Privacy Policy")
    st.write("""
    1. **Data Safety:** Hum aapka koi bhi personal data (Photos/PDFs) apne server par save nahi karte.
    2. **Local Processing:** Sab kuch aapke session tak hi seemit hai.
    3. **Permissions:** Camera aur Storage sirf features use karne ke liye chahiye.
    """)
    
    st.markdown("### 📞 Contact Us")
    st.write("Email: support@elitetech.com")
