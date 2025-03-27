import yt_dlp
import mpv

youtube_url = "https://www.youtube.com/watch?v=QCZZwZQ4qNs"

def get_stream_url(youtube_url):
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_url, download=False)
        formats = info_dict.get("formats", [])
        for fmt in formats:
            if "m3u8" in fmt.get("url", ""):
                return fmt["url"]
        return info_dict.get('url', None)

stream_url = get_stream_url(youtube_url)

if not stream_url:
    print("Could not retrieve stream URL")
    exit()

print(f"Streaming from: {stream_url}")

player = mpv.MPV(ytdl=False, input_default_bindings=True, input_vo_keyboard=True)

# Overlay a GIF or PNG frame as OSD overlay (Optional)
# Note: GIF animation support may vary, PNG recommended for simplicity
# Ensure 'frame.png' is in the current directory or provide full path
player.command('video-add', 'frame.png', 'auto')

player.play(stream_url)

player.wait_for_playback()
