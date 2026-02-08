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
st.set_page_config(page_title="Elite Super App", page_icon="🔥", layout="wide")
st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 20px; background-color: #00e676; color: black; font-weight: bold;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 🧠 DESI LOGIC (System Safe) ---
def desi_anuvad_logic(text, custom_map_text):
    # 1. Basic Translation (English -> Hindi)
    try:
        translated = GoogleTranslator(source='auto', target='hi').translate(text)
    except:
        return "⚠️ Internet Error: Translation fail ho gaya."

    # 2. LOCATIONS & GENERIC TERMS (System Chhodkar)
    # Sirf Jagah aur Padvi (Rank) badlegi
    replacements = {
        # Locations (Jagah)
        "Sect": "अखाड़ा (Akhada)",
        "Peak": "चोटी (Pahadi)",
        "Realm": "लोक (Lok)",
        "Continent": "महाद्वीप (Mahadweep)",
        "City": "नगर (Nagar)",
        "Village": "गाँव (Gaon)",
        "Pavilion": "मंडप (Mandap)",
        
        # Ranks (Padvi) - Characters ke liye
        "Patriarch": "मुखिया (Mukhiya)",
        "Elder": "दाऊ (Daau)",
        "Disciple": "चेला (Chela)",
        "Master": "गुरुजी (Guruji)",
        
        # NOTE: "System" ko list se hata diya hai, wo System hi rahega.
    }
    
    # 3. CUSTOM CHARACTER MAPPING (User Input se)
    # Format: Original=New (e.g., Ye Tian=Yug)
    if custom_map_text:
        lines = custom_map_text.split('\n')
        for line in lines:
            if '=' in line:
                parts = line.split('=')
                original = parts[0].strip()
                new_name = parts[1].strip()
                # Pehle English naam replace karo
                text = text.replace(original, new_name) 
                # Phir agar Google ne translate kar diya ho toh wo bhi replace karo
                replacements[original] = new_name

    # Apply Replacements on Hindi Text
    for word, desi_word in replacements.items():
        translated = translated.replace(word, desi_word)

    # 4. DIALECT (Halka Desi Touch)
    desi_tadka = {
        "मैं ": "हम ",
        "तुम ": "तोरा ",
        "क्यों": "काये",
        "वहाँ": "उते",
        "यहाँ": "इते",
        "लड़का": "मोरा",
        "लड़की": "मोरिया"
    }
    for hindi, desi in desi_tadka.items():
        translated = translated.replace(hindi, desi)

    return translated

# --- 🎭 RESOURCES ---
CHARACTERS = {
    "🔥 Thriller (Shiv)": {"voice": "ur-PK-SalmanNeural", "pitch": "-15Hz", "rate": "-5%", "desc": "Bhaari, Villain Awaaz"},
    "❤️ Romance (Viraj)": {"voice": "hi-IN-MadhurNeural", "pitch": "+5Hz", "rate": "+5%", "desc": "Lover Boy"},
    "👻 Horror (Bhoot)": {"voice": "hi-IN-SwaraNeural", "pitch": "-10Hz", "rate": "-20%", "desc": "Darawani, Goonjti hui"}
}

MOOD_MUSIC = {
    "Sad": "https://www.bensound.com/bensound-music/bensound-sadday.mp3",
    "Suspense": "https://www.bensound.com/bensound-music/bensound-epic.mp3",
    "Action": "https://www.bensound.com/bensound-music/bensound-dubstep.mp3",
    "Chill": "https://www.bensound.com/bensound-music/bensound-slowmotion.mp3"
}

# --- 🛠️ HELPER FUNCTIONS ---
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

async def generate_voice(text, voice_code, pitch, rate, output_file):
    communicate = edge_tts.Communicate(text, voice_code, pitch=pitch, rate=rate)
    await communicate.save(output_file)

