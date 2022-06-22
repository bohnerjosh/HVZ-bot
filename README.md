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
open ``hvz.env`` with your favorite command line text editor and replace "YOUR_TOKEN_HERE" with your bot's token. **DO NOT SHARE THIS TOKEN WITH ANYONE.**

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

Now that the bot is running, you have to perform some setup to make sure your bot sends the correct information to the correct channels in your discord server. You also need to identify yourself as a moderator to the bot so you can perform the other setup commands.

### Becoming a moderator
Copy your full discord username (username#1234 on lower left) and paste the following command:

```!addmod <USERNAME>```
Replace <USERNAME> with your discord username and send the message. If you get the message ``Added <USERNAME> as a moderator``, the command was successful. You can use this command to make any number of discord users moderators.
 
### Setting the moderator and mission channel ids

If you have not already, create a channel for moderators to interact privately with the bot. Additionally, create a channel dedicated to sending out mission information.

In order for the bot to send messages to these channels, we will need their ids. In order to see channel ids, developer mode must be enabled in discord. If not already enabled, navigate to user settings >> advanced >> toggle the button next to ``Developer Mode``.

Right click on the text channel you created for moderation on the left side of your screen where all your text channels are. Click on ``copy id`` at the bottom of the menu that appears. 

In your mod channel, type the following command:
```!setmodchannel <ID>```
where ``<ID>`` is the id of the channel you copied. You can paste it from your clipboard and hit enter to send the command. A confirmation message should appear if the command was successful.
  
To set your missions, channel, follow the same steps. Copy the id of the channel on the left in the list of text channels, and enter the command below in your moderation channel:
```!setmissionchannel <ID>```
where ``<ID>`` is the id of the channel you copied. Paste it and hit enter. 
  
## Allowing players to join
To allow players to register for your game, simply have them join your discord server and type the command ``!create`` in any text channel.
  
## Commands
Below is a full list of the commands of the bot with a link to further reading of how to use each command.
To use a command, invoke the bot using its prefix before a message. By default, the bot's prefix is ``!``.
  
  

### All Moderator Commands
* [addmod](#addmod)
* [createOZ](#createOZ)
* [makelive](#makelive)
* [missionend](#missionend)
* [mission](#mission)
* [missions](#missions)
* [missionget](#missionget)
* [OZpool](#ozpool)
* [prefix](#prefix)
* [reset](#reset)
* [setmissionschannel](#setmissionchannel)
* [setmodchannel](#setmodchannel)

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
 
###  createOZ
Allows a moderator to 
## Player Commands
asdf
