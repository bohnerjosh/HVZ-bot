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

            # Tell the player that they can register to become the OZ
            msg = await ctx.author.send("If you would like to have a chance of being OZ (:zombie:), tap the check mark below this message")
            
            # add a checkmark reaction to the message
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
            guild = ctx.guild
            name, disc = hvz.name_split(victim.username) # get the name and discriminator of discord username
            # grab discord profile object
            discord_profile = discord.utils.get(guild.members, name=name, discriminator=disc)
            
            # change user's discord roles from human to zombie
            zombie_role = discord.utils.get(guild.roles, name="Zombie")
            human_role = discord.utils.get(guild.roles, name="Human")
            await discord_profile.remove_roles(human_role)
            await discord_profile.add_roles(zombie_role)

    # Command that allows humans to track zombies that they stun
    @client.command(name="stun", help="Report a stunned zombie")
    async def get_user_killcode(ctx, *args):
        # check command syntax
        if len(args) < 2:
            await ctx.send("Invalid stun syntax")
            return
        # grab shooter and who they shot from args
        args = list(args)
        shooter = args[0]
        victim = args[1]

        # attempt to log the stun internally
        result = hvz.stun(shooter, victim)

        # error checking
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
        
    # Command lists the ID of each player in the bot's internal database
    # This makes it faster to log stuns and zombieifications
    @client.command(name="ids", help="Get ids of users")
    async def get_ids(ctx):
        out_str = "```==Players and their ids==\n"
        # grab players internally
        result = db.get_users()

        # print the ids out
        for player in result:
            out_str += "    " + str(player.id) + " : " + player.username + "\n"

        out_str += "==END==```"

        await ctx.send(out_str)

    # prints out game statistics for a player
    @client.command(name="stats", help="Users get stats at the end of the game")
    async def get_player_statistics(ctx):
        # get command sender's username
        username = str(ctx.author)

        # verify that the player is registered internally
        result = hvz.check_player(username)
        if not result:
            await ctx.send("You are not registered. Please register to track stats") 
        else:
            # send internal game statistics to player via DM
            await ctx.send("Sending stats to DM")

            # grab statistics
            player, tags, stuns, tagger = db.get_stats(username)
            time_alive = hvz.get_time_alive(player)
            
            # Sending statistics. Differentiates between humans and zombies
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
    
    # Allows mods to create missions. Must be a moderator to create missions.
    @client.command(name="mission", help="Create a mission")
    async def connect_mission(ctx):
        # grab the username of the sender and verify that they are registered and a mod
        username = str(ctx.author)
        result = hvz.check_player(username)
        
        if not result:
            await ctx.send("You must be registered to create missions") 
            return

        if not username in MODS or ctx.channel.id != config.params["mod_channel"]:
            await ctx.send("You do not have permission to create missions") 
    
            return

        # check for file attachment
        if not ctx.message.attachments:
            await ctx.send("No file attached") 
            return

        # process and decode file attachment. Mission is identified internally by its filename
        attachment = ctx.message.attachments[0]
        attachment_url = attachment.url
        file_request = requests.get(attachment_url)
        file_text = file_request.content.decode("utf-8")
        file_name = attachment.filename
       
        # save the file 
        m_id, result = hvz.handle_mission(file_name, file_text)

        if result == "init":
            await ctx.send(f"Mission created with id: {m_id}") 
        elif result == "modify":    
            await ctx.send(f"Mission modified with id: {m_id}") 
    
    # sends all created missions and their ids to a channel. Must be a mod to use.
    @client.command(name="missions", help="Get all missions")
    async def get_missions(ctx):
        # check to see if command sender is a mod and registered
        username = str(ctx.author)
        if not username in MODS:
            await ctx.send("You do not have permission to create missions") 
            return

        # grab the missions internally
        missions = db.get_missions()
        out_text = "```==Missions==\n\n"
        
        # print out missions
        for mission in missions:
            out_text += f"id: {mission} | header text:\n"
        # verify username
            out_text += missions[mission] + "\n\n"

        out_text += "==END OF MISSIONS==```"
        await ctx.send(out_text)
    
    # get info for a single mission. Must be a mod to use.
    @client.command(name="missionget", help="Get a singular mission")
    async def get_mission(ctx, *args):
        # check to see if command sender is a mod and registered
        if len(args) < 1:
            await ctx.send("Invalid mission get syntax")
            return
        
        mission_id = args[0]
        username = str(ctx.author)
        if not username in MODS:
            await ctx.send("You do not have permission to create missions") 
            return

        # grab mission info internally
        result = hvz.get_mission(mission_id)
        
        # if no matching mission tell user
        if result == "error":
            await ctx.send("No mission with that id") 
            return
        # otherwise send it
        out_text = f"```==MISSION TEXT==\n\n"
        out_text += result + "\n\n==END MISSION TEXT==```"
        
        await ctx.send(out_text)

    # Sends mission info to "missions" channel defined in config. 
    # This makes the mission "live" in game
    @client.command(name="makelive", help="Make a mission live")
    async def live_mission(ctx, *args):
        # check to see if the user is registered and is a mod
        if len(args) < 1:
            await ctx.send("Invalid live mission syntax")
            return

        mission_id = args[0]
        username = str(ctx.author)

        if not username in MODS:
            await ctx.send("You do not have permission to create missions") 
            return

        # get the specified mission id
        result = hvz.get_mission(mission_id)
        
        # throw error if given a bad mission id
        if result == "error":
            await ctx.send("No mission with that id") 
            return

        # send mission to mission channel
        out_text = "__**NEW MISSION**__\n" + result
       
        channel = client.get_channel(config.params["missions_channel"]) 
        await channel.send(out_text)

    # ends a mission and tells game players who won
    @client.command(name="missionend", help="End a mission")
    async def mission_end(ctx, *args):
        # check args and sender permissions
        if len(args) < 2:
            await ctx.send("Invalid live mission syntax")
            return
        
        if not username in MODS:
            await ctx.send("You do not have permission to end missions") 
            return
        
        # get mission id, throw error if its anything than a number for mission id
        try:
            mission_id = int(args[0])
            winner = args[1]
        except Exception:
            await ctx.send("Invalid command syntax")
            return

        # tell backend who won what mission 
        result = hvz.determine_winner(mission_id, winner)

        # raise errors for invalid ids and roles
        if result == "invalid_mission":
            await ctx.send("That mission id does not exist")
            return
        elif result == "invalid_winner":
            await ctx.send("Invalid winner. Must be 'Human' or 'Zombie'")
            return

        # send the message
        out_text = f"Mission is over! The result: A {result} victory!"

        channel = client.get_channel(config.params["missions_channel"]) 
        await channel.send(out_text)

    @client.command(name="starthvz", help="Sets the start time for being human for stats, and chooses an OZ")
    async def start_game(ctx):
        username = str(ctx.author)
        if not username in MODS:
            await ctx.send("You do not have permission to start the game") 
            return

        # update player's human_time to current time
        db.set_default_human_time()

        # choose an OZ
        OZ = hvz.choose_OZ()

        # if the volunteer pool is empty raise an error
        if OZ is None:
            await ctx.send("OZ pool is empty. Have at least 1 player volunteer before choosing an OZ") 
            return
        
        # notify mods a user has been chosen
        user = OZ.username
        await ctx.send(f"The OZ has been chosen! It is {user}!")
        
        await ctx.send(f"User will be notified and their status will change")
        db.OZ_status(OZ)

        guild = ctx.guild # the discord server

        # get chosen player's discord profile, and change their roles
        name, disc = hvz.name_split(user) # get the name and discriminator of discord username
        
        discord_profile = discord.utils.get(guild.members, name=name, discriminator=disc)
        zombie_role = discord.utils.get(guild.roles, name="Zombie")
        human_role = discord.utils.get(guild.roles, name="Human")
        await discord_profile.remove_roles(human_role)
        await discord_profile.add_roles(zombie_role)
 
        # Notify the player they have been chosen to be the OZ
        await discord_profile.send(":rotating_light: **You have been chosen to be the OZ!** :rotating_light:")
        await discord_profile.send("If you have questions pertaining to the rules of being OZ, be sure to ping the mods")
        await discord_profile.send("Good luck!")

        channel = client.get_channel(config.params["missions_channel"]) 
        out_text = "***THE GAME HAS BEGUN! GOOD LUCK!***"
        await channel.send(out_text)
    
    # Command used by mods to choose a OZ from a pool of volunteers at the beginning of the game
    @client.command(name="createOZ", help="Randomly select an OZ from a pool of volunteers")
    async def create_OZ(ctx):
        # verify user is a mod
        username = str(ctx.author)
        if not username in MODS:
            await ctx.send("You do not have permission to change prefix") 
            return

        # query an OZ from the backend
        OZ = hvz.choose_OZ()

        # if the volunteer pool is empty raise an error
        if OZ is None:
            await ctx.send("OZ pool is empty. Have at least 1 player volunteer before choosing an OZ") 
            return
        
        # notify mods a user has been chosen
        user = OZ.username
        await ctx.send(f"The OZ has been chosen! It is {user}!")
        
        await ctx.send(f"User will be notified and their status will change")
        db.OZ_status(OZ)

        guild = ctx.guild # the discord server

        # get chosen player's discord profile, and change their roles
        name, disc = hvz.name_split(user) # get the name and discriminator of discord username
        
        discord_profile = discord.utils.get(guild.members, name=name, discriminator=disc)
        zombie_role = discord.utils.get(guild.roles, name="Zombie")
        human_role = discord.utils.get(guild.roles, name="Human")
        await discord_profile.remove_roles(human_role)
        await discord_profile.add_roles(zombie_role)
 
        # Notify the player they have been chosen to be the OZ
        await discord_profile.send(":rotating_light: **You have been chosen to be the OZ!** :rotating_light:")
        await discord_profile.send("If you have questions pertaining to the rules of being OZ, be sure to ping the mods")
        await discord_profile.send("Good luck!")

     # command used by mods to change a player's OZpool status manually
    @client.command(name="OZPool", help="Modify a user pertaining to the OZ pool")
    async def change_prefix(ctx, *args):
        # verify command and that user is a mod
        username = str(ctx.author)
        if len(args) < 2:
            await ctx.send("Invalid command syntax")
            return
        
        if not username in MODS:
            await ctx.send("You do not have permission to change OZ Pool settings") 
            return

        # get args passed to bot
        try:       
            subcommand = args[0].lower()
        except:
            await ctx.send("Invalid command syntax")
            await ctx.send("Choices are ``poolremove``, ``pooladd``, ``makeOZ``, and ``takeOZ``")
            return

        value = args[1]

        # verify affected player is registered
        result = hvz.check_player(value)
        
        if not result:
            await ctx.send(f"Could not find user ``{value}``") 
            return
        player = result[0]
        
        # 4 cases for OZpool

        # Remove player from OZpool
        if "poolremove" in subcommand:
            if not player.oz_pool == 1:
                await ctx.send("Player is not in the OZ pool")
                return
            hvz.remove_from_OZ_pool(player)

        # Add player to OZpool
        elif "pooladd" in subcommand:
            if player.is_oz_pool == 1:
                await ctx.send("Player is already in the OZ pool")
                return
            db.add_to_OZ_lst(player.username)

        # make a specific player the OZ
        elif "makeoz" in subcommand:
            if player.is_oz == 1:
                await ctx.send("That player is already the OZ")
                return

            db.OZ_status(player)
            guild = ctx.guild

            name, disc = hvz.name_split(player.username) # get the name and discriminator of discord username
            # get discord profile, change roles, and alert player
            discord_profile = discord.utils.get(guild.members, name=name, discriminator=disc)
            zombie_role = discord.utils.get(guild.roles, name="Zombie")
            human_role = discord.utils.get(guild.roles, name="Human")
            await discord_profile.remove_roles(human_role)
            await discord_profile.add_roles(zombie_role)
            
            await discord_profile.send(":rotating_light: **You have been chosen to be the OZ by a MOD!** :rotating_light:")
   
        # remove OZ status from a player
        elif "takeoz" in subcommand:
            if not player.is_oz == 1:
               await ctx.send("Player is not the current OZ") 
               return

            db.take_OZ(player)

            guild = ctx.guild
            oz_name, oz_discrim = hvz.name_split(player.username)

            # get discord profile, change roles, notify player
            player_obj = discord.utils.get(guild.members, name=oz_name, discriminator=oz_discrim)
           
            zombie_role = discord.utils.get(guild.roles, name="Zombie")
            human_role = discord.utils.get(guild.roles, name="Human")

            await player_obj.remove_roles(zombie_role)
            await player_obj.add_roles(human_role)
            await player_obj.send("You are no longer OZ and are a regular human")
        else:
            # otherwise, tell them to fix command syntax
            await ctx.send("Invalid command syntax")
            await ctx.send("Choices are ``poolremove``, ``pooladd``, ``makeOZ``, and ``takeOZ``")

    # command that allows a mod to set the bot prefix 
    @client.command(name="prefix", help="set the box prefix")
    async def change_prefix(ctx, *args):
        # command checking and making sure user is a mod
        if len(args) < 1:
            await ctx.send("Invalid command syntax")
            return
        # get and check prefix is a single character
        prefix = args[0]
        username = str(ctx.author)
        prefix_length = len(prefix)
        if not prefix_length == 1:
            await ctx.send("Prefix must be a single character")
            return

        # must be a mod
        if not username in MODS:
            await ctx.send("You do not have permission to change the bot command prefix") 
            return
        
        # tell config to update the bot prefix
        config.update_params(prefix=prefix)
        await ctx.send(f"Prefix changed to {prefix}. Restart the bot to apply this change")

    # allows mods to set the moderation channel. This is done during first time
        # setup, and is where all mission commmands occur
    @client.command(name="setmodchannel", help="set the id for the mods channel")
    async def change_mod_channel(ctx, *args):
        # verify command syntax and that user is a mod
        username = str(ctx.author)
        if len(args) < 1:
            await ctx.send("Invalid command syntax")
            return

        if not username in MODS:
            await ctx.send("You do not have permission to set the mod channel") 
            return

        # get passed channel ID and tell config to update 
        channel_id = args[0]
        config.update_params(mod_channel=channel_id)
        await ctx.send(f"Mod channel changed to {channel_id}")

    # allows mods to set the missions channel. This is done during first time
        # setup, and is where all mission appear to humans and zombies
    @client.command(name="setmissionschannel", help="set the id for the missions channel")
    async def change_mission_channel(ctx, *args):
        # verify command syntax and that user is a mod
        username = str(ctx.author)
        if len(args) < 1:
            await ctx.send("Invalid command syntax")
            return

        if not username in MODS:
            await ctx.send("You do not have permission to set the mission channel") 
            return

        # get channel id from args
        channel_id = args[0]
    
        # tell config to update channel id
        config.update_params(missions_channel=channel_id)
        await ctx.send(f"Missions channel changed to {channel_id}")

    # adds a discord member to the list of internal moderators.
    # NOTE: Person adding must be a internal moderator. This does
    # not apply during initial setup
    @client.command(name="addmod", help="Add profile to mods list")
    async def change_mission_channel(ctx, *args):
        # verify command syntax and that the user is a mod
        username = str(ctx.author)
        if len(args) < 1:
            await ctx.send("Invalid command syntax")
            return

        # if first time setup, bypass mod requirement
        if not username in MODS and config.params["firsttimesetup"] == "False":
            await ctx.send("You do not have permission to add to the mods list") 
            return

        # if a user is already a moderator, return
        user = args[0]
        if user in config.params["mods"]:
            await ctx.send("{user} is already a moderator")
            return 
        
        # add user to the mods list in config
        config.update_params(mods=user)
        await ctx.send(f"Added {user} as a moderator")

    # allows mods to reset the config file if something bad happens
    @client.command(name="reset", help="Reset the config file")
    async def change_mission_channel(ctx, *args):
        # verify user is a mod
        username = str(ctx.author)

        if not username in MODS:
            await ctx.send("You do not have permission to reset the config file") 
            return
        # reset the config
        config.reset_config()
        
    @client.event
    async def on_message(message):
        # pass message to command handler
        await client.process_commands(message)

    # event that handles when a player clicks the checkmark to volunteer to be 
        # part of the OZpool
    @client.event
    async def on_reaction_add(reaction, user):
        username = str(user)
        # check to see if the reaction clicked was the one the bot made
        if reaction.emoji == CHECKMARK:
            usermatch = db.has_user(username)

            # make sure the reaction clicked is in a DM, not a regular channel
            if len(usermatch) > 0 and isinstance(reaction.message.channel, discord.channel.DMChannel):
                
                # add player to OZlist
                db.add_to_OZ_lst(username)
                await user.send(":warning: You have been added to the list of potential humans to be the OZ :warning:")
                await user.send("You will be sent a message at the beginning of the game if you are chosen")
                await user.send("If this was done in error or you change your mind, ping a mod")
