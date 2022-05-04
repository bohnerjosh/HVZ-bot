import os
import discord
from database import Database
from pathlib import Path

DATABASE_NAME = "db"
TOKEN = os.environ["DISCORD_TOKEN"]
client = discord.Client()

parent_dir = Path( __file__ ).parent.resolve()
db = Database(str(parent_dir / DATABASE_NAME))

@client.event
async def on_ready():
    print("Hello world!")

client.run(TOKEN)
