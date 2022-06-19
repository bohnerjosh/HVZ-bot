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
import requests

# Discord API stuff
TOKEN = os.environ["DISCORD_TOKEN"]
intents = discord.Intents.all()
intents.members = True
intents.guilds = True

# directory where program info is stored. Path.home() is the default
WORKING_DIR = Path.home()

# global class objects
config = Config(WORKING_DIR)
db = Database(config)
hvz = HVZ(db, config)

# Program specific globals
COMMAND_PREFIX = config.params["prefix"]
MODS = config.params["mods"]
CHECKMARK = "\U00002705"

client = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

class CLI(object):
    
    # the bot runs here
    def run(self):
        client.run(TOKEN)

    async def on_ready():
        print("Hello world!")

    # Command that initializes the player within HVZ. Generates a killcode and sends it
    #   to the player via DM
    @client.command(name="create", help="Register for HVZ")
    async def create_user(ctx):
        username = str(ctx.author)
        
        # create the player and killcode
        result, data = hvz.create_user(username)
        if result == "error":
            # prevent users from registering twice, remind them what their killcode is
            await ctx.send("Already a user")
            await ctx.author.send(f"Remember, your code is {data}")
        else:
            # inform the user what their killcode is
            await ctx.send("User created")
            await ctx.author.send(f"Your code is ``{data}``")
        
            # add the Human role to view human-specific channels
            guild = ctx.guild
            new_role = discord.utils.get(guild.roles, name="Human")

            await ctx.author.add_roles(new_role)

            msg = await ctx.author.send("If you would like to have a chance of being OZ (:zombie:), tap the check mark below this message")
            await msg.add_reaction(CHECKMARK)
            
    # Command that converts a human player to a zombie once they get tagged. Humans are uniquely
    #   identified for conversion via killcode
    @client.command(name="code", help="Convert to zombie")
    async def zombieify(ctx, *args):
        # check for correct command syntax
        if len(args) < 1:
            await ctx.send("Invalid killcode syntax")
            return

        # set up user and message data
        username = str(ctx.author)
        user = ctx.author
        code = args[0]

        # perform zombieification in hvz class
        result, victim = hvz.zombieify(username, code)
        if result == "error":
            # if bad killcode, inform user
            await ctx.send("Bad killcode or user doesn't exist")
        elif result == "illegal_zombieify":
            # if user tries to zombieify themselves or another human
            await ctx.send("Humans can't turn people into zombies")
        else:
            await ctx.send(f"Zombieified {victim.username}")

            # take away the human role and add the zombie role to the player
            guild = ctx.guild
            victim_name, disc = hvz.name_split(victim.username) # get the name and discriminator of discord username

            victim_profile = discord.utils.get(guild.members, name=victim_name, discriminator=disc)
            zombie_role = discord.utils.get(guild.roles, name="Zombie")
            human_role = discord.utils.get(guild.roles, name="Human")

            await victim_profile.remove_roles(human_role)
            await victim_profile.add_roles(zombie_role)

    # Command that allows humans to track zombies that they stun
    @client.command(name="stun", help="Report a stunned zombie")
    async def get_user_killcode(ctx, *args):
        # check command syntax
        if len(args) < 2:
            await ctx.send("Invalid stun syntax")
            return
        args = list(args)
        shooter = args[0]
        victim = args[1]
        result = hvz.stun(shooter, victim)
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
    
    @client.command(name="mission", help="Create a mission")
    async def connect_mission(ctx):
        username = str(ctx.author)
        result = hvz.check_player(username)
        
        if not result:
            await ctx.send("You must be registered to create missions") 
            return

        if not username in MODS or ctx.channel.id != config.params["mod_channel"]:
            await ctx.send("You do not have permission to create missions") 
    
            return

        if not ctx.message.attachments:
            await ctx.send("No file attached") 
            return

        attachment = ctx.message.attachments[0]
        attachment_url = attachment.url
        file_request = requests.get(attachment_url)
        file_text = file_request.content.decode("utf-8")
        file_name = attachment.filename
        
        m_id, result = hvz.handle_mission(file_name, file_text)

        if result == "init":
            await ctx.send(f"Mission created with id: {m_id}") 
        elif result == "modify":    
            await ctx.send(f"Mission modified with id: {m_id}") 
    
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
    
    @client.command(name="m-get", help="Get a singular mission")
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

    @client.command(name="make-live", help="Get all missions")
    async def live_mission(ctx, *args):
        if len(args) < 1:
            await ctx.send("Invalid live mission syntax")
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

        out_text = "__**NEW MISSION**__\n" + result
       
        channel = client.get_channel(config.params["missions_channel"]) 
        await channel.send(out_text)

    @client.command(name="m-end", help="Get all missions")
    async def mission_end(ctx, *args):
        if len(args) < 2:
            await ctx.send("Invalid live mission syntax")
            return

        try:
            mission_id = int(args[0])
            winner = args[1]
        except Exception:
            await ctx.send("Invalid command syntax")
            return

        result = hvz.determine_winner(mission_id, winner)

        if result == "invalid_mission":
            await ctx.send("That mission id does not exist")
            return
        elif result == "invalid_winner":
            await ctx.send("Invalid winner. Must be 'Human' or 'Zombie'")
            return

        out_text = f"Mission is over! The result: A {result} victory!"

        channel = client.get_channel(config.params["missions_channel"]) 
        await channel.send(out_text)

    @client.command(name="prefix", help="set the box prefix")
    async def live_mission(ctx, *args):
        if len(args) < 1:
            await ctx.send("Invalid command syntax")
            return

        prefix = args[0]
        username = str(ctx.author)
        prefix_length = len(prefix)
        if not prefix_length == 1:
            await ctx.send("Prefix must be a single character")
            return

        if not username in MODS:
            await ctx.send("You do not have permission to change the bot command prefix") 
            return
        config.update_prefix(prefix)
        ctx.send(f"Prefix changed to {prefix}. Restart the bot to apply this change")

    @client.event
    async def on_message(message):

        await client.process_commands(message)

    @client.event
    async def on_reaction_add(reaction, user):
        username = str(user)
        if reaction.emoji == CHECKMARK:
            usermatch = db.has_user(username)
            if len(usermatch) > 0 and isinstance(reaction.message.channel, discord.channel.DMChannel):
                db.add_to_OZ_lst(username)
                await user.send("You have been added to the list of potential humans to be the OZ")
                await user.send("You will be sent a message at the beginning of the game if you are chosen")
        
