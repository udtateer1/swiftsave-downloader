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

# --- Page Config ---
st.set_page_config(page_title="Elite Super App", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# --- SESSION STATE (Navigation Logic) ---
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Home"

def navigate_to(tab_name):
    st.session_state.current_tab = tab_name
    st.rerun()

# --- 🎨 CUSTOM CSS (Menu ON, Code Option OFF) ---
st.markdown("""
    <style>
    /* 1. Scroll Control */
    html, body {
        overscroll-behavior-y: none !important;
        overflow-y: auto !important;
    }
    
    /* 2. HEADER MAGIC (Sabse Zaroori) */
    /* Header ko dikhao (Sidebar button ke liye) */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* SIRF Right Side wala Toolbar (Manage App, Github, Settings) GAYAB karo */
    [data-testid="stToolbar"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }

    /* Top ki colored line bhi hatao */
    [data-testid="stDecoration"] {
        display: none !important;
    }

    /* 3. Mobile Optimization */
    .block-container {
        padding-top: 3rem !important; /* Button ke liye jagah */
        padding-bottom: 5rem !important;
    }

    /* 4. Buttons Design */
    .stButton>button {
        width: 100%; border-radius: 12px; 
        background-color: #00e676; color: black; 
        font-weight: bold; border: none; padding: 12px;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.2);
    }
    
    /* 5. Card Hover Effect */
    .dashboard-card {
        background-color: #1e1e1e; padding: 15px; 
        border-radius: 15px; border: 1px solid #333; 
        text-align: center; margin-bottom: 10px;
        transition: transform 0.2s;
    }
    .dashboard-card:hover {
        transform: scale(1.02);
        border-color: #00e676;
    }
    </style>
    """, unsafe_allow_html=True)

# --- RESOURCES ---
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

def desi_anuvad_logic(text, custom_map_text):
    try: translated = GoogleTranslator(source='auto', target='hi').translate(text)
    except: return "⚠️ Net Error"
    replacements = {"Sect": "अखाड़ा", "Peak": "चोटी", "Realm": "लोक", "City": "नगर"}
    if custom_map_text:
        for line in custom_map_text.split('\n'):
            if '=' in line:
                p = line.split('=')
                text = text.replace(p[0].strip(), p[1].strip())
                replacements[p[0].strip()] = p[1].strip()
    for w, d in replacements.items(): translated = translated.replace(w, d)
    return translated

# --- 🧭 SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=50)
    st.title("Elite Super App")
    
    selected = option_menu(
        menu_title="Main Menu",
        options=["Home", "Desi Translator", "Pocket Universe", "Music Lab", "PDF Tools", "Downloader", "Vault"],
        icons=["house", "translate", "mic", "music-note", "file-text", "download", "lock"],
        default_index=0 if st.session_state.current_tab == "Home" else \
                      1 if st.session_state.current_tab == "Desi Translator" else \
                      2 if st.session_state.current_tab == "Pocket Universe" else \
                      3 if st.session_state.current_tab == "Music Lab" else \
                      4 if st.session_state.current_tab == "PDF Tools" else \
                      5 if st.session_state.current_tab == "Downloader" else 6,
    )
    
    if selected != st.session_state.current_tab:
        st.session_state.current_tab = selected
        st.rerun()

# --- 1. 🏠 HOME ---
if st.session_state.current_tab == "Home":
    st.title("👋 Welcome, Aman!")
    st.caption("Aapka Personal AI Studio")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""<div class="dashboard-card"><h3>🎤 Studio</h3><p>Story & Audio</p></div>""", unsafe_allow_html=True)
        if st.button("Open Studio", key="btn_studio"): navigate_to("Pocket Universe")
    with c2:
        st.markdown("""<div class="dashboard-card"><h3>📜 Translator</h3><p>Desi Anuvad</p></div>""", unsafe_allow_html=True)
        if st.button("Open Translator", key="btn_trans"): navigate_to("Desi Translator")
    
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("""<div class="dashboard-card"><h3>🎵 Music</h3><p>Create Songs</p></div>""", unsafe_allow_html=True)
        if st.button("Open Music Lab", key="btn_music"): navigate_to("Music Lab")
    with c4:
        st.markdown("""<div class="dashboard-card"><h3>🔐 Vault</h3><p>Secure Files</p></div>""", unsafe_allow_html=True)
        if st.button("Open Vault", key="btn_vault"): navigate_to("Vault")

    st.write("---")
    st.caption("Tip: Use the arrow (>) at the top-left to open the full menu.")

# --- 2. TRANSLATOR ---
elif st.session_state.current_tab == "Desi Translator":
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
        cmap = st.text_area("Name Mapping (e.g. Ye=Prem):", height=100)
        if st.button("Translate"):
            if txt: st.success(desi_anuvad_logic(txt[:5000], cmap))
    if st.button("⬅️ Back to Home"): navigate_to("Home")

# --- 3. POCKET UNIVERSE ---
elif st.session_state.current_tab == "Pocket Universe":
    st.title("🎭 Pocket Universe")
    c1, c2 = st.columns(2)
    with c1: raw = st.text_area("Story Script:", height=200)
    with c2:
        char = st.selectbox("Character:", list(CHARACTERS.keys()))
        mus = st.selectbox("Music:", list(MOOD_MUSIC.keys()))
