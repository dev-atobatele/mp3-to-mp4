import streamlit as st
from moviepy import CompositeVideoClip, TextClip, VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip
import tempfile
import os

st.title("MP3 to MP4")

# User uploads
video_file = st.file_uploader("Upload a video, gif, or image. It will be looped and trimmed to the audio duration.", type=["mp4", "gif", "png", "jpg", "jpeg","mkv", "mov", "avi", "webm"])
audio_file = st.file_uploader("Upload an audio track", type=["mp3", "wav", "ogg", "flac","m4a","aac","aiff"])
progress_bar = st.progress(0)

txt_clip = TextClip(
    text="mp3-to-mp4.streamlit.app",
    font_size=20,
    margin=(30, 30),
    color='white'
)

if video_file and audio_file:
    progress_bar.progress(10, "Starting processing...")
    # Save the uploaded files to a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, video_file.name)
        audio_path = os.path.join(tmpdir, audio_file.name)
        
        # Write files to temp dir
        with open(video_path, "wb") as f:
            f.write(video_file.read())
        with open(audio_path, "wb") as f:
            f.write(audio_file.read())
        
        # Determine if it's an image or video/gif by extension
        if video_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            # Convert image to video with the same duration as audio
            audio_clip = AudioFileClip(audio_path)
            video_clip = (ImageClip(video_path)
                        .with_duration(audio_clip.duration)
                        .with_audio(audio_clip))
            clip_w_url = CompositeVideoClip([video_clip, txt_clip.with_duration(video_clip.duration)])
            output_path = os.path.join(tmpdir, "output.mp4")
            progress_bar.progress(70, "Rendering video...")
            clip_w_url.write_videofile(output_path, fps=1 , codec="libx264", audio_codec="aac", audio_bitrate="320k")
            video_clip.close()
            audio_clip.close()
            txt_clip.close()
            clip_w_url.close()
            progress_bar.progress(100)
        else:
            # Process as video/gif
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            num_loops = int(audio_clip.duration // video_clip.duration) + 1
            video_loops = [video_clip.copy() for _ in range(num_loops)]
            looped_video = concatenate_videoclips(video_loops)
            final_clip = looped_video.subclipped(0, audio_clip.duration).with_audio(audio_clip)
            clip_w_url = CompositeVideoClip([final_clip, txt_clip.with_duration(final_clip.duration)])
            output_path = os.path.join(tmpdir, "output.mp4")
            progress_bar.progress(70, "Rendering video...")
            clip_w_url.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", audio_bitrate="320k")
            video_clip.close()
            audio_clip.close()
            final_clip.close()
            looped_video.close()
            txt_clip.close()
            clip_w_url.close()
            progress_bar.progress(100)
        # Present for download
        with open(output_path, "rb") as f:
            st.success("Video created! Download below.")
            st.download_button('Download video', f, file_name="output_video.mp4", mime='video/mp4')