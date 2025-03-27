from services.link_manager import LinkManager
from services.queue_manager import QueueManager
from services.youtube_service import YouTubeService
import discord
import asyncio
from datetime import timedelta

def setup_events(client, config):
    category_name = config["karaparty_category"]
    monitored_channels = config["monitored_channels"] 
    output_channel = config["output_channel"]
    client_secret_file=config["youtube"]["client_secret_file"]
    credentials_file=config["youtube"]["credentials_file"]
    playlist_id=config["youtube"]["playlist_id"]
    wrong_message_warning= config["wrong_content_message"]

    queue_songs = [] 

    queue = QueueManager()
    link_manager = LinkManager()
    youtube_service = YouTubeService(   client_secret_file=client_secret_file,
                                        credentials_file=credentials_file,
                                        playlist_id=playlist_id
                                        )

    @client.event
    async def on_ready():
        print(f'Logged in as {client.user}')
        for guild in client.guilds:
            print(f'Connected to server: {guild.name}')
            # Sending a welcome message to a specific channel (if needed)
            default_channel = discord.utils.get(guild.text_channels, name=output_channel)
            if default_channel:
                await default_channel.send(f"🚀 Bot is now online and connected to **{guild.name}**!")


    @client.event
    async def on_message(message):
        if message.author.bot:
            return
        
        
        if message.channel.category.name == category_name and message.channel.name in monitored_channels: 
            print(message.content)
        
            valid, link = link_manager.validate_message(message.content)
            if not valid:
                await message.delete()
                await message.channel.send(f"{message.author.mention} Error: "+wrong_message_warning, delete_after=5)
                return
            
            if queue.is_in_queue(link) :
                await message.delete()
                await message.channel.send(f"{message.author.mention} Error: La canción ya está en fila. Escoge otra", delete_after=20)
                return
            
            queue.add_link(link, message.author, message.channel, message.created_at)

    async def dispatch_songs():
        await client.wait_until_ready()
        send_channel = discord.utils.get(client.get_all_channels(), name=output_channel)
        while not client.is_closed():
            if not queue.is_empty():
                song = queue.get_link()
                if song:
                    try:
                        youtube_service.add_video_to_playlist(song['link'])
                        await send_channel.send(
                            f"🎶 **Cancion en fila**\n**Link**: {song['link']}\n"
                            f"**Agregada por**: {song['user']}\n"
                            f"**Del equipo**: #{song['channel']}\n"
                            f"**A las**: {song['timestamp']} UTC"
                        )
                    except Exception as e:
                        error_message = f"⚠️ Error adding video to playlist: {e}\n"
                        print(error_message)
                        await send_channel.send(f"⚠️ Failed to add video {song['link']} to playlist. Error: {str(e)}")
                        raise
            await asyncio.sleep(10)

    async def setup_hook():
        client.loop.create_task(dispatch_songs())

    client.setup_hook = setup_hook
    
