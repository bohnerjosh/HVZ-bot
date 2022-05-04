import os
import discord

TOKEN = os.environ["DISCORD_TOKEN"]
client = discord.Client()

@client.event
async def on_ready():
    print("Hello world!")

client.run(TOKEN)
