import streamlit as st
import sys
import os

# --- SAFETY BLOCK (Ye App ko Crash hone se bachayega) ---
try:
    import pyaudioop
    sys.modules['audioop'] = pyaudioop
except ImportError:
    pass  # Agar tool nahi mila toh bhi app chalta rahega

# --- Baki Imports ---
from streamlit_option_menu import option_menu
import asyncio
import edge_tts
from pydub import AudioSegment
from PyPDF2 import PdfReader
from docx import Document
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from textblob import TextBlob
import requests
import yt_dlp

# --- Page Config ---
st.set_page_config(page_title="Elite Studio AI", page_icon="🎛️", layout="wide")

st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 20px; background-color: #ff4b4b; color: white; font-weight: bold;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 🥁 BEAT LIBRARY ---
BEATS = {
    "🔥 Hip Hop": "https://www.bensound.com/bensound-music/bensound-dubstep.mp3",
    "🎹 Sad Piano": "https://www.bensound.com/bensound-music/bensound-sadday.mp3",
    "🎸 Romantic": "https://www.bensound.com/bensound-music/bensound-love.mp3",
    "⚡ Action": "https://www.bensound.com/bensound-music/bensound-evolution.mp3"
}

# --- 🎤 ARTIST VOICES ---
ARTISTS = {
    "YoYo (Rapper)": {"voice": "hi-IN-MadhurNeural", "rate": "+20%", "pitch": "-5Hz"},
    "Gulzar (Poet)": {"voice": "ur-PK-SalmanNeural", "rate": "-15%", "pitch": "-10Hz"},
    "Simran (Singer)": {"voice": "hi-IN-SwaraNeural", "rate": "+0%", "pitch": "+5Hz"}
}

# --- HELPER FUNCTIONS ---
def download_file(url, filename):
    try:
        response = requests.get(url, timeout=10)
        with open(filename, "wb") as f: f.write(response.content)
        return True
    except: return False

async def generate_vocals(text, artist, output_file):
    try:
        data = ARTISTS[artist]
        communicate = edge_tts.Communicate(text, data['voice'], rate=data['rate'], pitch=data['pitch'])
        await communicate.save(output_file)
    except Exception as e: st.error(f"Voice Error: {e}")

def mix_song(vocals_path, beat_path, output_path):
    try:
        vocals = AudioSegment.from_file(vocals_path)
        if os.path.exists(beat_path):
            beat = AudioSegment.from_file(beat_path) - 10
            # Loop Beat
            if len(beat) < len(vocals):
                beat = beat * (len(vocals) // len(beat) + 1)
            final = beat[:len(vocals)+2000].overlay(vocals, position=500)
            final.export(output_path, format="mp3")
        else:
            vocals.export(output_path, format="mp3")
    except Exception as e: st.error(f"Mixing Error: {e}")

# --- APP NAVIGATION ---
selected = option_menu(
    menu_title=None,
    options=["Music Lab", "Pocket FM", "Downloader", "Vault"],
    icons=["music-note-list", "mic", "cloud-download", "lock"],
    default_index=0,
    orientation="horizontal",
)

# --- 1. MUSIC LAB ---
if selected == "Music Lab":
    st.title("🎵 AI Music Studio")
    col1, col2 = st.columns(2)
    
    with col1:
        lyrics = st.text_area("Lyrics / Bol:", height=200, placeholder="Likho apni rap ya shayari...")
    with col2:
        beat = st.selectbox("Beat Style:", list(BEATS.keys()))
        artist = st.radio("Artist:", list(ARTISTS.keys()))

    if st.button("💿 Create Song"):
        if not lyrics: st.error("Lyrics missing!")
        else:
            with st.spinner("Recording..."):
                asyncio.run(generate_vocals(lyrics, artist, "vocals.mp3"))
                if download_file(BEATS[beat], "beat.mp3"):
                    mix_song("vocals.mp3", "beat.mp3", "final_song.mp3")
                    st.audio("final_song.mp3")
                    with open("final_song.mp3", "rb") as f:
                        st.download_button("⬇️ Download Song", f, file_name="My_Song.mp3")

# --- 2. POCKET FM (Short Version) ---
elif selected == "Pocket FM":
    st.title("🎙️ Pocket FM Story")
    text = st.text_area("Story Text:", height=150)
    if st.button("Generate Story Audio"):
        asyncio.run(generate_vocals(text, "Gulzar (Poet)", "story.mp3"))
        st.audio("story.mp3")

# --- 3. DOWNLOADER ---
elif selected == "Downloader":
    st.title("🎬 Downloader")
    url = st.text_input("Link:")
    if st.button("Download"):
        with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                st.link_button("Download Video", info['url'])
            except: st.error("Invalid Link")

# --- 4. VAULT ---
elif selected == "Vault":
    st.title("🔐 Vault")
    if st.text_input("PIN", type="password") == "1234":
        st.file_uploader("Secret Files")
