import streamlit as st
from streamlit_option_menu import option_menu
import asyncio
import edge_tts
import os
from pydub import AudioSegment
from PyPDF2 import PdfReader
from docx import Document
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from textblob import TextBlob
import requests
import yt_dlp

# --- Page Config & Hide Menu ---
st.set_page_config(page_title="EliteVault Studio", page_icon="🎙️", layout="wide")

st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 20px; background-color: #00e676; color: black; font-weight: bold;}
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1rem;}
    </style>
    """, unsafe_allow_html=True)

# --- 🎵 ONLINE MUSIC LIBRARY (Royalty Free) ---
MOOD_MUSIC = {
    "Sad": "https://www.bensound.com/bensound-music/bensound-sadday.mp3",
    "Happy": "https://www.bensound.com/bensound-music/bensound-ukulele.mp3",
    "Suspense": "https://www.bensound.com/bensound-music/bensound-epic.mp3",
    "Romantic": "https://www.bensound.com/bensound-music/bensound-love.mp3",
    "Chill": "https://www.bensound.com/bensound-music/bensound-slowmotion.mp3"
}

# --- HELPER FUNCTIONS (Yahan galti thi, ab sahi hai) ---

def extract_text_from_epub(epub_path):
    try:
        book = epub.read_epub(epub_path)
        text = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                text.append(soup.get_text())
        return " ".join(text) # Ye line ab sahi jagah hai
    except: return ""

def extract_text_from_docx(docx_path):
    try:
        doc = Document(docx_path)
        return " ".join([para.text for para in doc.paragraphs])
    except: return ""

def analyze_sentiment(text):
    """Text ka mood pehchanta hai"""
    blob = TextBlob(text[:2000]) # Shuruwat padh kar mood batayega
    polarity = blob.sentiment.polarity
    if polarity < -0.2: return "Sad"
    elif polarity > 0.4: return "Happy"
    elif "love" in text.lower(): return "Romantic"
    elif "kill" in text.lower() or "gun" in text.lower(): return "Suspense"
    else: return "Chill"

def download_music(url, filename):
    response = requests.get(url)
    with open(filename, "wb") as f:
        f.write(response.content)

async def generate_tts(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def mix_audio(voice_file, music_file, output_file):
    voice = AudioSegment.from_file(voice_file)
    music = AudioSegment.from_file(music_file)
    
    # Music Volume Low (-20dB)
    music = music - 18
    
    # Loop Music to match Voice length
    if len(music) < len(voice):
        loops = len(voice) // len(music) + 1
        music = music * loops
    
    # Trim & Overlay
    music = music[:len(voice)]
    final = voice.overlay(music)
    final.export(output_file, format="mp3")

# --- APP LAYOUT ---
selected = option_menu(
    menu_title=None,
    options=["Pocket Studio", "Downloader", "Vault"],
    icons=["mic", "cloud-download", "lock"],
    default_index=0,
    orientation="horizontal",
)

# --- 1. POCKET STUDIO (Combined Features) ---
if selected == "Pocket Studio":
    st.title("🎙️ Pocket FM Maker (Auto-DJ)")
    st.caption("Upload Novel/PDF -> Get Audio with Music")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        input_type = st.radio("Input Source:", ["Paste Text", "Upload File (PDF/EPUB/DOCX)"], horizontal=True)
        raw_text = ""
        
        if input_type == "Paste Text":
            raw_text = st.text_area("Story text here...", height=300)
        else:
            uploaded_file = st.file_uploader("Select Book", type=['pdf', 'docx', 'epub', 'txt'])
            if uploaded_file:
                if uploaded_file.name.endswith('.pdf'):
                    reader = PdfReader(uploaded_file)
                    raw_text = " ".join([page.extract_text() for page in reader.pages])
                elif uploaded_file.name.endswith('.docx'):
                    raw_text = extract_text_from_docx(uploaded_file)
                elif uploaded_file.name.endswith('.epub'):
                    with open("temp.epub", "wb") as f: f.write(uploaded_file.getbuffer())
                    raw_text = extract_text_from_epub("temp.epub")
                elif uploaded_file.name.endswith('.txt'):
                    raw_text = uploaded_file.read().decode("utf-8")
                st.success(f"File Loaded: {len(raw_text)} chars")

    with col2:
        st.subheader("⚙️ Audio Settings")
        voices = {
            "🇮🇳 Hindi Male (Madhur)": "hi-IN-MadhurNeural",
            "🇮🇳 Hindi Female (Swara)": "hi-IN-SwaraNeural",
            "🇮🇳 English Male (Prabhat)": "en-IN-PrabhatNeural",
            "🇮🇳 English Female (Neerja)": "en-IN-NeerjaNeural"
        }
        selected_voice = st.selectbox("Narrator:", list(voices.keys()))
        auto_mode = st.checkbox("🤖 Auto-Detect Background Music", value=True)
        
        manual_mood = "Chill"
        if not auto_mode:
            manual_mood = st.selectbox("Select Music Mood:", list(MOOD_MUSIC.keys()))

    if st.button("✨ Create Audiobook"):
        if not raw_text:
            st.error("Text missing!")
        else:
            progress = st.progress(0)
            status = st.empty()
            try:
                # 1. Generate Voice (Chunking 50k chars for safety)
                status.text("🗣️ Generating Voiceover...")
                voice_code = voices[selected_voice]
                # Processing first 50,000 chars to avoid timeout in free cloud
                safe_text = raw_text[:50000] 
                asyncio.run(generate_tts(safe_text, voice_code, "voice.mp3"))
                progress.progress(40)
                
                # 2. Music Logic
                mood = manual_mood
                if auto_mode:
                    status.text("🧠 Analyzing Story Mood...")
                    mood = analyze_sentiment(safe_text)
                    st.info(f"Detected Scene Mood: **{mood}**")
                
                # 3. Mixing
                status.text(f"🎵 Mixing {mood} Music...")
                music_url = MOOD_MUSIC[mood]
                download_music(music_url, "bg_music.mp3")
                mix_audio("voice.mp3", "bg_music.mp3", "final_story.mp3")
                
                progress.progress(100)
                status.success("✅ Audiobook Ready!")
                st.audio("final_story.mp3")
                with open("final_story.mp3", "rb") as f:
                    st.download_button("⬇️ Download MP3", f, file_name="My_Story.mp3")
            except Exception as e:
                st.error(f"Error: {e}")

# --- 2. DOWNLOADER ---
elif selected == "Downloader":
    st.title("🎬 4K Downloader")
    url = st.text_input("Link:")
    if st.button("Process"):
        try:
            with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
                info = ydl.extract_info(url, download=False)
                st.image(info['thumbnail'])
                st.link_button("Download", info['url'])
        except: st.error("Invalid Link")

# --- 3. VAULT ---
elif selected == "Vault":
    st.title("🔐 Vault")
    if st.text_input("PIN", type="password") == "1234":
        st.success("Unlocked")
        st.file_uploader("Files", accept_multiple_files=True)
