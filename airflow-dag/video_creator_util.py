
from moviepy import *
import re

FONT_SIZE = 100
FONT_COLOR = "white"
FONT_PATH = "Arial"  # Ensure this font exists on the system

class ContentSegment:
    """Represents a segment (text, image, or audio) with timing information."""

    def __init__(self, type_, content, start, end):
        self.type = type_
        self.content = content
        self.start = start
        self.end = end

    @property
    def duration(self):
        return self.end - self.start


class VideoGenerator:
    """Parses script, processes segments, and creates a video with text, images, and audio."""

    def __init__(self, script_content="", output_path="video.mp4"):
        self.script_content = script_content
        self.output_path = output_path
        self.segments = []

    def parse_script(self):
        """Parses the script content and extracts segments."""
        # split to lines for script parsing
        lines = self.script_content.split(">>")
        
        for line in lines:
            regex = r"(text|image|audio) # (.*?) # (\d+):(\d+):(\d+) - (\d+):(\d+):(\d+)"
            match = re.match(regex, line.strip())
            # split to lines for script parsing
            if match:
                type_, content, h1, m1, s1, h2, m2, s2 = match.groups()
                start = int(h1) * 3600 + int(m1) * 60 + int(s1)
                end = int(h2) * 3600 + int(m2) * 60 + int(s2)
                self.segments.append(ContentSegment( type_, content, start, end))

    def create_video(self):
        """Creates a video using parsed segments."""
        clips = []
        audio_clips = []

        # Process audio segments first
        for segment in self.segments:
            if segment.type == "audio":
                audio_clip = AudioFileClip(segment.content).subclipped(segment.start, segment.end)
                audio_clips.append(audio_clip)

        final_audio = concatenate_audioclips(
            audio_clips) if audio_clips else None

        # Process image and text segments
        for segment in self.segments:
            if segment.type == "image":
                img_clip = ImageClip(
                    segment.content).with_duration(segment.duration)
                clips.append(img_clip)
            elif segment.type == "text":
                txt_clip = TextClip(text=segment.content, font_size=FONT_SIZE, color=FONT_COLOR,font=FONT_PATH, size=(1280, 720))
                txt_clip = txt_clip.with_position('center').with_duration(segment.duration)
                clips.append(txt_clip)

        # Concatenate all video clips
        final_video = concatenate_videoclips(clips, method="compose")

        # Add audio if available
        if final_audio:
            final_video = final_video.with_audio(final_audio)

        # Export video
        final_video.write_videofile(
            self.output_path, fps=24, codec='libx264', audio_codec='aac')

    def run(self):
        """Runs the full pipeline: parse script and generate video."""
        self.parse_script()
        self.create_video()


