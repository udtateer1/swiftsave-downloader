import streamlit as st
import yt_dlp
import validators

st.set_page_config(page_title="SwiftSave Downloader", page_icon="📥")
st.title("📥 SwiftSave: Video Downloader")
st.markdown("### Ek click mein Reels aur Shorts gallery mein!")

url = st.text_input("Video ka Link yahan paste karein:")

if st.button("Video Dhundo"):
    if not validators.url(url):
        st.error("Bhai, sahi link dalo!")
    else:
        with st.spinner("Jugaad lagaya ja raha hai..."):
            try:
                ydl_opts = {'format': 'best'}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    video_url = info.get('url', None)
                    title = info.get('title', 'Video')
                    
                    if video_url:
                        st.success(f"Mil gaya: {title}")
                        st.video(video_url)
                        st.download_button("Download Karein", video_url, file_name=f"{title}.mp4")
            except Exception as e:
                st.error("Error: Ye video private ho sakta hai ya link galat hai.")

