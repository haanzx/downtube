"""Global constants."""

APP_NAME = "DownTube"
APP_VERSION = "0.2.0"

# Supported audio file extensions
AUDIO_EXTS = {".mp3", ".m4a", ".flac", ".opus", ".ogg", ".wav", ".aac"}

# MIME types for audio streaming
AUDIO_MIME = {
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".flac": "audio/flac",
    ".opus": "audio/opus",
    ".ogg": "audio/ogg",
    ".wav": "audio/wav",
    ".aac": "audio/aac",
}

# YouTube thumbnail URL template
YT_THUMBNAIL = "https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
