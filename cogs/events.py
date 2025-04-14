from typing import Any
import discord
from discord.ext import commands
from services.link_manager import LinkManager
from services.queue.queue_buffer import QueueBuffer  # Our new buffer
from services.queue.queue_manager import QueueManager       # Our new live queue manager

import utils.warning_reporter as warning 

class EventCog(commands.Cog):
    """
    Cog responsible for handling core Discord events:
      - on_message: when a message is sent, validate and stage an "add" operation.
      - on_message_delete: when a message is deleted, stage a "delete" operation.
      - on_message_edit: when a message is edited, stage a "replace" operation.
    All actions are sent to QueueBuffer so that they can be applied in batch later.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Initializes the EventCog with configuration, QueueManager, and QueueBuffer.
        
        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot: commands.Bot = bot
        self.config: dict[str, Any] = bot.config

        # The staging buffer for operations (add/delete/replace)
        self.buffer: QueueBuffer = bot.queue_buffer
        self.queue: QueueManager = bot.queue

        # Link manager to validate YouTube links
        self.link_manager: LinkManager = LinkManager()

        # Configuration details
        self.category_name: str = self.config["bot"]["monitored_category"]
        self.monitored_channels: list[str] = self.config["bot"]["monitored_channels"]
        self.output_channel: str = self.config["bot"]["output_channel"]
        self.notification_channel: str = self.config["bot"]["notification_channel"]

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        Runs when the bot is fully connected and ready.
        Announces readiness in the configured notification channel.
        """
        print(f'Logged in as {self.bot.user}')
        for guild in self.bot.guilds:
            print(f'Connected to server: {guild.name}')
            default_channel: discord.TextChannel | None = discord.utils.get(
                guild.text_channels,
                name=self.notification_channel
            )
            if default_channel:
                await default_channel.send(
                    f"KaraParty bot está listo para operar en el servidor **{guild.name}**!"
                )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        When a message is sent in a monitored channel (within the monitored category),
        validates its content. If it's a valid YouTube link and not a duplicate (as
        determined by checking the live queue), the operation is staged as an "add" 
        in the QueueBuffer.
        
        Args:
            message (discord.Message): The received message.
        """
        if message.author.bot:
            return

        # Check that the message is in the correct category and channel.
        in_karaoke_category = (message.channel.category and 
                               message.channel.category.name == self.category_name)
        in_monitored_channel = message.channel.name in self.monitored_channels
        team_name = message.channel.name

        if in_karaoke_category and in_monitored_channel:
            valid, link = self.link_manager.validate_message(message.content)
            if not valid:
                await message.delete()
                await warning.discord_invalid_message(
                                                user=message.author,
                                                channel=message.channel,
                                                delete_after=20)                
                return

            if self.queue.is_dispatched(link, team_name):
                await message.delete()
                await warning.discord_repeated_song( user=message.author,
                                                     channel=message.channel,
                                                     delete_after=20)                
            else:
                # Stage the addition operation to the buffer.
                status_message  = self.buffer.add_song(team_name, link)
                if not status_message["success"]:
                    await message.delete()
                    await warning.discord_repeated_song( user=message.author,
                                                        channel=message.channel,
                                                        delete_after=20)  
                else:
                    print(f"[EventCog] Staged add song {link} for team {team_name}.")

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """
        When a message is deleted from a monitored channel within the monitored category,
        if the message contained a valid YouTube link, stage a delete operation in the
        QueueBuffer. 

        Args:
            message (discord.Message): The deleted message.
        """
        if message.author.bot:
            return

        in_karaoke_category = (message.channel.category and 
                               message.channel.category.name == self.category_name)
        in_monitored_channel = message.channel.name in self.monitored_channels

        if in_karaoke_category and in_monitored_channel:
            team_name = message.channel.name
            valid, link = self.link_manager.validate_message(message.content)
            if valid:
                # Stage a delete operation in the buffer.
                status_message  =self.buffer.delete_song(team_name, link)
                if not status_message["success"]:
                    await warning.discord_delete_dispatched( user=message.author,
                                                        channel=message.channel,
                                                        delete_after=20)                
                else:
                    print(f"[EventCog] Staged deletion of song {link} for team {team_name}.")

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        """
        When a message is edited in a monitored channel, if the content changes from a
        valid YouTube link to another valid YouTube link, stage a replacement operation
        in the QueueBuffer.
        
        Args:
            before (discord.Message): The original message.
            after (discord.Message): The edited message.
        """
        if before.author.bot:
            return

        if (before.channel.category and 
            before.channel.category.name == self.category_name and 
            before.channel.name in self.monitored_channels):
            # Only consider edits if the content has changed.
            if before.content == after.content:
                return

            # Validate both the old and new content.
            valid_before, old_link = self.link_manager.validate_message(before.content)
            valid_after, new_link = self.link_manager.validate_message(after.content)
            team_name = before.channel.name

            if not (valid_before and valid_after):
                await after.delete()
                await warning.discord_invalid_message(
                                                user=after.author,
                                                channel=after.channel,
                                                delete_after=20)                
                if valid_before:
                    status_message  =self.buffer.delete_song(team_name, old_link)
                    if not status_message["success"]:
                        print("[EventCog]  Failed to delete song from buffer.")                        
                    else:
                        print(f"[EventCog] Staged deletion of song {old_link} for team {team_name} due to wrong edit.")

                return

            # If both are valid YouTube links, stage a replacement.
            status_message = self.buffer.replace_song(team_name, old_link, new_link)
            if not status_message["success"]:
                await warning.discord_edit_dispatched( user=after.author,
                                                         channel=after.channel,
                                                         delete_after=20)                
            else:
                print(f"[EventCog] Staged replacement in team {team_name}: {old_link} -> {new_link} ")

async def setup(bot: commands.Bot) -> None:
    """
    Entrypoint for loading the EventCog into the bot.
    
    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(EventCog(bot))
