import os
import nacl
# import ffm
from subprocess import run
from dotenv import load_dotenv
import discord
from discord import FFmpegPCMAudio
from discord.ext import commands
from queue import Queue
import yt_dlp

# Load environment variables
load_dotenv()
discord_token = os.getenv("discord_token")

def search_song_yt(query):
    ydl_opts = {
        'format': 'bestaudio/best',  
        'noplaylist': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)
        if 'entries' in info:
            video = info['entries'][0]
            return video['url']
    return None

class Spoty_bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=discord.Intents.all())

    async def on_ready(self):
        print("This Bot is ready to serve you.")
        print("-" * 100)
        
    async def setup_hook(self):
        await self.add_cog(Player(self))
        await self.tree.sync()

class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Keeps a track who started the bot For some commands
    BotMainUser=False
    
    # queue for upcomming songs
    queue= Queue()
    
    # @commands.command(help="Says Hello!") 
    # async def hello(self, ctx):
    #     await ctx.send("Hello!")

    async def isInVoice(self, ctx) -> bool:
        if ctx.voice_client:
            return True
        
        return False
    
    # Connect the bot to the user's voice channel
    async def connectToVoice(self, ctx) -> bool:
        try:
            if ctx.author.voice:
                channel= ctx.author.voice.channel
                await channel.connect(self_deaf=True)
                self.BotMainUser= ctx.author
                await ctx.send("Bot connected to voice channel.")
                return True
            else:
                await ctx.send("You need to be in a voice channel to play music.")
                return False
        except Exception as e:
            await ctx.send(f"Failed to connect to the voice channel: {str(e)}")
            return False
    
    # User Can control or not 
    async def checkUserCanControl(self, ctx) -> bool:
        # logic: check if the user is in the same voice channel as the bot
        if ctx.voice_client and ctx.author.voice and ctx.voice_client.channel == ctx.author.voice.channel:
            return True
        else:
            await ctx.send("You need to be in the same voice channel as the bot to control it.")
            return False
    
    @commands.command(help="Search & Play any songs")
    async def play(self,ctx, * ,query: str = ""):
        try:
            # Get the player
            player = ctx.author

            if not await self.isInVoice(ctx):
                res= await self.connectToVoice(ctx)
                if not res:
                    return
            else:
                res= await self.checkUserCanControl(ctx)
                if not res:
                    return
            
            await ctx.send(f"Finding song for **@{player}** , `query: {query}`")
            youtube_url= search_song_yt(query)
            
            if not youtube_url: 
                raise Exception("Song not found!")
            
            await ctx.send(f"**@{player}** is playing song `query: {query}`")
            
            if ctx.voice_client is not None:
                source = FFmpegPCMAudio(youtube_url)
                ctx.voice_client.play(source)
                await ctx.send(f"Now playing: {query}")
            else:
                await ctx.send("Bot failed to connect to a voice channel.")           
            await ctx.send("Processing your request...")
            
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")
        
    @commands.command(help="Disconnect the bot from the voice channel (mute it).")
    async def disconnect(self, ctx):
        if ctx.voice_client is not None:
            if ctx.author == self.BotMainUser: 
                await ctx.voice_client.disconnect() 
                await ctx.send("Bot has been disconnected from the voice channel.")
            else:
                await ctx.send(f"Only **@{self.BotMainUser}** has permission to disconnect ***Spoty*** for this session.")
        else:
            await ctx.send("Bot is not in a voice channel.")
    
# def refresh_spotify_token():
#     generate_spotify_token()

def main():
    # refresh_spotify_token()
    bot = Spoty_bot()
    bot.run(discord_token)
    
if __name__ == '__main__':
    main()
