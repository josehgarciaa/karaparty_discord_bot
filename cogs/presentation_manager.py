from typing import Optional, Tuple
import discord
from discord.ext import commands
from services.smartbot_service import SmartBotService
from pydantic import BaseModel, Field

class ValidationFormat(BaseModel):
    name: Optional[str] = Field(description="Nombre, pueden usarse pseudónimos")
    city: Optional[str] = Field(description="Una ciudad, país o ambos")
    age: Optional[int] = Field(description="La edad, ha de ser mayor de edad para ser válido")
    finding_us: Optional[str] = Field(description="Dónde ha encontrado la comunidad")
    interest: Optional[str] = Field(description="Qué intereses o aficiones tiene")
    job: Optional[str] = Field(description="De qué trabajan")
    platform: Optional[str] = Field(description="Qué plataformas de juegos o entretenimiento utilizan")
    anime: Optional[str] = Field(description="Los animes o mangas favoritos")
    additional: Optional[str] = Field(description="Cualquier información adicional que quieran enviar")
    is_valid: bool = Field(description="Si los datos son todos válidos regresa verdadero")
    output_message: str = Field(description="Mensaje claro indicando si es válido o no y por qué en español")


class PresentationManagerCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.target_channel = bot.config["bot"]["presentation_channel"]
        self.assign_role = bot.config["bot"]["starting_role"]
        self.previous_role = "Kai Oculto"
        self.smart_bot_key = bot.config["smart_bot"]["deepseek_key"]

        self.instruction = """
        Valida la siguiente información:
        - Todos los campos excepto 'additional' deben estar completos.
        - La edad debe ser mayor o igual a 18.
        - Ningún campo debe contener lenguaje ofensivo, obscenidades o insultos.
        
        Devuelve siempre una respuesta con:
        - is_valid: verdadero sólo si cumple con todo, falso en caso contrario.
        - output_message: Mensaje claro y amable en español explicando si la información es válida o indicando exactamente qué falla y cómo corregirlo.
        """

    def validator(self, message: discord.Message) -> Tuple[bool, str]:
        smart_bot_agent = SmartBotService(self.smart_bot_key)
        response = smart_bot_agent.validate_text(self.instruction, message.content, ValidationFormat)

        return response.is_valid, response.output_message

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.channel.category:
            return

        if message.channel.name != self.target_channel:
            return

        is_valid, output_message = self.validator(message)

        if is_valid:
            new_role = discord.utils.get(message.guild.roles, name=self.assign_role)
            old_role = discord.utils.get(message.guild.roles, name=self.previous_role)
            if not new_role:
                print(f"[RoleAssigner] No encontré el rol '{self.assign_role}'")
                return

            try:
                await message.author.remove_roles(old_role)
                await message.author.add_roles(new_role)
                await message.channel.send(f"{message.author.mention} ✅ {output_message}", delete_after=30)

            except discord.Forbidden:
                print(f"[RoleAssigner] Sin permisos para asignar '{self.assign_role}'")
            except discord.HTTPException as e:
                print(f"[RoleAssigner] Error al asignar rol o enviar mensaje: {e}")

        else:
            await message.channel.send(f"{message.author.mention} ❌ {output_message}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PresentationManagerCog(bot))
