import re

class LinkManager:
    YOUTUBE_REGEX = r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+|https?://youtu\.be/[\w-]+)'

    def validate_message(self, message_content):
        links = re.findall(self.YOUTUBE_REGEX, message_content)
        if len(links) == 1:
            return True, links[0]
        return False, None
