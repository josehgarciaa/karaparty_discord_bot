from services.link_manager import LinkManager
from services.queue_manager import QueueManager
import discord
import asyncio
from datetime import timedelta

def setup_events(client, config):
    queue = QueueManager()
    link_manager = LinkManager()
    category_name = config["karaparty_category"]
    send_channel_name = config["send_songs_channel"]

    @client.event
    async def on_ready():
        print(f'Logged in as {client.user}')

    @client.event
    async def on_message(message):
        if message.author.bot:
            return
        if message.channel.category and message.channel.category.name == category_name:
            valid, link = link_manager.validate_message(message.content)
            if not valid:
                await message.delete()
                await message.channel.send(f"{message.author.mention} Invalid message. Exactly one YouTube link allowed.", delete_after=5)
                return
            queue.add_link(link, message.author, message.channel, message.created_at)

    async def dispatch_songs():
        await client.wait_until_ready()
        send_channel = discord.utils.get(client.get_all_channels(), name=send_channel_name)
        while not client.is_closed():
            if not queue.is_empty():
                song = queue.pop_link()
                await send_channel.send(f"🎶 **Song Added**\n**Link**: {song['link']}\n**Posted by**: {song['user']}\n**Channel**: #{song['channel']}\n**Time**: {song['timestamp']} UTC")
            await asyncio.sleep(30)

    async def setup_hook():
        client.loop.create_task(dispatch_songs())

    client.setup_hook = setup_hook
    
