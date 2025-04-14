import discord
from discord.ext import commands
import yaml

from utils.error_reporter import report_error
from services.queue.queue_manager import QueueManager
from services.queue.queue_buffer import QueueBuffer


class KarapartyBot(commands.Bot):
    """
    Custom bot class for the KaraParty Discord bot.

    This bot loads configuration from a YAML file, initializes shared components 
    such as the QueueManager and QueueBuffer, and loads the necessary cogs.
    """

    def __init__(self, config_file: str) -> None:
        """
        Initializes the bot by loading configuration, creating shared components,
        and setting up Discord intents.

        Args:
            config_file (str): The path to the configuration YAML file.
        """
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            report_error(e, context="Please, remember to fill your configs/config.yaml file. Template is at config.yaml.template")
            raise e  # Stop startup if config cannot be loaded

        # Initialize the shared queue and queue buffer
        self.queue: QueueManager = QueueManager()
        self.queue_buffer: QueueBuffer = QueueBuffer()

        # Setup Discord intents: enable what we need (message content, guilds, messages)
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.messages = True

        # Initialize the base commands.Bot class
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        """
        Asynchronously loads all cogs during bot startup.
        """
        await self.load_extension("cogs.events")
        await self.load_extension("cogs.music_dispatcher")
        #await self.load_extension("cogs.message_guard")

    def run_bot(self) -> None:
        """
        Starts the bot using the Discord token from the configuration file.
        """
        token = self.config["discord"]["token"]
        self.run(token)


if __name__ == "__main__":
    bot = KarapartyBot("configs/config.yaml")
    bot.run_bot()
