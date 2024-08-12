import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import time
import requests

from spotify import *

load_dotenv()
discord_token= os.getenv("discord_token")            

# Refreshing Spotify access token 
def refresh_spotify_token():
    generate_spotify_token()
    
def start_discord_bot():
    # creating intents obj
    intents= discord.Intents.default()
    intents.message_content=True

    # Bot initialization
    bot= commands.Bot(command_prefix='!',intents=intents)

    @bot.event
    async def on_ready():
        print("This Bot is ready to searve you.")
        print("--------------------------------")
            
    @bot.command(help="Says Hello!")
    async def hello(ctx):
        await ctx.send("Hello!")

    @bot.command(help="Repeats your message.")
    async def repeat(ctx,*,message):
        await ctx.send(message)
        
    bot.run(discord_token) 
    
def main():
    refresh_spotify_token()
    search_artists(artist_name="kishor")
    


if __name__ == '__main__':
    main()