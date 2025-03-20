import re

def is_youtube_link(link):
    regex = r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+|https?://youtu\.be/[\w-]+)'
    return re.match(regex, link) is not None
