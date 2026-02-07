import streamlit as st
from moviepy import CompositeVideoClip, TextClip, VideoFileClip, AudioFileClip, concatenate_videoclips, ImageClip
from proglog import ProgressBarLogger
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
status_text = st.empty()


class StreamlitProgressLogger(ProgressBarLogger):
    """Custom logger that updates a Streamlit progress bar during video rendering."""
    
    def __init__(self, progress_bar, status_text, progress_start=10, progress_end=95):
        super().__init__()
        self.progress_bar = progress_bar
        self.status_text = status_text
        self.progress_start = progress_start
        self.progress_end = progress_end
        self.current_phase = ""
    
    def bars_callback(self, bar, attr, value, old_value=None):
        # bar is the name of the progress bar (e.g., 't' for video frames, 'chunk' for audio)
        # attr is 'total', 'index', or 'message'
        if attr == "total":
            self.total = value
        elif attr == "index" and hasattr(self, 'total') and self.total > 0:
            # Calculate progress within the rendering phase
            render_progress = value / self.total
            # Map to our progress range (progress_start to progress_end)
            overall_progress = self.progress_start + render_progress * (self.progress_end - self.progress_start)
            self.progress_bar.progress(int(overall_progress), f"{self.current_phase}: {int(render_progress * 100)}%")
    
    def callback(self, **changes):
        # Called for general messages like "Moviepy - Writing video..."
        if "message" in changes:
            msg = changes["message"]
            if "video" in msg.lower():
                self.current_phase = "Rendering video"
            elif "audio" in msg.lower():
                self.current_phase = "Encoding audio"
            self.status_text.text(msg)


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
    progress_bar.progress(5, "Loading files...")
    
    txt_clip = TextClip(
        text="mp3-to-mp4.streamlit.app",
        font_size=20,
        margin=(30, 30),
        color='white'
    )
    
    # Create progress logger for rendering
    logger = StreamlitProgressLogger(progress_bar, status_text, progress_start=10, progress_end=95)
    
    # Save the uploaded files to a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, video_file.name)
        audio_path = os.path.join(tmpdir, audio_file.name)
        
        # Write files to temp dir
        with open(video_path, "wb") as f:
            f.write(video_file.read())
        with open(audio_path, "wb") as f:
            f.write(audio_file.read())
        
        progress_bar.progress(10, "Processing media...")
        
        # Determine if it's an image or video/gif by extension
        if video_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
            # Convert image to video with the same duration as audio
            audio_clip = AudioFileClip(audio_path)
            video_clip = (ImageClip(video_path)
                        .with_duration(audio_clip.duration)
                        .with_audio(audio_clip))
            clip_w_url = CompositeVideoClip([video_clip, txt_clip.with_duration(video_clip.duration)])
            output_path = os.path.join(tmpdir, "output.mov")
            clip_w_url.write_videofile(output_path, fps=1, codec="libx264", audio_codec="pcm_s16le", logger=logger)
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
            clip_w_url.write_videofile(output_path, fps=24, codec="libx264", audio_codec="pcm_s16le", logger=logger)
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
        
        progress_bar.progress(100, "Complete!")
        status_text.empty()

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
