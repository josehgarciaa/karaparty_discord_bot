from typing import Any
import discord
from discord.ext import commands


class MessageGuardCog(commands.Cog):
    """
    A cog that monitors messages inside a specific category and deletes any
    message that is not posted in an explicitly allowed channel. Sends a warning
    to the user that auto-deletes after 30 seconds.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Initializes the MessageGuardCog.

        Args:
            bot (commands.Bot): The bot instance this cog is attached to.
        """
        self.bot = bot

        # Read configuration values
        self.allowed_channels: list[str]= bot.config["bot"]["monitored_channels"] + bot.config["bot"]["free_talk_channels"]
        self.monitored_category: str = bot.config["bot"]["monitored_category"]
        self.warning_message: str = "Cant write here"

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Event handler that deletes messages not in allowed channels inside the
        monitored category and sends a warning to the user.

        Args:
            message (discord.Message): The incoming message event from Discord.
        """
        if message.author.bot:
            return  # Ignore bot messages

        # Ignore messages outside the target category
        if not message.channel.category:
            return

        if message.channel.category.name != self.monitored_category:
            return


        # Get the part of the channel name up to the last separator (including it)
        def get_channel_prefix(channel_name):
            parts = channel_name.split('︱')
            # Check if there are at least 3 parts: something like 🎤equipo︱number︱
            if len(parts) >= 3 and parts[1].isdigit():
                # Rebuild the prefix up to and including the second separator
                return '︱'.join(parts[:2]) + '︱'
            return channel_name  # Return as is if the structure is not matched
        formated_channel_name = get_channel_prefix(message.channel.name)


        # Check if channel is NOT in the allowed list
        if formated_channel_name not in self.allowed_channels:
            try:
                await message.delete()
                await message.channel.send(
                    f"{message.author.mention} {self.warning_message}",
                    delete_after=30
                )
                print(f"[Guard] Deleted message from {message.author} in #{message.channel.name}")
            except discord.Forbidden:
                print(f"[Guard] Missing permissions to delete/warn in #{message.channel.name}")
            except discord.HTTPException as e:
                print(f"[Guard] Failed to delete or warn: {e}")


async def setup(bot: commands.Bot) -> None:
    """
    Entrypoint for loading the cog into the bot.

    Args:
        bot (commands.Bot): The bot instance to attach the cog to.
    """
    await bot.add_cog(MessageGuardCog(bot))
