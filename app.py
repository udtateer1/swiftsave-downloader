import streamlit as st
from streamlit_option_menu import option_menu
import yt_dlp
import os
import asyncio
import edge_tts
from deep_translator import GoogleTranslator
from PyPDF2 import PdfReader
from fpdf import FPDF
import validators

# --- Page Config & Hide Menu ---
st.set_page_config(page_title="EliteVault Pro", page_icon="🔒", layout="centered")

st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 20px; background-color: #00e676; color: black; font-weight: bold;}
    .stTextInput>div>div>input {border-radius: 10px;}
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    </style>
    """, unsafe_allow_html=True)

# --- Navigation Menu ---
selected = option_menu(
    menu_title=None,
    options=["Downloader", "Vault", "Audiobook & Tools"],
    icons=["cloud-download", "lock", "book-half"],
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#1e1e1e"},
        "icon": {"color": "orange", "font-size": "18px"}, 
        "nav-link": {"font-size": "14px", "text-align": "center", "margin":"0px", "--hover-color": "#333"},
        "nav-link-selected": {"background-color": "#00e676", "color": "black"},
    }
)

# --- HELPER: Async TTS Function ---
async def generate_audio(text, voice, filename):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)

# --- 1. DOWNLOADER SECTION ---
if selected == "Downloader":
    st.title("🎬 4K Media Downloader")
    url = st.text_input("🔗 Link Paste Karein:")
    col1, col2 = st.columns(2)
    with col1: format_option = st.selectbox("Format", ["Video (MP4)", "Audio (MP3)"])
    with col2: quality_option = st.selectbox("Quality", ["4K/HD (Best)", "480p (Saver)"])

    if st.button("🚀 Process Media"):
        if not url: st.error("Link to dalo bhai!")
        else:
            with st.spinner("Processing..."):
                try:
                    ydl_opts = {'outtmpl': '%(title)s.%(ext)s', 'quiet': True}
                    if format_option == "Audio (MP3)":
                        ydl_opts['format'] = 'bestaudio/best'
                    else:
                        ydl_opts['format'] = 'bestvideo+bestaudio/best' if quality_option == "4K/HD (Best)" else 'worst'
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        st.image(info.get('thumbnail'), use_container_width=True)
                        st.success(f"Ready: {info.get('title')}")
                        st.link_button("⬇️ Download Now (Server Link)", info.get('url'))
                except Exception as e: st.error("Link Private hai ya Expired.")

# --- 2. VAULT SECTION ---
elif selected == "Vault":
    st.title("🔐 Secret Vault")
    if 'unlocked' not in st.session_state: st.session_state.unlocked = False

    if not st.session_state.unlocked:
        pin = st.text_input("🔑 Enter PIN:", type="password")
        if st.button("Unlock"):
            if pin == "1234":
                st.session_state.unlocked = True
                st.rerun()
            else: st.error("Galat PIN!")
    else:
        st.success("🔓 Vault Open")
        st.file_uploader("Hide Photos/Videos", accept_multiple_files=True)
        if st.button("🔒 Lock Vault"):
            st.session_state.unlocked = False
            st.rerun()

# --- 3. AUDIOBOOK & TOOLS SECTION ---
elif selected == "Audiobook & Tools":
    st.title("🎧 Audiobook & Translator")
    
    tab1, tab2 = st.tabs(["🗣️ Text to Audio", "📄 PDF Tools"])
    
    # --- AUDIOBOOK MAKER ---
    with tab1:
        st.info("Kisi bhi text ya file ko Real Human Voice mein suno!")
        
        # Input Method
        input_type = st.radio("Input Type:", ["Type Text", "Upload File (PDF/TXT)"], horizontal=True)
        
        text_data = ""
        if input_type == "Type Text":
            text_data = st.text_area("Yahan kahani likhein...", height=150)
        else:
            uploaded_file = st.file_uploader("File Chunein", type=["pdf", "txt"])
            if uploaded_file:
                if uploaded_file.name.endswith(".pdf"):
                    reader = PdfReader(uploaded_file)
                    for page in reader.pages:
                        text_data += page.extract_text()
                else:
                    text_data = uploaded_file.read().decode("utf-8")
                st.success(f"File Loaded: {len(text_data)} characters")

        # Translation & Voice Settings
        col1, col2 = st.columns(2)
        with col1:
            translate_to = st.checkbox("Translate to Hindi?")
        with col2:
            voice_gender = st.selectbox("Voice Style", ["Male (Indian Accent)", "Female (Indian Accent)", "Male (US)", "Female (US)"])

        # Mapping Voices (Edge TTS)
        voice_map = {
            "Male (Indian Accent)": "en-IN-PrabhatNeural",
            "Female (Indian Accent)": "en-IN-NeerjaNeural",
            "Male (US)": "en-US-ChristopherNeural",
            "Female (US)": "en-US-AriaNeural"
        }
        if translate_to: # Agar Hindi translate hua to Hindi voice chahiye
            voice_map = {
                "Male (Indian Accent)": "hi-IN-MadhurNeural",
                "Female (Indian Accent)": "hi-IN-SwaraNeural",
                "Male (US)": "hi-IN-MadhurNeural",
                "Female (US)": "hi-IN-SwaraNeural"
            }

        if st.button("🎧 Create Audiobook"):
            if not text_data:
                st.warning("Kuch likho ya file upload karo!")
            else:
                with st.spinner("Converting... (Lambi files mein time lag sakta hai)"):
                    final_text = text_data
                    
                    # 1. Translation Logic
                    if translate_to:
                        try:
                            # Chunking for translation (limit 5000 chars per chunk)
                            translator = GoogleTranslator(source='auto', target='hi')
                            chunks = [text_data[i:i+4000] for i in range(0, len(text_data), 4000)]
                            translated_chunks = [translator.translate(chunk) for chunk in chunks]
                            final_text = " ".join(translated_chunks)
                            st.info("Translation Complete! Audio generating...")
                        except Exception as e:
                            st.error(f"Translation Error: {e}")

                    # 2. Audio Generation Logic
                    try:
                        selected_voice = voice_map[voice_gender]
                        output_file = "audiobook.mp3"
                        asyncio.run(generate_audio(final_text[:50000], selected_voice, output_file)) # Limit 50k chars for safety
                        
                        st.audio(output_file)
                        with open(output_file, "rb") as f:
                            st.download_button("⬇️ Download Audiobook (MP3)", f, file_name="my_audiobook.mp3")
                    except Exception as e:
                        st.error(f"Audio Error: {e}")

    # --- PDF TOOLS ---
    with tab2:
        st.header("📄 Image to PDF")
        imgs = st.file_uploader("Select Images", accept_multiple_files=True, type=["jpg", "png"])
        if imgs and st.button("Convert to PDF"):
            from PIL import Image
            image_list = [Image.open(i).convert("RGB") for i in imgs]
            image_list[0].save("output.pdf", save_all=True, append_images=image_list[1:])
            with open("output.pdf", "rb") as f:
                st.download_button("⬇️ Download PDF", f)
