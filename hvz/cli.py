import os
import discord
from discord.ext import commands
from hvz.database import Database
from hvz.config import Config
from hvz.hvz import HVZ
from pathlib import Path
from random import choice
import string
from datetime import datetime

# Discord API stuff
TOKEN = os.environ["DISCORD_TOKEN"]
intents = discord.Intents.all()
intents.members = True
intents.guilds = True

# program specific variables
PROGNAME = "hvz"
WORKING_DIR = Path.home()

config = Config(WORKING_DIR)
db = Database(config)
hvz = HVZ(db, config)
COMMAND_PREFIX = config.params["prefix"]
MODS = ["The_Pro_Legion#7667"]

client = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

class CLI(object):
    
    def run(self):
        client.run(TOKEN)

    @client.event
    async def on_ready():
        print("Hello world!")

    @client.command(name="create", help="dumbass")
    async def create_user(ctx):
        username = str(ctx.author)
        
        result, data = hvz.create_user(username)
        if result == "error":
            await ctx.send("Already a user")
            await ctx.author.send(f"Remember, your code is {data}")
        else:
            await ctx.send("User created")
            await ctx.author.send(f"Your code is {data}")
        
            guild = ctx.guild
            new_role = discord.utils.get(guild.roles, name="Human")

            await ctx.author.add_roles(new_role)
            
    @client.command(name="code", help="Get your killcode")
    async def get_user_killcode(ctx, *args):
        if len(args) < 1:
            await ctx.send("Invalid killcode syntax")
            return
        username = str(ctx.author)
        user = ctx.author
        code = args[0]
        result, victim = hvz.zombieify(username, code)
        if result == "error":
            await ctx.send("Bad killcode or user doesn't exist")
        else:
            await ctx.send(f"Zombieified {victim.username}")

            guild = ctx.guild
            victim_name, disc = hvz.name_split(victim.username)

            victim_profile = discord.utils.get(guild.members, name=victim_name, discriminator=disc)
            zombie_role = discord.utils.get(guild.roles, name="Zombie")
            human_role = discord.utils.get(guild.roles, name="Human")

            await victim_profile.remove_roles(human_role)
            await victim_profile.add_roles(zombie_role)

    @client.command(name="stun", help="Report a stunned zombie")
    async def get_user_killcode(ctx, *args):
        if len(args) < 1:
            await ctx.send("Invalid stun syntax")
            return
        result = hvz.stun(list(args))
        if not result == "ok":
            if result == "msg_len":
                await ctx.send("Invalid stun message syntax")
            elif result == "f_usr_match":
                await ctx.send("Cannot log stun with message: ")
                await ctx.send("stunner or person stunned does not exist")
            elif result == "f_stun_human":
                await ctx.send("Stunner cannot be a zombie. Additionally, only zombies can be stunned")
        else:
            await ctx.send(f"Logged stun")
        
    @client.command(name="ids", help="Get ids of users")
    async def get_ids(ctx):
        out_str = "```==Players and their ids==\n"
        result = db.get_user_ids()
        for player in result:
            out_str += "    " + str(player.id) + " : " + player.username + "\n"

        out_str += "==END==```"

        await ctx.send(out_str)

    @client.command(name="stats", help="Get ids of users")
    async def get_player_statistics(ctx):
        username = str(ctx.author)
        result = hvz.check_player(username)
        if not result:
            await ctx.send("You are not registered. Please register to track stats") 
        else:
            await ctx.send("Sending stats to DM")
            player, tags, stuns, tagger = db.get_stats(username)
            time_alive = hvz.get_time_alive(player)
            
            out_text = f"```==Player statistics for {player.username}==\n\n"
            out_text += "   Current status: " + player.status + "\n"
            out_text += "   Time as human: " + time_alive + "\n"
            
            if player.status == "Human":
                out_text += "\n    --Stuns--\n"
                if len(stuns) == 0:
                    out_text += "   No data\n"
                else:
                    for player in stuns:
                        out_text += f"    You stunned {player} {stuns[player]} time(s)\n"
                out_text += "\n==END==```"

            else:
                out_text += "\n    --Stuns--\n"
                for player in stuns:
                     out_text += f"    You were stunned by {player} {stuns[player]} time(s)\n"
                
                out_text += "\n    --Tags--\n"
                if len(tags) == 0:
        
                    out_text += "    No data\n"
                else:
                    for player in tags:
                        out_text += f"    You tagged {player} {tags[player]} time(s)\n"

                out_text += f"\n    You were turned into a zombie by {tagger}\n"
                out_text += "\n==END==```"

            await ctx.author.send(out_text)
    
    @client.command(name="mcreate", help="Create a mission")
    async def initialize_mission(ctx, *args):
        text = "".join(args)
        username = str(ctx.author)
        result = hvz.check_player(username)
        
        if not result:
            await ctx.send("You must be registered to create missions") 
            return

        if not username in MODS:
            await ctx.send("You do not have permission to create missions") 
            return

        result = hvz.create_mission(text)
        await ctx.send(f"Mission created with id: {result}") 
    
    @client.command(name="missions", help="Get all missions")
    async def get_missions(ctx):
        
        username = str(ctx.author)
        if not username in MODS:
            await ctx.send("You do not have permission to create missions") 
            return

        missions = db.get_missions()
        out_text = "```==Missions==\n\n"
        for mission in missions:
            out_text += f"id: {mission} | header text:\n"
            out_text += missions[mission] + "\n\n"

        out_text += "==END OF MISSIONS==```"
        await ctx.send(out_text)

    @client.command(name="mget", help="Get a singular mission")
    async def get_mission(ctx, *args):
        if len(args) < 1:
            await ctx.send("Invalid mission get syntax")
            return
        
        mission_id = args[0]
        username = str(ctx.author)
        if not username in MODS:
            await ctx.send("You do not have permission to create missions") 
            return
        result = hvz.get_mission(mission_id)
        if result == "error":
            await ctx.send("No mission with that id") 
            return
        out_text = f"```==MISSION TEXT==\n\n"
        out_text += result + "\n\n==END MISSION TEXT==```"
        
        await ctx.send(out_text)

 
    @client.event
    async def on_message(message):
        username = str(message.author)
        user = message.author
        user_message = str(message.content)

        await client.process_commands(message)
