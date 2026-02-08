import streamlit as st
from streamlit_option_menu import option_menu
import asyncio
import edge_tts
import os
import requests
import yt_dlp
from io import BytesIO
from textblob import TextBlob # Sentiment Analysis ke liye

# --- SAFETY CHECK (Crash Rokne Ke Liye) ---
try:
    from pydub import AudioSegment
    HAS_MUSIC_ENGINE = True
except ImportError:
    HAS_MUSIC_ENGINE = False

# --- DOCUMENT TOOLS IMPORTS ---
from PyPDF2 import PdfReader, PdfMerger
from docx import Document
from PIL import Image
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

# --- Page Config ---
st.set_page_config(page_title="Elite Super App", page_icon="🚀", layout="wide")
st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 20px; background-color: #00e676; color: black; font-weight: bold;}
    header {visibility: hidden;}
    .css-1v0mbdj {margin-top: -50px;}
    </style>
    """, unsafe_allow_html=True)

# --- 🎭 CHARACTER & MUSIC LIBRARY ---
CHARACTERS = {
    "🔥 Thriller (Shiv)": {"voice": "ur-PK-SalmanNeural", "pitch": "-15Hz", "rate": "-5%", "desc": "Bhaari, Villain Awaaz"},
    "❤️ Romance (Viraj)": {"voice": "hi-IN-MadhurNeural", "pitch": "+5Hz", "rate": "+5%", "desc": "Lover Boy"},
    "👻 Horror (Bhoot)": {"voice": "hi-IN-SwaraNeural", "pitch": "-10Hz", "rate": "-20%", "desc": "Darawani, Goonjti hui"},
    "📜 Wisdom (Guruji)": {"voice": "ta-IN-ValluvarNeural", "pitch": "-10Hz", "rate": "-10%", "desc": "Bujurg, Gyaani"},
    "🤖 Sci-Fi (Jarvis)": {"voice": "en-US-ChristopherNeural", "pitch": "+0Hz", "rate": "+0%", "desc": "AI Assistant"},
    "🇮🇳 Standard Hindi (Swara)": {"voice": "hi-IN-SwaraNeural", "pitch": "+0Hz", "rate": "+0%", "desc": "Normal Kahani"}
}

MOOD_MUSIC = {
    "Sad": "https://www.bensound.com/bensound-music/bensound-sadday.mp3",
    "Happy": "https://www.bensound.com/bensound-music/bensound-ukulele.mp3",
    "Suspense": "https://www.bensound.com/bensound-music/bensound-epic.mp3",
    "Romantic": "https://www.bensound.com/bensound-music/bensound-love.mp3",
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

def analyze_sentiment(text):
    blob = TextBlob(text[:1000])
    p = blob.sentiment.polarity
    if p < -0.1: return "Sad"
    elif p > 0.3: return "Happy"
    elif "love" in text.lower(): return "Romantic"
    elif "kill" in text.lower() or "run" in text.lower(): return "Action"
    else: return "Chill"

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
    options=["Pocket FM Universe", "Music Lab", "PDF Tools", "Downloader", "Vault"],
    icons=["mic", "music-note-beamed", "file-earmark-text", "cloud-download", "lock"],
    default_index=0,
    orientation="horizontal",
)

# --- 1. POCKET FM UNIVERSE (Audiobook + Characters) ---
if selected == "Pocket FM Universe":
    st.title("🎭 Pocket FM Universe")
    st.caption("Shiv, Viraj, aur Bhoot ki awaaz mein Novel suno!")
    
    c1, c2 = st.columns(2)
    with c1:
        src = st.radio("Input:", ["Likhein (Text)", "Upload (File)"], horizontal=True)
        raw_text = ""
        if src == "Likhein (Text)":
            raw_text = st.text_area("Kahani:", height=200, placeholder="Ek andheri raat thi...")
        else:
            f = st.file_uploader("File (PDF, DOCX, EPUB)", type=['pdf','docx','epub','txt'])
            if f:
                ext = f.name.split('.')[-1]
                raw_text = extract_text(f, ext)
                st.success(f"File Loaded: {len(raw_text)} chars")

    with c2:
        char_name = st.selectbox("Character Chunein:", list(CHARACTERS.keys()))
        char_data = CHARACTERS[char_name]
        st.info(f"🎙️ **Style:** {char_data['desc']}")
        
        auto_dj = st.checkbox("🤖 Auto-DJ (Mood ke hisaab se music)", value=True)
        manual_music = "Chill"
        if not auto_dj:
            manual_music = st.selectbox("Music Select Karein:", list(MOOD_MUSIC.keys()))

    if st.button("✨ Create Episode"):
        if not raw_text: st.error("Content missing!")
        else:
            with st.spinner("Recording & Mixing..."):
                # 1. Voice
                safe_text = raw_text[:50000] # 50k Limit
                asyncio.run(generate_voice(safe_text, char_data['voice'], char_data['pitch'], char_data['rate'], "voice.mp3"))
                
                # 2. Music Logic
                mood = manual_music
                if auto_dj:
                    mood = analyze_sentiment(safe_text)
                    st.toast(f"Detected Mood: {mood}")
                
                download_file(MOOD_MUSIC[mood], "bg.mp3")
                
                # 3. Mixing
                final_file = "voice.mp3"
                if HAS_MUSIC_ENGINE and mix_audio_safe("voice.mp3", "bg.mp3", "episode.mp3", -18):
                    final_file = "episode.mp3"
                
                st.audio(final_file)
                with open(final_file, "rb") as f:
                    st.download_button("⬇️ Download Episode", f, file_name=f"{char_name}_Story.mp3")

# --- 2. MUSIC LAB (Rap/Song) ---
elif selected == "Music Lab":
    st.title("🎵 AI Rap & Song Lab")
    c1, c2 = st.columns(2)
    with c1:
        lyrics = st.text_area("Lyrics / Bol:", height=200, placeholder="Rap lyrics yahan likhein...")
    with c2:
        beat = st.selectbox("Beat Style:", list(MOOD_MUSIC.keys()))
        artist = st.radio("Artist Style:", ["Rapper (Fast)", "Poet (Slow)", "Singer (Normal)"])

    if st.button("💿 Create Song"):
        if not lyrics: st.error("Lyrics missing!")
        else:
            with st.spinner("Dropping the beat..."):
                # Voice logic based on artist
                voice = "hi-IN-MadhurNeural"
                rate, pitch = "+0%", "+0Hz"
                if artist == "Rapper (Fast)": rate, pitch = "+20%", "-5Hz"
                elif artist == "Poet (Slow)": voice, rate, pitch = "ur-PK-SalmanNeural", "-10%", "-5Hz"
                
                asyncio.run(generate_voice(lyrics, voice, pitch, rate, "vocals.mp3"))
                download_file(MOOD_MUSIC[beat], "beat.mp3")
                
                if HAS_MUSIC_ENGINE and mix_audio_safe("vocals.mp3", "beat.mp3", "song.mp3", -10):
                    st.audio("song.mp3")
                    with open("song.mp3", "rb") as f:
                        st.download_button("⬇️ Download Song", f, file_name="My_Track.mp3")
                else: st.warning("Mixing failed, playing vocals only."); st.audio("vocals.mp3")

# --- 3. PDF TOOLS ---
elif selected == "PDF Tools":
    st.title("📄 PDF Tools")
    t1, t2 = st.tabs(["Image to PDF", "Merge PDF"])
    with t1:
        imgs = st.file_uploader("Images", accept_multiple_files=True, type=['png','jpg'])
        if imgs and st.button("Convert"):
            images = [Image.open(x).convert("RGB") for x in imgs]
            images[0].save("photos.pdf", save_all=True, append_images=images[1:])
            with open("photos.pdf", "rb") as f: st.download_button("Download PDF", f)
    with t2:
        pdfs = st.file_uploader("PDFs", accept_multiple_files=True, type='pdf')
        if pdfs and st.button("Merge"):
            m = PdfMerger()
            for p in pdfs: m.append(p)
            m.write("merged.pdf")
            with open("merged.pdf", "rb") as f: st.download_button("Download Merged", f)

# --- 4. DOWNLOADER ---
elif selected == "Downloader":
    st.title("🎬 4K Downloader")
    url = st.text_input("Link:")
    if st.button("Download"):
        with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                st.link_button("Download Video", info['url'])
            except: st.error("Invalid Link")

# --- 5. VAULT ---
elif selected == "Vault":
    st.title("🔐 Vault")
    if st.text_input("PIN", type="password") == "1234":
        st.success("Unlocked")
        st.file_uploader("Hide Files")
