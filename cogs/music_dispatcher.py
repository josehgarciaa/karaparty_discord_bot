import aiofiles
import json
from typing import Any
from discord.ext import commands, tasks
import discord
from services.youtube_service import YouTubeService
from services.queue.queue_manager import QueueManager

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
        self.queue: QueueManager = bot.queue
        self.buffer = bot.queue_buffer

        self.notification_channel: str = bot.config["bot"]["notification_channel"]
        self.admin_channel: str = bot.config["bot"]["admin_log_channel"]
        self.output_channel: str = bot.config["bot"]["output_channel"]

        yt_conf: dict[str, Any] = bot.config["youtube"]
        self.youtube_service: YouTubeService = YouTubeService(
            client_secret_file=yt_conf["client_secret_file"],
            credentials_file=yt_conf["credentials_file"],
            playlist_id=yt_conf["playlist_id"]
        )

        # Start the background task when the cog is initialized
        self.dispatch_songs.start()

    def cog_unload(self) -> None:
        """
        Called automatically when the cog is unloaded.
        Cancels the background dispatch task.
        """
        self.dispatch_songs.cancel()

    async def write_dispatched_songs(self, dispatched_songs):
        """Asynchronously write dispatched songs to a JSON file"""
        file_name = "dispatched_songs.json"

        try:
            # Attempt to read existing songs from the JSON file
            async with aiofiles.open(file_name, 'r') as f:
                data = json.loads(await f.read())
        except (FileNotFoundError, json.JSONDecodeError):
            # Initialize with empty list if file does not exist or is invalid
            data = []

        # Extend the existing list with newly dispatched songs
        data.extend(dispatched_songs)

        # Write updated data back into the JSON file
        async with aiofiles.open(file_name, 'w') as f:
            await f.write(json.dumps(data, indent=4))

    @tasks.loop(seconds=60)
    async def dispatch_songs(self):
        """
        Background loop task that runs every 2 minutes.

        Dispatches buffered songs to YouTube playlist and Discord.
        Writes dispatched songs to JSON asynchronously afterward.
        """
        # Apply buffered operations and retrieve songs awaiting dispatch
        dispatched_songs = self.buffer.apply_to(self.queue)
        print("Dispatching songs:")
        print(self.queue._dispatched)

        # Early exit if no songs to dispatch
        if not dispatched_songs:
            return

        # Get the configured Discord channel for notifications
        send_channel = discord.utils.get(self.bot.get_all_channels(), name=self.output_channel)

        # Iterate through dispatched songs and attempt dispatch
        for song in dispatched_songs:
            try:
                # Add song to YouTube playlist
                self.youtube_service.add_video_to_playlist(song['link'])

                # Construct message content
                content = (
                    f"🎶 **Canción en fila**\n"
                    f"**Link**: {song['link']}\n"
                    f"**Del equipo**: #{song['team']}\n"
                    f"**A las**: {song['timestamp']} UTC"
                )

                # Send message to output channel
                if send_channel:
                    await send_channel.send(content)

            except Exception as e:
                # Notify admin if there's an error during dispatch
                admin_channel = discord.utils.get(self.bot.get_all_channels(), name=self.admin_channel)
                error_message = f"⚠️ Error adding video: {e}"
                print(error_message)
                if admin_channel:
                    await admin_channel.send(error_message)

        # After dispatching all songs successfully, write them asynchronously to json
        await self.write_dispatched_songs(dispatched_songs)

    @dispatch_songs.before_loop
    async def before_dispatch_songs(self):
        """
        Coroutine that runs once before the `dispatch_songs` loop starts.
        Ensures the bot is fully ready and connected to Discord.
        """
        await self.bot.wait_until_ready()


async def setup(bot):
    """
    Entrypoint for loading the cog into the bot.

    Args:
        bot (commands.Bot): The bot instance to attach the cog to.
    """
    await bot.add_cog(MusicDispatcherCog(bot))