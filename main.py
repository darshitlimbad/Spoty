import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
api_key= os.getenv("discord_token")

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
    
bot.run(api_key) 