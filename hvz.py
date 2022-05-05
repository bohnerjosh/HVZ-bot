import os
import discord
from database import Database
from pathlib import Path
from random import choice
import string
from datetime import datetime

DATABASE_NAME = "db"
GUILD_ID = 871424085064810516
TOKEN = os.environ["DISCORD_TOKEN"]
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

parent_dir = Path( __file__ ).parent.resolve()
db = Database(str(parent_dir / DATABASE_NAME))

def generate_killcode(codes):
    code = "".join(choice(string.ascii_lowercase) for _ in range(6))
    while True:
        if code in codes:
            code = "".join(choice(string.ascii_lowercase) for _ in range(6))
        return code

def create_user(username):
    print("Creating user...")
    
    # check to see if the user is already registered
    result = db.has_user(username)
    if len(result) > 0:
        user = result[0]
        killcode = user.killcode
        print(f"That user already exists.")
        return "error", killcode

    all_codes = db.get_killcodes()
    new_code = generate_killcode(all_codes)
    db.init_player(username, new_code)

    return "ok", new_code

def zombieify(username, code):
    result = db.has_user_code(code)
    if not len(result) > 0:
        return "error"

    db.human_to_zombie(result[0])    
    return "ok"

@client.event
async def on_ready():
    print("Hello world!")

@client.event
async def on_message(message):
    username = str(message.author)
    user = message.author
    user_message = str(message.content)

    print(f"[{user_message}]")

    if user_message.startswith("!create"):
        result, data = create_user(username)
        if result == "error":
            await message.channel.send("Already a user")
            await message.author.send(f"Remember, your code is {data}")
        else:
            await message.channel.send("User created")
            await message.author.send(f"Your code is {data}")
    
            guild = client.get_guild(GUILD_ID)
            new_role = discord.utils.get(guild.roles, name="Human")

            await user.add_roles(new_role)

    elif user_message.startswith("!code"):
        code = user_message[6:12]
        result = zombieify(username, code)
        if result == "error":
            await message.channel.send("Bad killcode or user doesn't exist")
        else:
            await message.channel.send(f"Zombieified {username}")

            guild = client.get_guild(GUILD_ID)
            zombie_role = discord.utils.get(guild.roles, name="Zombie")
            human_role = discord.utils.get(guild.roles, name="Human")

            await user.remove_roles(human_role)
            await user.add_roles(zombie_role)

client.run(TOKEN)
