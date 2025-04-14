# utils/warning_handler.py

import discord
from discord.ext import commands

# Centralized warning messages dictionary (in English).
WARNING_MESSAGES = {
    "repeated_song": "Error: La canción ya se encuentra en la fila de tu equipo. Por favor escoge otra.",
    "unwanted_channel": "Error: No puedes escribir en este canal.",
    "invalid_message": "Error: El mensaje enviado no es un link de Youtube, o no tiene el formato correcto.",
    "delete_dispatched_song": "Error: La canción ya se ha enviado a la playlist, no se puede eliminar mas.",
    "edit_dispatched_song": "Error: La canción ya se ha enviado a la playlist, no se puede editar mas."
}

async def warn_user( 
                    user: discord.User,
                    channel: discord.TextChannel,
                    warning_key: str,
                    delete_after: int = 30
                    ) -> None:
    """
    Sends a warning message to a user in a specified channel.
    
    The message is automatically deleted after the specified number of seconds.
    
    Args:
        user (discord.User): The user to warn.
        channel (discord.TextChannel): The channel in which to send the warning.
        warning_key (str): The key to look up the warning message (e.g., "repeated_song" or "unwanted_channel").
        delete_after (int, optional): Time in seconds after which the warning message is auto-deleted. Defaults to 30.
    """
    message_text = WARNING_MESSAGES.get( warning_key, "Ha ocurrido un error desconocido, consulta a alguno de los administradores." )
    content = f"{user.mention} {message_text}"
    try:
        await channel.send(content, delete_after=delete_after)
    except discord.Forbidden:
        print(f"[WARNING_HANDLER] Internal error (for the admins) Missing permission to send messages in #{channel.name}")
    except discord.HTTPException as e:
        print(f"[WARNING_HANDLER] Internal error (for the admins) Failed to send warning message: {e}")

async def discord_repeated_song( user: discord.User,
                              channel: discord.TextChannel,
                              delete_after: int = 30
                            ) -> None:
    """
    Convenience wrapper to warn a user about a repeated song.
    
    Args:
        user (discord.User): The user to warn.
        channel (discord.TextChannel): The channel in which to send the warning.
        delete_after (int, optional): Number of seconds after which the warning is auto-deleted. Defaults to 30.
    """
    await warn_user(user, channel, "repeated_song", delete_after)

async def discord_unwanted_channel( user: discord.User,
                                 channel: discord.TextChannel,
                                 delete_after: int = 30
                                 ) -> None:
    """
    Convenience wrapper to warn a user about writing in an unwanted channel.
    
    Args:
        user (discord.User): The user to warn.
        channel (discord.TextChannel): The channel in which to send the warning.
        delete_after (int, optional): Number of seconds after which the warning is auto-deleted. Defaults to 30.
    """
    await warn_user(user, channel, "unwanted_channel", delete_after)

async def discord_invalid_message( user: discord.User,
                                 channel: discord.TextChannel,
                                 delete_after: int = 30
                                 ) -> None:
    await warn_user(user, channel, "invalid_message", delete_after)

async def discord_delete_dispatched( user: discord.User,
                                 channel: discord.TextChannel,
                                 delete_after: int = 30
                                 ) -> None:
    await warn_user(user, channel, "delete_dispatched_song", delete_after)

async def discord_edit_dispatched( user: discord.User,
                                   channel: discord.TextChannel,
                                   delete_after: int = 30
                                   ) -> None:
    await warn_user(user, channel, "edit_dispatched_song", delete_after)
    

