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

# --- PAGE CONFIG (Sidebar collapsed rakha hai, par hum use nahi karenge) ---
st.set_page_config(page_title="Elite Super App", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# --- SESSION STATE (App ka Dimaag) ---
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Home"

def navigate_to(page):
    st.session_state.current_tab = page
    st.rerun()

# --- 🎨 CUSTOM CSS (No Sidebar, Pure App Feel) ---
st.markdown("""
    <style>
    /* 1. System UI Fixes */
    html, body {
        overscroll-behavior-y: none !important;
        overflow-y: auto !important;
        background-color: #0e1117;
    }
    
    /* 2. PURA STREAMLIT HEADER GAYAB (No Menu, No Code Option) */
    header, [data-testid="stHeader"], [data-testid="stToolbar"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }

    /* 3. Custom Top Bar (Back Button Area) */
    .top-nav-bar {
        background-color: #1e1e1e;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-bottom: 2px solid #00e676;
        display: flex;
        align-items: center;
    }

    /* 4. Mobile Padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
    }

    /* 5. Buttons Design */
    .stButton>button {
        width: 100%; border-radius: 12px; 
        background-color: #00e676; color: black; 
        font-weight: bold; border: none; padding: 12px;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.2);
    }
    
    /* 6. Dashboard Cards */
    .dashboard-card {
        background-color: #1e1e1e; padding: 20px; 
        border-radius: 15px; border: 1px solid #333; 
        text-align: center; margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
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

# --- 🚀 CUSTOM NAVIGATION BAR (Har page ke upar dikhega) ---
def render_header(title, show_back=True):
    c1, c2 = st.columns([1, 4])
    with c1:
        if show_back:
            if st.button("⬅️ Home", key=f"back_{title}"):
                navigate_to("Home")
        else:
            st.write("🚀") # Home icon
    with c2:
        st.markdown(f"### {title}")
    st.markdown("---")

# --- 1. 🏠 HOME DASHBOARD ---
if st.session_state.current_tab == "Home":
    st.title("👋 Hi Aman!")
    st.markdown("Select a Tool:")
    
    # Grid Layout for Dashboard
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""<div class="dashboard-card"><h3>🎤 Studio</h3><p>Story & Audio</p></div>""", unsafe_allow_html=True)
        if st.button("Open Studio", key="btn_studio"): navigate_to("Pocket Universe")
    with c2:
        st.markdown("""<div class="dashboard-card"><h3>📜 Translate</h3><p>Desi Anuvad</p></div>""", unsafe_allow_html=True)
        if st.button("Open Translator", key="btn_trans"): navigate_to("Desi Translator")
    
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("""<div class="dashboard-card"><h3>🎵 Music</h3><p>Rap & Songs</p></div>""", unsafe_allow_html=True)
        if st.button("Open Music", key="btn_music"): navigate_to("Music Lab")
    with c4:
        st.markdown("""<div class="dashboard-card"><h3>🎬 Video</h3><p>Downloader</p></div>""", unsafe_allow_html=True)
        if st.button("Open Downloader", key="btn_dl"): navigate_to("Downloader")

    st.write("---")
    # Extra Tools
    if st.button("🔐 Private Vault"): navigate_to("Vault")
    if st.button("📄 PDF Tools"): navigate_to("PDF Tools")

# --- 2. POCKET UNIVERSE ---
elif st.session_state.current_tab == "Pocket Universe":
    render_header("Pocket Studio") # Back button automatic aayega
    
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

# --- 3. DESI TRANSLATOR ---
elif st.session_state.current_tab == "Desi Translator":
    render_header("Desi Translator")
    
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

# --- 4. MUSIC LAB ---
elif st.session_state.current_tab == "Music Lab":
    render_header("Music Lab")
    lyr = st.text_area("Lyrics:", height=150)
    if st.button("Create Song"):
        if lyr:
            asyncio.run(generate_voice(lyr, "hi-IN-MadhurNeural", "-5Hz", "+10%", "voc.mp3"))
            st.audio("voc.mp3")

# --- 5. DOWNLOADER ---
elif st.session_state.current_tab == "Downloader":
    render_header("4K Downloader")
    url = st.text_input("Video Link:")
    if st.button("Download"):
        with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                st.link_button("Download Video", info['url'])
            except: st.error("Invalid Link")

# --- 6. VAULT ---
elif st.session_state.current_tab == "Vault":
    render_header("Secret Vault")
    if st.text_input("PIN", type="password") == "1234":
        st.file_uploader("Secret Files")

# --- 7. PDF TOOLS ---
elif st.session_state.current_tab == "PDF Tools":
    render_header("PDF Tools")
    upl = st.file_uploader("Images", accept_multiple_files=True)
    if upl and st.button("Convert to PDF"):
        imgs = [Image.open(x).convert("RGB") for x in upl]
        imgs[0].save("doc.pdf", save_all=True, append_images=imgs[1:])
        with open("doc.pdf", "rb") as f: st.download_button("Download", f)
