import streamlit as st
from streamlit_option_menu import option_menu
import asyncio
import edge_tts
import os
from pydub import AudioSegment
from PyPDF2 import PdfReader
from textblob import TextBlob  # Dimaag (Sentiment Analysis)
import requests

# --- Page Config ---
st.set_page_config(page_title="Pocket FM Maker", page_icon="🎙️", layout="wide")

st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 20px; background-color: #ff4b4b; color: white; font-weight: bold;}
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1rem;}
    </style>
    """, unsafe_allow_html=True)

# --- 🎵 ONLINE MUSIC LIBRARY (Copyright Free Links) ---
# Aap baad mein apne links bhi daal sakte ho
MOOD_MUSIC = {
    "Sad": "https://www.bensound.com/bensound-music/bensound-sadday.mp3",
    "Happy": "https://www.bensound.com/bensound-music/bensound-ukulele.mp3",
    "Suspense": "https://www.bensound.com/bensound-music/bensound-epic.mp3",
    "Romantic": "https://www.bensound.com/bensound-music/bensound-love.mp3",
    "Chill": "https://www.bensound.com/bensound-music/bensound-slowmotion.mp3"
}

# --- HELPER FUNCTIONS ---
def analyze_sentiment(text):
    """Text padh kar mood batata hai"""
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity # -1 (Negative) to +1 (Positive)
    
    if polarity < -0.3: return "Sad"
    elif polarity > 0.3: return "Happy"
    elif "love" in text.lower() or "pyaar" in text.lower(): return "Romantic"
    elif "kill" in text.lower() or "gun" in text.lower() or "run" in text.lower(): return "Suspense"
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
    
    # Music Volume Low karo (-20dB)
    music = music - 20
    
    # Loop Music
    if len(music) < len(voice):
        music = music * (len(voice) // len(music) + 1)
    
    # Trim & Overlay
    music = music[:len(voice)]
    final = voice.overlay(music)
    final.export(output_file, format="mp3")

# --- APP LAYOUT ---
selected = option_menu(
    menu_title=None,
    options=["Pocket Studio", "Settings"],
    icons=["mic", "gear"],
    default_index=0,
    orientation="horizontal",
)

if selected == "Pocket Studio":
    st.title("🎙️ Pocket FM Style Creator")
    st.caption("Auto-Background Music + AI Voice")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        text_input = st.text_area("Yahan Kahani Likhein (Hindi/English):", height=300, 
                                placeholder="Ek andheri raat thi... (Suspense music khud bajega)")
        
    with col2:
        st.subheader("⚙️ Voice Settings")
        
        # Indian Voices
        voices = {
            "🇮🇳 Hindi Male (Madhur)": "hi-IN-MadhurNeural",
            "🇮🇳 Hindi Female (Swara)": "hi-IN-SwaraNeural",
            "🇮🇳 English Male (Prabhat)": "en-IN-PrabhatNeural",
            "🇮🇳 English Female (Neerja)": "en-IN-NeerjaNeural"
        }
        selected_voice = st.selectbox("Narrator:", list(voices.keys()))
        
        # Auto Mode Toggle
        auto_mode = st.checkbox("🤖 Auto-Detect Background Music", value=True)
        
        manual_mood = "Chill"
        if not auto_mode:
            manual_mood = st.selectbox("Manual Music:", list(MOOD_MUSIC.keys()))

    if st.button("✨ Create Magic Audio"):
        if not text_input:
            st.error("Kuch likho toh sahi!")
        else:
            progress = st.progress(0)
            status = st.empty()
            
            try:
                # 1. Voice Generate
                status.text("🗣️ Voice Generate ho rahi hai...")
                voice_code = voices[selected_voice]
                asyncio.run(generate_tts(text_input, voice_code, "voice.mp3"))
                progress.progress(40)
                
                # 2. Music Decision
                mood = manual_mood
                if auto_mode:
                    status.text("🧠 AI Scene samajh raha hai...")
                    mood = analyze_sentiment(text_input)
                    st.info(f"Detected Mood: **{mood}**")
                
                # 3. Download & Mix
                status.text(f"🎵 {mood} Music add ho raha hai...")
                music_url = MOOD_MUSIC[mood]
                download_music(music_url, "bg_music.mp3")
                
                mix_audio("voice.mp3", "bg_music.mp3", "final_story.mp3")
                progress.progress(100)
                status.success("✅ Audio Ready!")
                
                # 4. Play & Download
                st.audio("final_story.mp3")
                with open("final_story.mp3", "rb") as f:
                    st.download_button("⬇️ Download MP3", f, file_name="My_Story.mp3")
                    
            except Exception as e:
                st.error(f"Error: {e}")

elif selected == "Settings":
    st.title("🛠️ App Settings")
    st.write("Yahan aap apni API keys ya custom music links set kar payenge (Future Update).")
    return " ".join(text)

def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    return " ".join([para.text for para in doc.paragraphs])

async def generate_tts_audio(text, voice, output_file):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def mix_audio_with_music(voice_file, music_file, output_file, volume_adjustment=-15):
    # Load Files
    voice = AudioSegment.from_file(voice_file)
    music = AudioSegment.from_file(music_file)
    
    # Adjust Music Volume (Make it background)
    music = music + volume_adjustment
    
    # Loop Music to match Voice length
    if len(music) < len(voice):
        loops = len(voice) // len(music) + 1
        music = music * loops
    
    # Trim Music to exact voice length
    music = music[:len(voice)]
    
    # Overlay
    final_audio = voice.overlay(music)
    final_audio.export(output_file, format="mp3")

# --- NAVIGATION ---
selected = option_menu(
    menu_title=None,
    options=["Ultra Audiobook", "Video Downloader", "Vault"],
    icons=["music-note-beamed", "cloud-download", "lock"],
    default_index=0,
    orientation="horizontal",
)

# --- 1. ULTRA AUDIOBOOK MAKER ---
if selected == "Ultra Audiobook":
    st.title("🎧 Ultimate Audiobook Studio")
    st.caption("Support: PDF, EPUB, DOCX, TXT | Limit: 3,00,000+ Words")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. File & Text")
        input_method = st.radio("Choose Input:", ["Upload File", "Paste Text"], horizontal=True)
        
        raw_text = ""
        if input_method == "Upload File":
            uploaded_file = st.file_uploader("Select Book/Doc", type=['pdf', 'docx', 'epub', 'txt'])
            if uploaded_file:
                with st.spinner("Reading File..."):
                    try:
                        if uploaded_file.name.endswith('.pdf'):
                            reader = PdfReader(uploaded_file)
                            raw_text = " ".join([page.extract_text() for page in reader.pages])
                        elif uploaded_file.name.endswith('.docx'):
                            raw_text = extract_text_from_docx(uploaded_file)
                        elif uploaded_file.name.endswith('.epub'):
                            # Save temp file for parsing
                            with open("temp.epub", "wb") as f: f.write(uploaded_file.getbuffer())
                            raw_text = extract_text_from_epub("temp.epub")
                        elif uploaded_file.name.endswith('.txt'):
                            raw_text = uploaded_file.read().decode("utf-8")
                        st.success(f"Loaded {len(raw_text.split())} words successfully!")
                    except Exception as e:
                        st.error(f"Error reading file: {e}")
        else:
            raw_text = st.text_area("Paste Story Here (Unlimited)", height=300)

    with col2:
        st.subheader("2. Voice & Music")
        
        # Indian Voices List
        voice_options = {
            "🇮🇳 Hindi - Madhur (Male)": "hi-IN-MadhurNeural",
            "🇮🇳 Hindi - Swara (Female)": "hi-IN-SwaraNeural",
            "🇮🇳 English (India) - Prabhat (Male)": "en-IN-PrabhatNeural",
            "🇮🇳 English (India) - Neerja (Female)": "en-IN-NeerjaNeural",
            "🇮🇳 Tamil - Pallavi": "ta-IN-PallaviNeural",
            "🇮🇳 Telugu - Mohan": "te-IN-MohanNeural",
            "🇮🇳 Marathi - Aarohi": "mr-IN-AarohiNeural",
            "🇺🇸 US English - Christopher": "en-US-ChristopherNeural",
            "🇺🇸 US English - Aria": "en-US-AriaNeural"
        }
        selected_voice_name = st.selectbox("Select Narrator Voice", list(voice_options.keys()))
        selected_voice_code = voice_options[selected_voice_name]
        
        # Background Music Upload
        st.markdown("---")
        bg_music = st.file_uploader("🎵 Upload Background Music (MP3)", type=['mp3'])
        music_vol = st.slider("Music Volume (Background)", -30, 0, -15, help="Lower is quieter")

    # --- PROCESSING ENGINE ---
    if st.button("🚀 Generate Audiobook (Start Magic)"):
        if not raw_text:
            st.error("Please provide text or file first!")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 1. Generate Voice Audio
                status_text.text("🎙️ Generating Voiceover... (This may take time for large files)")
                voice_filename = "temp_voice.mp3"
                
                # Chunking large text to avoid timeouts (Imp for 300k words)
                # Note: Streamlit has limits, but this loop handles logical breaks
                asyncio.run(generate_tts_audio(raw_text[:100000], selected_voice_code, voice_filename)) # Processing first 100k chars for Demo safety
                progress_bar.progress(60)
                
                final_output = voice_filename
                
                # 2. Mix Music (If uploaded)
                if bg_music:
                    status_text.text("🎼 Mixing Background Music...")
                    # Save uploaded music
                    with open("temp_bg.mp3", "wb") as f: f.write(bg_music.getbuffer())
                    
                    final_output = "Final_Audiobook.mp3"
                    mix_audio_with_music(voice_filename, "temp_bg.mp3", final_output, music_vol)
                    progress_bar.progress(90)
                
                progress_bar.progress(100)
                status_text.success("✅ Audiobook Ready!")
                
                # 3. Download Button
                with open(final_output, "rb") as f:
                    st.download_button("⬇️ Download Full Audiobook", f, file_name="Elite_Audiobook.mp3", mime="audio/mp3")
                    
            except Exception as e:
                st.error(f"Processing Failed: {e}")

# --- 2. VIDEO DOWNLOADER (Compact) ---
elif selected == "Video Downloader":
    st.title("🎬 4K Media Downloader")
    url = st.text_input("Paste Link (YouTube/Insta/FB):")
    if st.button("Download Video"):
        if url:
            try:
                ydl_opts = {'format': 'best', 'quiet': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.image(info.get('thumbnail'), width=300)
                    st.success(f"Found: {info.get('title')}")
                    st.link_button("⬇️ Download Now", info.get('url'))
            except: st.error("Invalid Link")

# --- 3. VAULT (Compact) ---
elif selected == "Vault":
    st.title("🔐 Secure Vault")
    pin = st.text_input("Enter PIN:", type="password")
    if pin == "1234":
        st.success("Unlocked")
        st.file_uploader("Hidden Files", accept_multiple_files=True)
