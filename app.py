import streamlit as st
from streamlit_option_menu import option_menu
import asyncio
import edge_tts
import os
import requests
import yt_dlp
from textblob import TextBlob

# --- SAFETY IMPORTS (App Crash Rokne Ke Liye) ---
try:
    from pydub import AudioSegment
    HAS_MUSIC_ENGINE = True
except ImportError:
    HAS_MUSIC_ENGINE = False
    print("Music Engine (Pydub) load nahi hua.")

# --- Page Config ---
st.set_page_config(page_title="Elite Studio Safe", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 20px; background-color: #00e676; color: black; font-weight: bold;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 🥁 BEAT LIBRARY ---
BEATS = {
    "🔥 Hip Hop": "https://www.bensound.com/bensound-music/bensound-dubstep.mp3",
    "🎹 Sad Piano": "https://www.bensound.com/bensound-music/bensound-sadday.mp3"
}

# --- HELPER FUNCTIONS ---
def download_file(url, filename):
    try:
        response = requests.get(url, timeout=10)
        with open(filename, "wb") as f: f.write(response.content)
        return True
    except: return False

async def generate_voice(text, output_file):
    # Default Voice: Hindi Male
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural")
    await communicate.save(output_file)

def mix_audio_safe(voice_path, beat_path, output_path):
    if not HAS_MUSIC_ENGINE:
        st.warning("⚠️ Music Engine (FFmpeg) missing. Sirf voice aayegi.")
        return False
    
    try:
        voice = AudioSegment.from_file(voice_path)
        if os.path.exists(beat_path):
            beat = AudioSegment.from_file(beat_path) - 10
            # Loop Beat
            if len(beat) < len(voice):
                beat = beat * (len(voice) // len(beat) + 1)
            final = beat[:len(voice)+1000].overlay(voice)
            final.export(output_path, format="mp3")
            return True
    except Exception as e:
        st.error(f"Mixing Error: {e}")
        return False

# --- APP LAYOUT ---
selected = option_menu(
    menu_title=None,
    options=["Music Lab", "Downloader", "Vault"],
    icons=["music-note", "cloud-download", "lock"],
    default_index=0,
    orientation="horizontal",
)

# --- 1. MUSIC LAB ---
if selected == "Music Lab":
    st.title("🎵 AI Music Lab")
    col1, col2 = st.columns(2)
    
    with col1:
        lyrics = st.text_area("Lyrics:", height=150, placeholder="Kuch likhein...")
    with col2:
        beat_name = st.selectbox("Beat:", list(BEATS.keys()))
    
    if st.button("Create Song"):
        if not lyrics: st.error("Lyrics missing!")
        else:
            with st.spinner("Processing..."):
                asyncio.run(generate_voice(lyrics, "vocals.mp3"))
                
                # Music Mixing Attempt
                beat_url = BEATS[beat_name]
                download_file(beat_url, "beat.mp3")
                
                if HAS_MUSIC_ENGINE:
                    success = mix_audio_safe("vocals.mp3", "beat.mp3", "final.mp3")
                    file_to_play = "final.mp3" if success else "vocals.mp3"
                else:
                    file_to_play = "vocals.mp3"
                
                st.audio(file_to_play)

# --- 2. DOWNLOADER ---
elif selected == "Downloader":
    st.title("🎬 Downloader")
    url = st.text_input("Link:")
    if st.button("Download"):
        with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                st.link_button("Download", info['url'])
            except: st.error("Invalid Link")

# --- 3. VAULT ---
elif selected == "Vault":
    st.title("🔐 Vault")
    st.info("Files are safe here.")
    st.file_uploader("Upload")
