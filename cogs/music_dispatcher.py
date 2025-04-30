from discord.ext import commands, tasks
import discord
import aiofiles
import json
from typing import Any
from services.youtube_service import YouTubeService
from services.queue.queue_manager import QueueManager

class MusicDispatcherCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue: QueueManager = bot.queue
        self.buffer = bot.queue_buffer

        self.notification_channel: str = bot.config["bot"]["notification_channel"]
        self.managment_channel: str = bot.config["bot"]["managment"]
        self.output_channel: str = bot.config["bot"]["output_channel"]

        self.command_list = {
            "dispatch_frequency": "Defines the times in which the songs are dispatched in seconds.",
            "dispatch_number": "Defines the number of songs dispatched every dispatched time."
        }
        self.dispatch_frequency = 120  # Default value
        self.dispatch_number = 1  # Default value
        self.buffer.set_dispatch_number(self.dispatch_number)

        print("Managment channel:", self.managment_channel)

        yt_conf: dict[str, Any] = bot.config["youtube"]
        self.youtube_service: YouTubeService = YouTubeService(
            client_secret_file=yt_conf["client_secret_file"],
            credentials_file=yt_conf["credentials_file"],
            playlist_id=yt_conf["playlist_id"]
        )

        # Start the background task
        self.dispatch_songs.start()

    def cog_unload(self):
        self.dispatch_songs.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.name != self.managment_channel:
            return

        required_role = "KaraParty Admin"
        has_role = any(role.name == required_role for role in message.author.roles)
        if not has_role:
            return

        if not message.content.startswith("!kai"):
            return

        parts = message.content.strip().split(maxsplit=2)
        if len(parts) < 2:
            await message.channel.send("⚠️ Comando inválido. Uso: `!kai comando [valor]`")
            return

        _, command = parts[0], parts[1]
        value = parts[2] if len(parts) > 2 else None

        if command == "help" or command == "commands":
            help_message = ["Here you can control the behavior of Kai bot for the KaraParty:"]
            help_message += [f"{k}\n\t-- {v}" for k, v in self.command_list.items()]
            final_message = "\n".join(help_message)
            await message.channel.send(final_message)

        if command == "dispatch_frequency":
            valid_value = None
            try:
                valid_value = int(value)
            except ValueError:
                await message.channel.send("The command value should be an integer.")
            if valid_value is not None:
                self.dispatch_frequency = valid_value
                if self.dispatch_songs.is_running():
                    self.dispatch_songs.change_interval(seconds=valid_value)
                else:
                    self.dispatch_songs.start()
                await message.channel.send(f"Dispatching time changed to {valid_value} seconds.")
                

        if command == "dispatch_number":
            valid_value = None
            try:
                valid_value = int(value)
            except ValueError:
                await message.channel.send("The command value should be a positive  integer.")
            if valid_value is not None:
                self.dispatch_frequency = valid_value
                if self.dispatch_songs.is_running():
                    self.buffer.set_dispatch_number(valid_value)
                else:
                    self.dispatch_songs.start()
                await message.channel.send(f"Number of Dispatching songs changed to {valid_value}.")

                

    async def write_dispatched_songs(self, dispatched_songs):
        file_name = "dispatched_songs.json"
        try:
            async with aiofiles.open(file_name, 'r') as f:
                data = json.loads(await f.read())
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        data.extend(dispatched_songs)

        async with aiofiles.open(file_name, 'w') as f:
            await f.write(json.dumps(data, indent=4))

    @tasks.loop(seconds=60)
    async def dispatch_songs(self):
        print("Dispatching happening every:", self.dispatch_frequency, "seconds")
        
        dispatched_songs = self.buffer.apply_to(self.queue)
        if not dispatched_songs:
            return

        send_channel = discord.utils.get(self.bot.get_all_channels(), name=self.output_channel)

        for song in dispatched_songs:
            print("Attempring to send the song:", song['link']," of team:", song['team'], "to youtube" )
            try:
                print("The song was submitted")
                self.youtube_service.add_video_to_playlist(song['link'])
                content = (
                    f"🎶 **Canción en fila**\n"
                    f"**Link**: {song['link']}\n"
                    f"**Del equipo**: #{song['team']}\n"
                    f"**A las**: {song['timestamp']} UTC"
                )
                if send_channel:
                    await send_channel.send(content)
            except Exception as e:
                print("Problems sending the song")


                managment_channel = discord.utils.get(self.bot.get_all_channels(), name=self.managment_channel)
                error_message = f"⚠️ Error adding video: {e}"
                print(error_message)
                if managment_channel:
                    await managment_channel.send(error_message)

        await self.write_dispatched_songs(dispatched_songs)

    @dispatch_songs.before_loop
    async def before_dispatch_songs(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(MusicDispatcherCog(bot))
