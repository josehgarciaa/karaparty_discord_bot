from __future__ import annotations

import json
from typing import Any, List

import aiofiles
import discord
from discord.ext import commands, tasks

from utils.logger import get_logger                     # ← your central logger helper
from services.youtube_service import YouTubeService
from services.queue.queue_manager import QueueManager

logger = get_logger(__name__)                           # one logger for the whole cog


class MusicDispatcherCog(commands.Cog):
    """
    Dispatches songs from the internal queue to both YouTube (via
    YouTubeService) and a Discord ‘output_channel’.

    All important milestones are *printed* **and** *logged* so you
    can tail `logs/YYYY-MM-DD.log` later without losing the quick
    console feedback you’re used to.
    """

    # ────────────────────────────────────────────────
    #  life-cycle
    # ────────────────────────────────────────────────
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.queue: QueueManager = bot.queue
        self.buffer = bot.queue_buffer

        self.notification_channel: str = bot.config["bot"]["notification_channel"]
        self.management_channel: str = bot.config["bot"]["managment"]             # sic → config spelling kept
        self.output_channel: str = bot.config["bot"]["output_channel"]

        self.command_list = {
            "dispatch_frequency": "Defines the time between dispatch cycles (seconds).",
            "dispatch_number": "Defines how many songs are dispatched each cycle.",
        }

        # user-tweakable parameters
        self.dispatch_frequency: int = 120
        self.dispatch_number: int = 1
        self.buffer.set_dispatch_number(self.dispatch_number)

        self._say(f"Management channel: {self.management_channel}")

        # YouTube helper
        yt_conf: dict[str, Any] = bot.config["youtube"]
        self.youtube_service = YouTubeService(
            client_secret_file=yt_conf["client_secret_file"],
            credentials_file=yt_conf["credentials_file"],
            playlist_id=yt_conf["playlist_id"],
        )

        # start background task
        self.dispatch_songs.start()

    def cog_unload(self):
        self.dispatch_songs.cancel()

    # ────────────────────────────────────────────────
    #  message listener (admin commands)
    # ────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel.name != self.management_channel:
            return

        required_role = "KaraParty Admin"
        if not any(role.name == required_role for role in message.author.roles):
            return

        if not message.content.startswith("!kai"):
            return

        parts: List[str] = message.content.strip().split(maxsplit=2)
        if len(parts) < 2:
            await message.channel.send("⚠️ Comando inválido. Uso: `!kai comando [valor]`")
            return

        _, command = parts[0], parts[1]
        value = parts[2] if len(parts) > 2 else None

        # ---- help -----------------------------------------------------------
        if command in {"help", "commands"}:
            lines = ["Here you can control Kai bot’s behavior:"]
            lines += [f"• **{k}** – {v}" for k, v in self.command_list.items()]
            await message.channel.send("\n".join(lines))
            return

        # ---- dispatch_frequency --------------------------------------------
        if command == "dispatch_frequency":
            try:
                new_freq = int(value)
            except (TypeError, ValueError):
                await message.channel.send("⚠️ Value must be an integer.")
                return

            self.dispatch_frequency = new_freq
            if self.dispatch_songs.is_running():
                self.dispatch_songs.change_interval(seconds=new_freq)
            else:
                self.dispatch_songs.start()

            await message.channel.send(f"⏱️ Dispatch frequency set to **{new_freq} s**.")
            self._say(f"Dispatch frequency changed to {new_freq}s")
            return

        # ---- dispatch_number -----------------------------------------------
        if command == "dispatch_number":
            try:
                new_num = int(value)
            except (TypeError, ValueError):
                await message.channel.send("⚠️ Value must be a positive integer.")
                return

            self.dispatch_number = new_num
            self.buffer.set_dispatch_number(new_num)
            await message.channel.send(f"🎶 Songs per dispatch set to **{new_num}**.")
            self._say(f"Dispatch number changed to {new_num}")
            return

    # ────────────────────────────────────────────────
    #  background task
    # ────────────────────────────────────────────────
    @tasks.loop(seconds=60)
    async def dispatch_songs(self):
        self._say(f"Dispatch cycle started; frequency = {self.dispatch_frequency}s")

        dispatched_songs = self.buffer.apply_to(self.queue)
        if not dispatched_songs:
            self._say("No songs to dispatch this cycle", level="debug")
            return

        send_channel = discord.utils.get(self.bot.get_all_channels(), name=self.output_channel)

        # iterate over songs
        for song in dispatched_songs:
            self._say(f"Attempting to queue {song['link']} (team #{song['team']}) on YouTube")

            try:
                self.youtube_service.add_video_to_playlist(song["link"])
                content = (
                    f"🎶 **Canción en fila**\n"
                    f"**Link**: {song['link']}\n"
                    f"**Del equipo**: #{song['team']}\n"
                    f"**A las**: {song['timestamp']} UTC"
                )
                if send_channel:
                    await send_channel.send(content)

            except Exception as exc:
                self._say(f"Error adding video: {exc}", level="error")

                management_ch = discord.utils.get(
                    self.bot.get_all_channels(), name=self.management_channel
                )
                if management_ch:
                    await management_ch.send(f"⚠️ Error adding video: {exc!s}")

        await self._write_dispatched_songs(dispatched_songs)

    @dispatch_songs.before_loop
    async def before_dispatch_songs(self):
        await self.bot.wait_until_ready()

    # ────────────────────────────────────────────────
    #  helpers
    # ────────────────────────────────────────────────
    async def _write_dispatched_songs(self, dispatched_songs):
        file_name = "dispatched_songs.json"
        try:
            async with aiofiles.open(file_name, "r") as f:
                data = json.loads(await f.read())
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        data.extend(dispatched_songs)
        async with aiofiles.open(file_name, "w") as f:
            await f.write(json.dumps(data, indent=4))
        self._say(f"Wrote {len(dispatched_songs)} dispatched song(s) to {file_name}", level="debug")

    def _say(self, msg: str, *, level: str = "info"):
        """
        Print `msg` to the console **and** log it at the specified level.
        Valid levels: debug, info, warning, error, critical.
        """
        print(msg)
        getattr(logger, level.lower(), logger.info)(msg)  # fall back to INFO if level typo


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicDispatcherCog(bot))
