import discord
import os
from dotenv import load_dotenv
from bot.events import setup_events
import yaml

class BotCore:
    def __init__(self):
        load_dotenv()
        self.token = os.getenv("DISCORD_TOKEN")
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        with open("configs/config.yaml") as f:
            self.config = yaml.safe_load(f)

    def run(self):
        setup_events(self.client, self.config)
        self.client.run(self.token)
