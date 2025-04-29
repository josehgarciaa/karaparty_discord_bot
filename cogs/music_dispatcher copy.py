from discord.ext import commands, tasks
import discord
import aiofiles
import json
import logging
from typing import Any, List, Dict, Optional
from services.youtube_service import YouTubeService
from services.queue.queue_manager import QueueManager

logger = logging.getLogger(__name__)

class MusicDispatcherCog(commands.Cog):
    """
    A Cog for managing music dispatching to Discord channels.
    Handles commands to configure dispatching and a background task to dispatch songs.
    """

    def __init__(self, bot: commands.Bot):
        """Initialize cog with bot instance and services."""
        self.bot = bot
        self.queue: QueueManager = bot.queue
        self.buffer = bot.queue_buffer

        cfg = bot.config
        self.notification_channel = cfg["bot"]["notification_channel"]
        self.management_channel = cfg["bot"]["managment"]
        self.output_channel = cfg["bot"]["output_channel"]

        # Default dispatch settings
        self.dispatch_frequency = 60
        self.dispatch_number = 3
        self.buffer.set_dispatch_number(self.dispatch_number)

        yt_conf: Dict[str, Any] = cfg["youtube"]
        self.youtube_service = YouTubeService(
            client_secret_file=yt_conf["client_secret_file"],
            credentials_file=yt_conf["credentials_file"],
            playlist_id=yt_conf["playlist_id"]
        )

        # Command descriptions
        self.command_list = {
            "dispatch_frequency": "Interval between dispatches in seconds.",
            "dispatch_number": "Number of songs to dispatch each time."
        }

        # Start background dispatch task
        self.dispatch_songs.start()
        logger.info(f"MusicDispatcherCog initialized, management channel: %s", self.management_channel)

    def cog_unload(self) -> None:
        """Cancel ongoing tasks on unload."""
        self.dispatch_songs.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Listen for configuration commands in the management channel from admins.
        """
        if not self._is_valid_command_context(message):
            return

        command, value = self._parse_command(message.content)
        if not command:
            await self._safe_send(message.channel, "⚠️ Invalid usage. Use: `!kai <command> [value]`")
            return

        handlers = {
            "help": self._handle_help,
            "commands": self._handle_help,
            "dispatch_frequency": self._handle_frequency,
            "dispatch_number": self._handle_number
        }

        handler = handlers.get(command)
        if handler:
            await handler(message.channel, value)

    def _is_valid_command_context(self, message: discord.Message) -> bool:
        """
        Check message is from non-bot user, correct channel, has required role and prefix.
        """
        if message.author.bot:
            return False
        if message.channel.name != self.management_channel:
            return False
        if not any(role.name == "KaraParty Admin" for role in message.author.roles):
            return False
        return message.content.startswith("!kai")

    def _parse_command(self, content: str) -> (Optional[str], Optional[str]):
        """
        Extract command and value from message content.

        Returns:
            Tuple of command name and optional value.
        """
        parts = content.strip().split(maxsplit=2)
        if len(parts) < 2:
            return None, None
        command = parts[1]
        value = parts[2] if len(parts) > 2 else None
        return command, value

    async def _handle_help(self, channel: discord.TextChannel, _: Any) -> None:
        """Send formatted help message to channel."""
        lines = ["Here you can control Kai bot for the KaraParty:"]
        lines += [f"`{cmd}`: {desc}" for cmd, desc in self.command_list.items()]
        await self._safe_send(channel, "\n".join(lines))

    async def _handle_frequency(self, channel: discord.TextChannel, value: str) -> None:
        """Validate and apply new dispatch frequency."""
        try:
            seconds = int(value)
        except (ValueError, TypeError):
            await self._safe_send(channel, "⚠️ Value must be an integer number of seconds.")
            return

        self.dispatch_frequency = seconds
        self.dispatch_songs.change_interval(seconds=seconds)
        await self._safe_send(channel, f"Dispatch interval set to {seconds} seconds.")
        logger.info("Dispatch frequency changed to %s seconds", seconds)

    async def _handle_number(self, channel: discord.TextChannel, value: str) -> None:
        """Validate and apply new dispatch number."""
        try:
            count = int(value)
            if count < 1:
                raise ValueError("Must be positive.")
        except (ValueError, TypeError):
            await self._safe_send(channel, "⚠️ Value must be a positive integer.")
            return

        self.dispatch_number = count
        self.buffer.set_dispatch_number(count)
        await self._safe_send(channel, f"Dispatch number set to {count} songs.")
        logger.info("Dispatch number changed to %s", count)

    async def _safe_send(self, channel: discord.abc.Messageable, content: str) -> None:
        """
        Safely send a message, catching Discord send errors.
        """
        try:
            await channel.send(content)
        except discord.HTTPException as e:
            logger.error("Failed to send message to %s: %s", channel, e)

    async def _read_dispatched_data(self) -> List[Dict[str, Any]]:
        """
        Read previously dispatched songs from JSON file.

        Returns:
            List of dispatched song records.
        """
        file_name = "dispatched_songs.json"
        try:
            async with aiofiles.open(file_name, 'r') as f:
                text = await f.read()
                return json.loads(text)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    async def _write_dispatched_data(self, data: List[Dict[str, Any]]) -> None:
        """
        Append new dispatched songs to JSON file.
        """
        file_name = "dispatched_songs.json"
        existing = await self._read_dispatched_data()
        existing.extend(data)
        try:
            async with aiofiles.open(file_name, 'w') as f:
                await f.write(json.dumps(existing, indent=4))
        except Exception as e:
            logger.error("Failed to write dispatched songs file: %s", e)

    @tasks.loop(seconds=60)
    async def dispatch_songs(self) -> None:
        """
        Periodic task that dispatches songs from queue to Discord and YouTube.
        """
        dispatched = self.buffer.apply_to(self.queue)
        if not dispatched:
            return

        send_channel = discord.utils.get(
            self.bot.get_all_channels(),
            name=self.output_channel
        )

        for song in dispatched:
            await self._dispatch_song(song, send_channel)

        await self._write_dispatched_data(dispatched)

    async def _dispatch_song(self, song: Dict[str, Any], channel: Optional[discord.TextChannel]) -> None:
        """
        Add song to YouTube playlist and send to Discord channel.
        """
        try:
            self.youtube_service.add_video_to_playlist(song['link'])
        except Exception as e:
            await self._notify_error(f"Error adding video {song['link']}: {e}")
            return

        if channel:
            content = (
                f"🎶 **Queued Song**\n"
                f"**Link**: {song['link']}\n"
                f"**Team**: #{song['team']}\n"
                f"**At**: {song['timestamp']} UTC"
            )
            await self._safe_send(channel, content)

    async def _notify_error(self, message: str) -> None:
        """
        Send error messages to management channel.
        """
        mgmt = discord.utils.get(
            self.bot.get_all_channels(),
            name=self.management_channel
        )
        logger.error(message)
        if mgmt:
            await self._safe_send(mgmt, f"⚠️ {message}")

    @dispatch_songs.before_loop
    async def before_dispatch(self) -> None:
        """Wait until bot is ready before starting dispatch loop."""
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    """Add the MusicDispatcherCog to the bot."""
    await bot.add_cog(MusicDispatcherCog(bot))