def mix_audio_safe(voice_path, beat_path, output_path, vol_adj=-15):
    if not HAS_MUSIC_ENGINE: return False
    try:
        voice = AudioSegment.from_file(voice_path)
        if os.path.exists(beat_path):
            beat = AudioSegment.from_file(beat_path) + vol_adj
            if len(beat) < len(voice):
                beat = beat * (len(voice) // len(beat) + 1)
            final = beat[:len(voice)+1000].overlay(voice)
            final.export(output_path, format="mp3")
            return True
    except: return False

# --- 🧭 NAVIGATION ---
selected = option_menu(
    menu_title=None,
    options=["Desi Translator", "Pocket Universe", "Music Lab", "PDF Tools", "Downloader", "Vault"],
    icons=["translate", "mic", "music-note-beamed", "file-text", "cloud-download", "lock"],
    default_index=0,
    orientation="horizontal",
)

# --- 1. 📜 DESI TRANSLATOR (System Safe) ---
if selected == "Desi Translator":
    st.title("📜 Desi Translator (System Safe)")
    
    c1, c2 = st.columns([1, 1])
    
    with c1:
        src_type = st.radio("Input Source:", ["Text Paste", "File Upload"], horizontal=True)
        input_text = ""
        if src_type == "Text Paste":
            input_text = st.text_area("English Text:", height=300, placeholder="Example: The System activated...")
        else:
            f = st.file_uploader("Upload Novel", type=['txt', 'docx', 'pdf'])
            if f:
                ext = f.name.split('.')[-1]
                input_text = extract_text(f, ext)
                st.success(f"Loaded: {len(input_text)} chars")

    with c2:
        st.subheader("🛠️ Name Changer (Mapping)")
        st.caption("Format: OriginalName=NewName (Har line mein ek)")
        custom_map = st.text_area("Character/Location Map:", height=150, 
            placeholder="Ye Tian = Yug\nBeijing = Banaras\nSect = Akhada\n(Note: 'System' change nahi hoga)")
        
        if st.button("🚀 Translate Now"):
            if not input_text: st.error("Text missing!")
            else:
                with st.spinner("Translating..."):
                    desi_out = desi_anuvad_logic(input_text[:5000], custom_map)
                    
                    st.markdown("### **📖 Translated Output:**")
                    st.success(desi_out)
                    st.download_button("⬇️ Download Text", desi_out, file_name="Desi_Novel.txt")

# --- 2. POCKET UNIVERSE ---
elif selected == "Pocket Universe":
    st.title("🎭 Pocket FM Universe")
    c1, c2 = st.columns(2)
    with c1: raw_text = st.text_area("Script:", height=200)
    with c2:
        char = st.selectbox("Character:", list(CHARACTERS.keys()))
        music = st.selectbox("Music:", list(MOOD_MUSIC.keys()))

    if st.button("✨ Create Audio"):
        if raw_text:
            cd = CHARACTERS[char]
            asyncio.run(generate_voice(raw_text, cd['voice'], cd['pitch'], cd['rate'], "v.mp3"))
            download_file(MOOD_MUSIC[music], "bg.mp3")
            if HAS_MUSIC_ENGINE and mix_audio_safe("v.mp3", "bg.mp3", "final.mp3"):
                st.audio("final.mp3")
            else: st.audio("v.mp3")

# --- 3. MUSIC LAB ---
elif selected == "Music Lab":
    st.title("🎵 AI Music Lab")
    lyrics = st.text_area("Lyrics:", height=150)
    if st.button("Make Song"):
        if lyrics:
            asyncio.run(generate_voice(lyrics, "hi-IN-MadhurNeural", "-5Hz", "+10%", "voc.mp3"))
            st.audio("voc.mp3")

# --- 4. PDF TOOLS ---
elif selected == "PDF Tools":
    st.title("📄 PDF Tools")
    upl = st.file_uploader("Images", accept_multiple_files=True)
    if upl and st.button("Convert"):
        imgs = [Image.open(x).convert("RGB") for x in upl]
        imgs[0].save("doc.pdf", save_all=True, append_images=imgs[1:])
        with open("doc.pdf", "rb") as f: st.download_button("Download", f)

# --- 5. DOWNLOADER ---
elif selected == "Downloader":
    st.title("🎬 Downloader")
    url = st.text_input("Link:")
    if st.button("Download"):
        with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                st.link_button("Download", info['url'])
            except: st.error("Invalid")

# --- 6. VAULT ---
elif selected == "Vault":
    st.title("🔐 Vault")
    if st.text_input("PIN", type="password") == "1234":
        st.file_uploader("Files")
