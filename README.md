# HVZ-bot

This repository contains software I created to facilitate Humans vs. Zombies (HVZ) events. It allows you to track player statistics, automate missions, and customize the bot for your game's needs.

## Prerequisites
This program requires that you have virtualenv and python installed. You must also have a discord account.

## Installation and Development

First, follow the instructions to create the discord bot for your server [here](https://discordpy.readthedocs.io/en/stable/discord.html) on discord's official website. Make sure you name the bot HVZ.
Make sure you save your token as well.

Next, follow the installation instructions below:

```
git clone https://github.com/bohnerjosh/HVZ-bot
cd HVZ-bot
virtualenv -p python3 env
```
Open ``hvz.env`` with your favorite command line text editor and replace "YOUR_TOKEN_HERE" with your bot's token. **DO NOT SHARE THIS TOKEN WITH ANYONE.**

Then:
```
source hvz.env
pip install -r requirements.txt
```

## Run - Command Line
```
source blurg.env
./run-bot.sh
```

## First time setup

Now that the bot is running, you have to perform some setup to make sure your bot sends the correct information to the correct channels in your discord server. You also need to identify yourself as a moderator to the bot so you can perform the other setup commands. You also need to make 2 roles in your discord server: ``Human`` and ``Zombie``.

### Becoming a moderator
Copy your full discord username (username#1234 on lower left) and paste the following command:

```!addmod <USERNAME>```

Replace ```<USERNAME>``` with your discord username and send the message. If you get the message ``Added <USERNAME> as a moderator``, the command was successful. You can use this command to make any number of discord users moderators.
 
### Setting the moderator and mission channel ids

If you have not already, create a channel for moderators to interact privately with the bot. Additionally, create a channel dedicated to sending out mission information.

In order for the bot to send messages to these channels, we will need their ids. In order to see channel ids, developer mode must be enabled in discord. If not already enabled, navigate to user settings >> advanced >> toggle the button next to ``Developer Mode``.

Right click on the text channel you created for moderation on the left side of your screen where all your text channels are. Click on ``copy id`` at the bottom of the menu that appears. 

In your mod channel, type the following command:
```!setmodchannel <ID>```

where ``<ID>`` is the id of the channel you copied. You can paste it from your clipboard and hit enter to send the command. A confirmation message should appear if the command was successful.
  
To set your missions, channel, follow the same steps. Copy the id of the channel on the left in the list of text channels, and enter the command below in your moderation channel:
```!setmissionschannel <ID>```

where ``<ID>`` is the id of the channel you copied. Paste it and hit enter. 
  
## Allowing players to join
To allow players to register for your game, simply have them join your discord server and type the command ``!create`` in any text channel.
  
## Commands
Below is a full list of the commands of the bot with a link to further reading of how to use each command.
To use a command, invoke the bot using its prefix before a message. By default, the bot's prefix is ``!``.
  
### All Moderator Commands
* [addmod](#addmod)
* [createOZ](#createoz)
* [makelive](#makelive)
* [missionend](#missionend)
* [mission](#mission)
* [missions](#missions)
* [missionget](#missionget)
* [OZpool](#ozpool)
* [prefix](#prefix)
* [reset](#reset)
* [setmissionschannel](#setmissionschannel)
* [setmodchannel](#setmodchannel)
* [starthvz](#starthvz)

### All Player Commands
* [create](#create)
* [code](#code)
* [ids](#ids)
* [stats](#stats)
* [stun](#stun)

## Moderator Commands
### addmod
Allows a moderator to allow other discord users to perform moderator commands. Only give this permission to users that need it.
 
```!addmod <USERNAME>```
 
where ``<USERNAME>`` is the user's full discord username (name#1234)
 
### createOZ
Allows a moderator to choose an OZ from a pool of volunteers at the beginning of the game. Players opt-in by reacting to a message sent in their DMs when they register for the game. This is to keep those who volunteer anonymous.
 
```!createOZ```
 
### makelive
Sends mission information to the "missions" channel defined during setup. This makes the mission "live".
 
```!makelive <ID>```
 
where <ID> is the mission ID. You can get the mission id with [missions](#missions).
 
### missionend
"Ends" an active mission and allows a mod to declare a winner for a role defined by a moderator.
 
```!missionend <WINNER>```
 
where ```<WINNER>``` is ```Zombie``` or ```Human```.
 
### mission
Allows a moderator to upload missions to the discord bot to create a new mission or modify an existing mission.
To upload a mission, place the text for your mission into a plaintext file, and name that file a number that represents what mission number it is. This is the mission's ID. 
To upload a mission, drag the file with the mission text into the mod channel you created, and in the optional field for text when you upload the document, type ```!mission```.

Do this every time you make a modification for a mission to update it for the bot. Make sure the mission id is the same.
 
### missions
Allows a moderator to see all missions uploaded to the bot along with their ids. Only shows mission text up to the first newline to save space on the screen.
 
```!missions```
 
### missionget
Allows a moderator to see the entire contents of a mission's text via its id. 
 
```!missionget <ID>```
 
where ```<ID>``` is the mission id of the mission.
 
### OZpool
Allows a moderator to manually change the OZpool status of a player.
Subcommands:
**poolremove** - manually removes a player from the OZpool
 
```!OZpool poolremove <NAME>```
 
 where ```<NAME>``` is the name of the player (user#1234).
 
 **pooladd** - manually add a player to the OZpool
 
 ```!OZpool pooladd <NAME>```
 
 where ```<NAME>``` is the name of a player (user#1234).

 **makeoz** - forces a player to become the OZ
 
 ```!OZpool makeoz <NAME>```
 
 where ```<NAME>``` is the name of a player (user#1234).
 
 **takeoz** - removes OZ status from a player
 
 ```!OZpool takeoz <NAME>```
 
 where ```<NAME>``` is the name of a player (user#1234).

 
 ### prefix
 Allows a moderator to change the prefix used to invoke the bot. You MUST restart the bot for this change to take effect.
 
 ```!prefix <PREFIX>```
 
 where ```<PREFIX>``` is a single character.
 
 ### reset
 Use this command to reset the config file. You MUST perform first time setup again once you run this command.
 
 ```!reset```
 
 ### setmissionschannel
 See first time setup
 
 ### setmodchannel
 See first time setup
 
 ### starthvz
 Allows a mod to start the game. When this command runs, all player's 'human_time' metric is set to the current time, and a OZ is chosen.
 
 ```!starthvz```
 
 ## Player Commands
 
 ### create
 Allows a user to register for participation in HVZ. Also includes a response from the bot that allows a player to have a chance of being the OZ. If the player wants to opt-in, have them react to the checkmark on the message they get when they register.
 
 This command generates a killcode for a user, which is sent to their DMs. **DO NOT SHARE THIS CODE WITH ANYONE**. It is used to identify players when they get transformed into a zombie.
 
 ```!create```
 
 ### code
 Allows a zombie to convert a human to a zombie when they are tagged. **Note: Humans cannot use this command, and the person tagged must be human.**
 Requires the tagged player's killcode.
 
```!code <CODE>```

where ```<CODE>``` is the tagged player's killcode.

### ids
Allows a player to get all player's internal ids. This is for use of the stun command so players can refer to each other by id, making command typing faster.

```ids```

### stats
Generates game statistics for a player. Can be generated at any time, but it is recommended that players wait until the end of the game to see their stats.

Tracks the following:
* status - human or zombie)
* human time - how long the player has been a human since the beginning of the game
* stuns/tags - number of zombies stunned or humans tagged 

```!stats```

### stun

Allows humans to keep track of zombies they have stunned. Uses a player's internal ID (from the ```ids``` commmand) to track stuns.

```!stun <SHOOTER_ID> <VICTIM_ID>```

where ```<SHOOTER_ID>``` is the human's internal id, and ```<VICTIM_ID>``` is the stunned player's internal id.
