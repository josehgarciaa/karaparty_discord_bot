from typing import Any
import discord
from discord.ext import commands
from services.smartbot_service import SmartBotService
from pydantic import BaseModel
from typing import Optional
from pydantic import BaseModel
from pydantic import Field

class ValidationFormat(BaseModel):
    name: Optional[str] = Field(description="Nombre, pueden usarse pseudonimos")
    city: Optional[str] = Field(description="Una ciudad, pais o ambos")
    age: Optional[int] = Field(description="La edad, ha de ser mayor de edad para ser valido")
    finding_us: Optional[str] = Field(description="Donde ha encontrado la comunidad")
    interest: Optional[str] = Field(description="Que intereses o aficiones tiene")
    job: Optional[str] = Field(description="De que trabajan")
    platform: Optional[str] = Field(description="Que plataformas de juegos o entretenmiento utilizand")
    anime: Optional[str] = Field(description="Los animes o mangas favoritos")
    additional: Optional[str] = Field(description="Cualquier informacion adicional que quieran enviar")
    is_valid: bool = Field(description="Si los datos son todos válidos regresa verdadero")
    output_message: str 


class PresentationManagerCog(commands.Cog):
    """
    A cog that listens for messages in a target channel within a specific category.
    When a message passes the `validator` check, it assigns a predetermined role to
    the user and sends a confirmation message.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """

        Args:
            bot (commands.Bot): The bot instance this cog is attached to.
        """
        self.bot = bot
        # Read configuration values from bot.config
        self.target_channel: str = bot.config["bot"]["presentation_channel"]  # e.g., "presentation"
        self.assign_role: str = bot.config["bot"]["starting_role"]  # Role to assign if validated
        self.previous_role: str = "Kai Oculto"
        self.instruction: str = bot.config["smart_bot"]["presentation_instruction"]
        self.smart_bot_key: str = bot.config["smart_bot"]["deepseek_key"]
        
    def validator(self, message: discord.Message) -> bool:
        smart_bot_agent  = SmartBotService(self.smart_bot_key)
        print(message.content)
        response = smart_bot_agent.validate_text(self.instruction, message.content, ValidationFormat)
        print(response)

        return (response["is_valid"], response["output_message"])

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Event handler that processes messages from the target channel within the target category.
        If the message passes the validator check, assigns a role to the user and sends a confirmation message.

        Args:
            message (discord.Message): The incoming message event from Discord.
        """
        # Ignore messages from bots.
        if message.author.bot:
            return

        # Ensure the message is from a channel that belongs to a category.
        if not message.channel.category:
            return

        # Check if the message is in the designated target channel and category.
        if (message.channel.name != self.target_channel):
            return

        # Validate the message using the validator function.
        is_valid = False 
        output_message = ""
        is_valid, output_message = self.validator(message)
        
        if is_valid:
            # Find the role in the guild by name.
            new_role = discord.utils.get(message.guild.roles, name=self.assign_role)
            old_role = discord.utils.get(message.guild.roles, name=self.previous_role)
            if new_role is None:
                print(f"[RoleAssigner] Role '{self.assign_role}' not found in guild '{message.guild.name}'.")
                return
            try:
                # Assign the role to the user.
                await message.author.remove_roles(old_role)
                await message.author.add_roles(new_role)
                # Send a confirmation message that auto-deletes after 30 seconds.
                await message.channel.send(f"{message.author.mention} {output_message}")
                print(f"[RoleAssigner] Assigned role '{role.name}' to user {message.author} and sent confirmation.")
                return 
            except discord.Forbidden:
                print(f"[RoleAssigner] Missing permissions to assign role '{role.name}' to user {message.author}.")
            except discord.HTTPException as e:
                print(f"[RoleAssigner] Failed to assign role or send message: {e}")
        if not is_valid:
            print("No es válido")
            await message.channel.send(f"{message.author.mention} {output_message}")


async def setup(bot: commands.Bot) -> None:
    """
    Entrypoint for loading the cog into the bot.

    Args:
        bot (commands.Bot): The bot instance to attach the cog to.
    """
    await bot.add_cog(PresentationManagerCog(bot))
