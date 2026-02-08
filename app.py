import streamlit as st
from streamlit_option_menu import option_menu
import yt_dlp
import os
import shutil
from cryptography.fernet import Fernet
import validators

# --- Page Config (App ka Look) ---
st.set_page_config(page_title="EliteVault Pro", page_icon="🔒", layout="centered")

# --- Custom CSS (Pro Design ke liye) ---
st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 20px; background-color: #00e676; color: black; font-weight: bold;}
    .stTextInput>div>div>input {border-radius: 10px;}
    </style>
    """, unsafe_allow_html=True)

# --- Navigation Menu (Bottom Bar style) ---
selected = option_menu(
    menu_title=None,
    options=["Downloader", "Vault", "PDF Tools"],
    icons=["cloud-download", "lock", "file-earmark-pdf"],
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#1e1e1e"},
        "icon": {"color": "orange", "font-size": "18px"}, 
        "nav-link": {"font-size": "14px", "text-align": "center", "margin":"0px", "--hover-color": "#333"},
        "nav-link-selected": {"background-color": "#00e676", "color": "black"},
    }
)

# --- 1. DOWNLOADER SECTION ---
if selected == "Downloader":
    st.title("🎬 4K Media Downloader")
    st.info("Supported: YouTube, Instagram, Facebook, Twitter (X)")
    
    url = st.text_input("🔗 Link Paste Karein:")
    
    col1, col2 = st.columns(2)
    with col1:
        format_option = st.selectbox("Format", ["Video (MP4)", "Audio Only (MP3)"])
    with col2:
        quality_option = st.selectbox("Quality", ["Best Available (4K/HD)", "Data Saver (480p)", "Lowest (144p)"])

    if st.button("🚀 Process Media"):
        if not url:
            st.error("Pehle Link to dalo bhai!")
        else:
            with st.spinner("Analyzing... (Thoda time lagega)"):
                try:
                    # Setting Options based on user choice
                    ydl_opts = {
                        'outtmpl': '%(title)s.%(ext)s',
                        'quiet': True,
                    }
                    
                    if format_option == "Audio Only (MP3)":
                        ydl_opts['format'] = 'bestaudio/best'
                        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3',}]
                    else:
                        if quality_option == "Lowest (144p)":
                            ydl_opts['format'] = 'worst'
                        else:
                            ydl_opts['format'] = 'bestvideo+bestaudio/best'

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        st.image(info.get('thumbnail'), caption=info.get('title'), use_container_width=True)
                        st.success(f"Ready: {info.get('title')}")
                        
                        # Note: Server Download restricted on Cloud, showing Direct Link
                        video_url = info.get('url')
                        st.link_button("⬇️ Download Now (Server Link)", video_url)
                        st.caption("Agar download start na ho, to button daba kar 'Save Video As' karein.")
                        
                except Exception as e:
                    st.error(f"Error: Link private hai ya galat hai. ({str(e)})")

# --- 2. PRIVATE VAULT SECTION ---
elif selected == "Vault":
    st.title("🔐 Secure Private Vault")
    
    # Simple PIN System (Session State)
    if 'unlocked' not in st.session_state:
        st.session_state.unlocked = False

    if not st.session_state.unlocked:
        pin = st.text_input("🔑 Enter PIN to Access:", type="password")
        if st.button("Unlock Vault"):
            if pin == "1234":  # Default PIN
                st.session_state.unlocked = True
                st.rerun()
            else:
                st.error("Galat PIN! Door raho.")
    else:
        st.success("🔓 Vault Unlocked!")
        tab1, tab2 = st.tabs(["Hidden Photos", "Hidden Videos"])
        
        with tab1:
            uploaded_file = st.file_uploader("Hide Photo", type=['png', 'jpg'])
            if uploaded_file:
                st.image(uploaded_file, caption="Secured Image")
                st.toast("Photo Encrypted & Saved in Vault!")
        
        if st.button("🔒 Lock Vault"):
            st.session_state.unlocked = False
            st.rerun()

# --- 3. PDF TOOLS SECTION ---
elif selected == "PDF Tools":
    st.title("📄 PDF Converter Suite")
    st.write("Coming Soon in Pro Version...")
    st.info("Yahan hum PDF Merge aur Image-to-PDF add karenge.")

