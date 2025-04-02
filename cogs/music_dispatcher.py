
from typing import Any
from discord.ext import commands, tasks
import discord
from services.youtube_service import YouTubeService
from services.queue_manager import QueueManager

class MusicDispatcherCog(commands.Cog):
    """
    Cog responsible for dispatching songs from the internal queue
    to a Discord channel and uploading them to a YouTube playlist.
    """
    def __init__(self, bot):
        """
        Initializes the MusicDispatcherCog.

        Args:
            bot (commands.Bot): The bot instance this cog is attached to.
        """

        self.bot = bot
        self.queue = QueueManager()


        yt_conf: dict[str, Any] = bot.config["youtube"]        
        self.youtube_service: YouTubeService = YouTubeService(
            client_secret_file=yt_conf["client_secret_file"],
            credentials_file=yt_conf["credentials_file"],
            playlist_id=yt_conf["playlist_id"]
        )        

        self.output_channel: str = bot.config["bot"]["output_channel"]
        # Start the background task when the cog is initialized
        self.dispatch_songs.start()

    def cog_unload(self) -> None:
        """
        Called automatically when the cog is unloaded.
        Cancels the background dispatch task.
        """
        self.dispatch_songs.cancel()

    @tasks.loop(seconds=10)
    async def dispatch_songs(self):
        """
        Background loop task that runs every 10 seconds.

        This method is managed by `discord.ext.tasks.Loop`, which schedules
        the coroutine to be run on the specified interval. It checks the internal
        queue for pending songs and dispatches them:
            - Adds the song to the YouTube playlist via the YouTubeService
            - Sends a message in the configured output channel

        The loop is started using `self.dispatch_songs.start()` during cog initialization,
        and can be cancelled using `self.dispatch_songs.cancel()` during cog unload.
        """
        if not self.queue.is_empty():
            song = self.queue.get_link()
            if song:
                send_channel = discord.utils.get(self.bot.get_all_channels(), name=self.output_channel)
                if send_channel:
                    try:
                        self.youtube_service.add_video_to_playlist(song['link'])
                        content = (
                            f"🎶 **Canción en fila**\n"
                            f"**Link**: {song['link']}\n"
                            f"**Agregada por**: {song['user']}\n"
                            f"**Del equipo**: #{song['channel']}\n"
                            f"**A las**: {song['timestamp']} UTC"
                        )
                        await send_channel.send(content)
                    except Exception as e:
                        error_message = f"⚠️ Error adding video: {e}"
                        print(error_message)
                        await send_channel.send(error_message)#

    @dispatch_songs.before_loop
    async def before_dispatch_songs(self):
        """
        Coroutine that runs once before the `dispatch_songs` loop starts.

        This is used to delay the task until the bot is fully ready and connected
        to Discord. It ensures that all necessary guild/channel data is available
        before the loop begins dispatching messages.

        Decorator: `@dispatch_songs.before_loop`
        This links the method to the task object so it's run as a setup step.
        """        
        await self.bot.wait_until_ready()

async def setup(bot):
    """
    Entrypoint for loading the cog into the bot.

    Args:
        bot (commands.Bot): The bot instance to attach the cog to.
    """    
    await bot.add_cog(MusicDispatcherCog(bot))
