import os
import nacl
from subprocess import run
from dotenv import load_dotenv
import discord
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext import commands
from queue import Queue
import yt_dlp

# Load environment variables
load_dotenv()
discord_token = os.getenv("discord_token")

def search_song(query):
    try:
        ydl_opts = {
            'format': 'bestaudio[abr>0]/bestaudio/best',   
            'default_search': 'ytsearch',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"{query} song", download=False)
            if 'entries' in info:
                audio = info['entries'][0]
                return {'title': audio['title'], 'url': audio['url']}
        return {'title': None, 'url': None}

    except Exception as e:
        print(f"Error fetching song: {e}")
        return {'title': None, 'url': None}

def search_by_query(query):
    try:
        ydl_opts = {
            'format': 'bestaudio[abr>0]/bestaudio/best',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Check if the query is a URL or a search term
            if 'youtube.com' in query or 'youtu.be' in query:
                info = ydl.extract_info(query, download=False)
            else:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)
                
            if 'entries' in info: 
                audio = info['entries'][0]
                return {'title': audio['title'], 'url': audio['url']}
            elif 'url' in info:
                return {'title': info.get('title',"Title Not Found"), 'url': info['url']}
            
        return {'title': None, 'url': None}
    except Exception as e:
            print(f"Error fetching audio: {e}")
            return {'title': None, 'url': None}

class Spoty_bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=discord.Intents.all())

    async def on_ready(self):
        print("Bot is online and ready to serve.")
        print("-" * 100)
        
    async def setup_hook(self):
        await self.add_cog(Player(self))
        await self.tree.sync()

