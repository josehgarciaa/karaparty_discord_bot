from bot.core import KarapartyBot
from utils.playlist_player import YouTubePlaylistMonitor

if __name__ == "__main__":
    #bot = KarapartyBot(config_file="configs/config.yaml")
    #bot.run_bot()


    PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLP641Bf8QxbWAieUPDyrrQJoil8-5ZdMw"
    PROFILE_PATH = "C:\\Users\\joseh\\AppData\\Local\\Google\\Chrome\\User Data"

    SONG_QUEUE = [
        {'title': 'Song 1', 'team': 'A', 'link': 'https://youtube.com/1'},
        {'title': 'Song 2', 'team': 'B', 'link': 'https://youtube.com/2'},
        {'title': 'Song 3', 'team': 'C', 'link': 'https://youtube.com/3'},
    ]

    monitor = YouTubePlaylistMonitor(PLAYLIST_URL, SONG_QUEUE, PROFILE_PATH)
    monitor.start_playlist()
    monitor.monitor_playlist()
    monitor.close()
