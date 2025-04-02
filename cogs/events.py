from typing import Any
import discord
from discord.ext import commands
from services.link_manager import LinkManager
from services.queue_manager import QueueManager


class EventCog(commands.Cog):
    """
    Cog responsible for handling core Discord events such as when the bot connects
    or receives a message in a monitored channel. It validates YouTube links and 
    manages the queue system for song submissions.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Initializes the EventCog and prepares services and configuration.

        Args:
            bot (commands.Bot): The bot instance to which this cog is attached.
        """
        self.bot: commands.Bot = bot
        self.config: dict[str, Any] = bot.config

        self.queue: QueueManager = QueueManager()
        self.link_manager: LinkManager = LinkManager()

        self.category_name: str = self.config["bot"]["karaparty_category"]
        self.monitored_channels: list[str] = self.config["bot"]["monitored_channels"]
        self.output_channel: str = self.config["bot"]["output_channel"]
        self.wrong_message_warning: str = self.config["bot"]["errors"]["content"]

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        Event listener that runs when the bot is fully connected and ready.

        Decorator: @commands.Cog.listener()
        This makes the method respond to the `on_ready` Discord event.
        """
        print(f'Logged in as {self.bot.user}')
        for guild in self.bot.guilds:
            print(f'Connected to server: {guild.name}')
            default_channel: discord.TextChannel | None = discord.utils.get(
                guild.text_channels,
                name=self.output_channel
            )
            if default_channel:
                await default_channel.send(
                    f"🚀 Bot is now online and connected to **{guild.name}**!"
                )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Event listener that runs whenever a message is sent in a channel.

        Validates whether the message is in a monitored karaoke channel. If valid,
        the message is checked for a YouTube link and added to the queue.
        If invalid, it is deleted and a warning is sent.

        Decorator: @commands.Cog.listener()
        This makes the method respond to the `on_message` Discord event.

        Args:
            message (discord.Message): The message object received from Discord.
        """
        if message.author.bot:
            return

        in_karaoke_category = (
            message.channel.category
            and message.channel.category.name == self.category_name
        )
        in_monitored_channel = message.channel.name in self.monitored_channels

        if in_karaoke_category and in_monitored_channel:
            valid, link = self.link_manager.validate_message(message.content)
            if not valid:
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention} Error: {self.wrong_message_warning}",
                    delete_after=5
                )
                return

            if self.queue.is_in_queue(link):
                await message.channel.send(
                    f"{message.author.mention} Error: La canción ya está en fila. Quizás quieras escoger otra.",
                    delete_after=20
                )
                return

            self.queue.add_link(
                link=link,
                user=message.author,
                channel=message.channel,
                timestamp=message.created_at
            )


async def setup(bot: commands.Bot) -> None:
    """
    Entrypoint for loading the EventCog into the bot.

    Args:
        bot (commands.Bot): The bot instance to attach the cog to.
    """
    await bot.add_cog(EventCog(bot))
