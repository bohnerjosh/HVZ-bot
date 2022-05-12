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
        return "error", "null"

    result = result[0]
    db.human_to_zombie(username, result)    
    return "ok", result

def stun(message):
    message_lst = message.split()
    if len(message_lst) != 3:
        return "msg_len"
    shooter = message_lst[1]
    victim = message_lst[2]

    verify_shooter = db.has_user_id(shooter)
    verify_victim = db.has_user_id(victim)

    if len(verify_shooter) == 0 or len(verify_victim) == 0:
         return "f_usr_match"

    shooter = verify_shooter[0]
    victim = verify_victim[0]
   
    if shooter.status == "Zombie" or victim.status == "Human":
        return "f_stun_human"

    db.add_stun(shooter, victim)
    return "ok"    

def get_profile(server, username):
    for user in server.members:
        if str(user) == username:
            return user

@client.event
async def on_ready():
    print("Hello world!")

@client.event
async def on_message(message):
    username = str(message.author)
    user = message.author
    user_message = str(message.content)

    if user_message.startswith("!create"):
        print(username)
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
        result, victim = zombieify(username, code)
        if result == "error":
            await message.channel.send("Bad killcode or user doesn't exist")
        else:
            await message.channel.send(f"Zombieified {victim.username}")

            guild = client.get_guild(GUILD_ID)
            victim_discord_profile = get_profile(guild, victim.username)
            zombie_role = discord.utils.get(guild.roles, name="Zombie")
            human_role = discord.utils.get(guild.roles, name="Human")

            await victim_discord_profile.remove_roles(human_role)
            await victim_discord_profile.add_roles(zombie_role)

    elif user_message.startswith("!stun"):
        result = stun(user_message)
        if not result == "ok":
            if result == "msg_len":
                await message.channel.send("Invalid stun message syntax")
            elif result == "f_usr_match":
                await message.channel.send(f"Cannot log stun with message: {user_message}")
                await message.channel.send("stunner or person stunned does not exist")
            elif result == "f_stun_human":
                await message.channel.send("Stunner cannot be a zombie. Additionally, only zombies can be stunned")
        
        else:
            await message.channel.send(f"Logged stun")
    
    elif user_message.startswith("!ids"):
        out_str = "Players and their ids:\n"
        result = db.get_user_ids()
        for player in result:
            out_str += "    " + str(player.id) + " : " + player.username + "\n"

        out_str += "===END==="

        await message.channel.send(out_str)
client.run(TOKEN)
