import discord
from discord.ext import commands
import yaml

from  utils.error_reporter import report_error


class KarapartyBot(commands.Bot):# the self.run command is defined in commands.bot
    def __init__(self, config_file):
        try:
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            report_error(e, context=f"Please, remember to fill your configs/config.yaml file. Template is at config.yaml.template ")

        
        #This tell the bot what shall it listen to
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.messages = True

        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Load all cogs
        await self.load_extension('cogs.events')
        await self.load_extension('cogs.music_dispatcher')

    def run_bot(self):
        token = self.config['discord']['token']
        self.run(token)