class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # admin of the bot ID
        self.admin= '550382024402272256'
        # Track the context for the bot
        self.current_ctx = None
        # Queue for upcoming songs
        self.queue = Queue()
        
        #volume of the bot from 0.0 to 2.0
        self.current_volume= 0
    
    async def is_bot_connected_to_voice(self, ctx) -> bool:
        """Check if the bot is connected to a voice channel."""
        return ctx.voice_client is not None
    
    async def join(self, ctx) -> bool:
        """Connect the bot to the user's voice channel."""
        try:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
                await channel.connect(self_deaf=True)
                self.current_ctx = ctx
                self.current_volume= 0.05
                await ctx.send(f"Connected to voice channel: **{channel.name}**.")
                print(f"Joined voice channel: {channel.name}.")
                return True
            else:
                await ctx.send("You need to be in a voice channel to play music.")
                return False
        except Exception as e:
            await ctx.send(f"Failed to connect to the voice channel: {str(e)}")
            print(f"Error connecting to voice channel: {e}")
            return False
    
    async def is_user_authorized_to_control(self, ctx) -> bool:
        """Check if the user can control the bot."""
        if ctx.voice_client and ctx.author.voice and ctx.voice_client.channel == ctx.author.voice.channel:
            return True
        else:
            await ctx.send("You must be in the same voice channel as the bot to control it.")
            return False
            
    async def play_song(self, ctx):
        """Play the next song in the queue."""
        try:
            if ctx.voice_client is None:
                await ctx.send("Error: The bot is not connected to a voice channel.")
                print("Error: Attempted to play a song when the voice client is not available.")
                return

            if ctx.voice_client.is_playing():
                print("Error: Attempted to play the next song while the voice client is already playing a song.")
                return
            
            if not self.queue.empty():
                ffmpeg_options = {
                    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    'options': '-vn',
                }
                song = self.queue.get()
                source = FFmpegPCMAudio(song['url'], **ffmpeg_options)
                source = PCMVolumeTransformer(source, self.current_volume)
                
                ctx.voice_client.play(source, after=lambda error: print("current song is finished"))
        
                await ctx.send(f"Now playing: **{song['title']}**")
                print(f"Started playing: {song['title']}")
            else:
                await ctx.send("The queue is empty. The bot will now disconnect.")
                print("Queue is empty. Disconnecting the bot.")
                await self.disconnect(ctx)
            
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")
            print(f"Error during playnow command: {e}")
    
    @commands.command(help="Stops current playback, clears the queue, and immediately plays the requested song.")
    async def playnow(self, ctx, *, query: str = ""):
        """Stops current playback, clears the queue, and immediately plays the requested song."""
        try:
            if not query:
                raise Exception("Please Provide a query with `!playnow` ")
            
            if ctx.voice_client is not None:
                await self.stop(ctx)
            
            await self.play(ctx,query=query)
            
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")
            print(f"Error during playnow command: {e}")
        
    
    @commands.command(help="Lists the websites from which you can play audio.")
    async def urllist(self, ctx):
        """Sends a list of supported websites for audio playback."""
        await ctx.send("You can use URLs from the following websites to play audio:")
        await ctx.send("- YouTube")

    @commands.command(help="Plays audio from the given URL or query. For a list of supported platforms, use !urllist.")
    async def sourceplay(self, ctx, *, query: str = ""):
        """
        Plays audio from the provided URL or search query. For more information on supported URLs, check the !urllist command.
        """
        try:
            # Validate the query and voice client connection
            if not query:
                await ctx.send("Please provide a valid URL or search query.")
                return
            
            if not await self.is_bot_connected_to_voice(ctx):
                if not await self.join(ctx):
                    return
            
            if not await self.is_user_authorized_to_control(ctx):
                return
            
            await ctx.send("Processing your request...")
            player = ctx.author
            
            # Check if the bot is connected and handle the search
            await ctx.send(f"Searching for: **{query}** requested by {player.mention}.")
            search_response = search_by_query(query)
                
            if ctx.voice_client:    
                if not search_response['url']:
                    raise Exception("No results found for the query.")
                
                self.queue.put(search_response)
                
                if ctx.voice_client.is_playing():
                    await ctx.send(f"**{search_response['title']}** has been added to the queue by {player.mention}.")
                    print(f"Added song to queue: {search_response['title']}")
                else:
                    await self.play_song(ctx)
                    
            else:
                await ctx.send("Failed to connect to a voice channel.")
                print("Error: Failed to connect to a voice channel.")
                
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")
            print(f"Error during sourceplay command: {e}")
            
    @commands.command(help="Search & Play any songs")
    async def play(self, ctx, *, query: str = ""):
        """Search for a song and add it to the queue or play it immediately."""
        try:
            if not query:
                raise Exception("Please Provide a query with `!play` ")
            
            await ctx.send("Processing your request...")
            player = ctx.author

            if not await self.is_bot_connected_to_voice(ctx):
                if not await self.join(ctx):
                    return
            else:
                if not await self.is_user_authorized_to_control(ctx):
                    return
            await ctx.send(f"Searching for song: **{query}** requested by {player.mention}.")
            search_response = search_song(query)
                
            if ctx.voice_client is not None:   
                
                if not search_response['url']:
                    raise Exception("Song not found!")
                
                self.queue.put(search_response)
                
                if ctx.voice_client.is_playing():
                    await ctx.send(f"**{search_response['title']}** has been added to the queue by {player.mention}.")
                    print(f"Added song to queue: {search_response['title']}")
                else:
                    await self.play_song(ctx)
            else:
                await ctx.send("Failed to connect to a voice channel.")
                print("Failed to connect to a voice channel.")
        
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")
            print(f"Error during play command: {e}")
    
    @commands.command(help="Disconnect the bot from the voice channel.")
    async def disconnect(self, ctx):
        """Disconnect the bot from the voice channel."""
        if ctx.voice_client is not None:
            if ctx.author == self.current_ctx.author or ctx.author == self.bot.user or ctx.author.id == self.admin:
                await ctx.voice_client.disconnect()
                await ctx.send("Bot has been disconnected from the voice channel.")
                print("Bot disconnected from voice channel.")
            else:
                await ctx.send(f"Only **{self.current_ctx.author.mention}** has permission to disconnect the bot for this session.")
                print(f"Unauthorized disconnect attempt by: {ctx.author}")
        else:
            await ctx.send("The bot is not in a voice channel.")
            print("Attempted to disconnect, but the bot is not in a voice channel.")
            
    @commands.command(help="Stops the current song and clears the queue.")
    async def stop(self, ctx):
        if ctx.voice_client is not None:
            if ctx.voice_client.is_playing():
                # Stop the current playback
                ctx.voice_client.stop()
            
                # Clear the queue of upcoming songs
                self.queue.queue.clear()
                await ctx.send("Playback has been stopped, and the queue has been cleared.")
            else:
                await ctx.send("No song is currently playing.")
        else:
            await ctx.send("The bot is not connected to a voice channel.")
    
    @commands.command(help="Plays the next song from the queue.")
    async def next(self, ctx):
        if ctx.voice_client is not None:
            if ctx.voice_client.is_playing():
                # Stop the currently playing song
                ctx.voice_client.stop()
            
            # Play the next song in the queue
            await ctx.send("Playing the next song...")
            await self.play_song(ctx)
        else:
            await ctx.send("The bot is not connected to a voice channel.")
        
    @commands.command(help="Get Current volume or Set the volume (0 to 100).")
    async def volume(self, ctx, volume: int= 0):
        if not volume:
            # Normalize volume from range 0.0 to 2.0 to percentage
            await ctx.send(f"Current Volume: {int(self.current_volume * 50)}")
            return
        
        if not (10 <= volume <= 100):
            await ctx.send("Volume must be between 10 and 100.")
            return

        if ctx.voice_client is None:
            await ctx.send("Bot is not connected to a voice channel.")
            return

        # Normalize volume to the range 0.0 to 2.0
        self.current_volume = volume / 50.0

        await ctx.send(f"Volume set to {volume}%. Changes will apply on next song.")
        
    @commands.command(help="Prints HELLO!.")
    async def hello(self, ctx):
        await ctx.send("HELLO!")        
            
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state updates."""
        if self.current_ctx and self.current_ctx.voice_client and before.channel and not after.channel and member == self.current_ctx.author:
            await self.current_ctx.send(f"{member.mention} has left the voice channel. The bot will now disconnect.")
            print(f"{member} has left the voice channel. Disconnecting the bot.")
            await self.current_ctx.voice_client.disconnect()

def main():
    bot = Spoty_bot()
    bot.run(discord_token)

if __name__ == '__main__':
    main()
