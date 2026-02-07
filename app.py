import streamlit as st
from moviepy import CompositeVideoClip, TextClip, VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip
import tempfile
import os

st.title("MP3 to MP4")

# Initialize session state for tracking rendered video
if "rendered_video" not in st.session_state:
    st.session_state.rendered_video = None
    st.session_state.rendered_for = None  # Track which files were used

# User uploads
video_file = st.file_uploader("Upload a video, gif, or image. It will be looped and trimmed to the audio duration.", type=["mp4", "gif", "png", "jpg", "jpeg","mkv", "mov", "avi", "webm"])
audio_file = st.file_uploader("Upload an audio track", type=["mp3", "wav", "ogg", "flac","m4a","aac","aiff"])
progress_bar = st.progress(0)

# Create a unique identifier for the current file combination
current_files_id = None
if video_file and audio_file:
    current_files_id = (video_file.name, video_file.size, audio_file.name, audio_file.size)

# Check if we need to re-render (new files uploaded) or can use cached result
needs_render = (
    video_file and audio_file and 
    st.session_state.rendered_for != current_files_id
)

if needs_render:
    progress_bar.progress(10, "Starting processing...")
    
    txt_clip = TextClip(
        text="mp3-to-mp4.streamlit.app",
        font_size=20,
        margin=(30, 30),
        color='white'
    )
    
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
            output_path = os.path.join(tmpdir, "output.mov")
            progress_bar.progress(70, "Rendering video...")
            clip_w_url.write_videofile(output_path, fps=1 , codec="libx264", audio_codec="pcm_s16le")
            video_clip.close()
            audio_clip.close()
            txt_clip.close()
            clip_w_url.close()
        else:
            # Process as video/gif
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            num_loops = int(audio_clip.duration // video_clip.duration) + 1
            video_loops = [video_clip.copy() for _ in range(num_loops)]
            looped_video = concatenate_videoclips(video_loops)
            final_clip = looped_video.subclipped(0, audio_clip.duration).with_audio(audio_clip)
            clip_w_url = CompositeVideoClip([final_clip, txt_clip.with_duration(final_clip.duration)])
            output_path = os.path.join(tmpdir, "output.mov")
            progress_bar.progress(70, "Rendering video...")
            clip_w_url.write_videofile(output_path, fps=24, codec="libx264", audio_codec="pcm_s16le")
            video_clip.close()
            audio_clip.close()
            final_clip.close()
            looped_video.close()
            txt_clip.close()
            clip_w_url.close()
        
        # Cache the rendered video in session state
        with open(output_path, "rb") as f:
            st.session_state.rendered_video = f.read()
            st.session_state.rendered_for = current_files_id
        
        progress_bar.progress(100)

# Show download button if we have a rendered video
if st.session_state.rendered_video is not None:
    st.success("Video created! Download below.")
    st.download_button(
        'Download video',
        st.session_state.rendered_video,
        file_name="output_video.mov",
        mime='video/quicktime'
    )

# Clear cached video if files are removed
if not video_file or not audio_file:
    st.session_state.rendered_video = None
    st.session_state.rendered_for = None
