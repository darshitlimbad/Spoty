import os
from dotenv import load_dotenv
from subprocess import run
import yt_dlp
import logging
import colorlog

import discord
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext import commands

from CustomQueue import Queue

# Load environment variables from .env file
load_dotenv()
discord_token = os.getenv("discord_token")
adminID = os.getenv("adminID")

# Set up logging with color formatting
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    "%(log_color)s %(asctime)s %(levelname)s: %(message)s"
))

logger = colorlog.getLogger('colored_logger')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def search_song(query):
    """Search for a song on YouTube by query.

    Args:
        query (str): The search query for the song.

    Returns:
        dict: A dictionary containing the title and URL of the first result.
    """
    try:
        ydl_opts = {
            'format': 'bestaudio[abr>0]/bestaudio/best',
            'default_search': 'ytsearch',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"{query} Song or Music", download=False)
            if 'entries' in info:
                audio = info['entries'][0]
                return {'title': audio['title'], 'url': audio['url']}
        return {'title': None, 'url': None}

    except Exception as e:
        logger.error(f"Error occurred while fetching song: {e}")
        return {'title': None, 'url': None}

def search_by_query(query):
    """Search YouTube by query or URL and return the first result.

    Args:
        query (str): The search query or URL.

    Returns:
        dict: A dictionary containing the title and URL of the first result.
    """
    try:
        ydl_opts = {
            'format': 'bestaudio[abr>0]/bestaudio/best',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if 'youtube.com' in query or 'youtu.be' in query:
                info = ydl.extract_info(query, download=False)
            else:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)
                
            if 'entries' in info: 
                audio = info['entries'][0]
                return {'title': audio['title'], 'url': audio['url']}
            elif 'url' in info:
                return {'title': info.get('title', "Title Not Found"), 'url': info['url']}
            
        return {'title': None, 'url': None}
    except Exception as e:
        logger.error(f"Error occurred while fetching audio: {e}")
        return {'title': None, 'url': None}

def format_queue(queue):
    """Format the song queue for display in an embed.

    Args:
        queue (list): A list of dictionaries where each dictionary represents a song with a 'title' key.

    Returns:
        discord.Embed: An embed containing the formatted song queue.
    """
    embed = discord.Embed(title="Current Queue", color=discord.Color.blue())
    
    header="Index Song"
    entries = [header]
    
    for i, song in enumerate(queue, start=1):
        title = song.get('title', "N/A")
        short_title = ' '.join(title.split()[:4])
        entry = f"#{i:<5} {short_title:<20}"
        entries.append(entry)

    formatted_queue = "\n".join(entries)

    embed.description = f"```\n{formatted_queue}\n```"
    
    return embed

class Spoty_bot(commands.Bot):
    """Main bot class for handling commands and events."""

    def __init__(self):
        """
        Initialize the bot with a command prefix and all intents.
        Removes the default help command.
        """
        super().__init__(command_prefix='!', intents=discord.Intents.all())
        self.remove_command('help')

    async def on_ready(self):
        """
        Called when the bot has successfully connected and is ready.
        Logs the bot's status and prints a separator line.
        """
        
        await self.tree.sync()
        logger.info("Bot is online and ready to serve.")
        print("-" * 150)

    async def setup_hook(self):
        """
        Sets up the bot by loading cogs and synchronizing the command tree.
        """
        await self.add_cog(Player(self))
        # await self.load_extension('player')
    
    async def on_command_error(self, ctx, error):
        """
        Handles errors that occur during command execution.
        Provides specific responses for common errors and logs detailed information.
        """
        if isinstance(error, commands.CommandNotFound):
            embed = discord.Embed(
                title="Command Not Found",
                description="The command you tried to use does not exist. Please verify the command and try again.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            logger.warning(f"CommandNotFound: {ctx.message.content}")

        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Missing Argument",
                description=f"A required argument is missing: `{str(error.param)}`.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            logger.warning(f"MissingRequiredArgument: {error}")

        else:
            embed = discord.Embed(
                title="An Error Occurred",
                description=f"An unexpected error occurred: `{str(error)}`.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            logger.error(f"Unhandled error: {error}", exc_info=True)


class Player(commands.Cog):
    """Cog to handle music playback commands."""
    def __init__(self, bot):
        self.bot = bot
        self.adminID = adminID          # Admin ID for the bot
        self.current_ctx = None         # Tracks the current context for the bot
        self.current_volume = None      # Default volume level for playback
        self.Queue = Queue()            # Queue to manage upcoming songs
        self.auto_play= False           # should auto play or not 
        
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
                self.current_volume = 50     # Default volume level for playback
                embed = discord.Embed(title="Connected", description=f"Connected to voice channel: **{channel.name}**", color=discord.Color.green())
                await ctx.send(embed=embed)
                logger.info(f"Connected to voice channel: {channel.name}.")
                return True
            else:
                embed = discord.Embed(
                    title="Error",
                    description="You need to be in a voice channel to play music.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return False
        except Exception as e:
            embed = discord.Embed(
                title="Connection Error",
                description=f"Failed to connect to the voice channel",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            logger.error(f"Error while connecting to voice channel: {e}")
            return False
    
    async def is_user_authorized_to_control(self, ctx) -> bool:
        """Check if the user is authorized to control the bot."""
        if ctx.voice_client and (ctx.author.voice and ctx.voice_client.channel == ctx.author.voice.channel) or ctx.author.id == self.adminID or ctx.author.id == self.bot.user.id: # admin get's full permision
            return True
        elif ctx.author.voice is None:
            embed = discord.Embed(
                title="Error",
                description="Please connect to the voice channel.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                    title="Error",
                    description="You must be in the same voice channel as the bot to control it.",
                    color=discord.Color.red()
            )
            
        await ctx.send(embed=embed)
        return False
    
    async def play_song(self, ctx):
        """Play the next song in the queue."""
        try:
            if ctx.voice_client is None:
                embed = discord.Embed(
                    title="Error",
                    description="The bot is not connected to a voice channel.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                logger.error("Error: Attempted to play a song when the bot is not connected.")
                return

            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                logger.error("Error: Attempted to play the next song while a song is already playing.")
                return
            
            if not self.Queue.is_empty():
                ffmpeg_options = {
                    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                    'options': '-vn',
                }
                
                if self.auto_play is False :
                    self.auto_play= True
                    
                song = self.Queue.get()
                source = FFmpegPCMAudio(song['url'], **ffmpeg_options)
                source = PCMVolumeTransformer(source, self.current_volume/100)
                
                ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_song(ctx) if self.auto_play is True else None ))
        
                embed = discord.Embed(title="Now Playing", description=f"**{song['title']}**", color=discord.Color.blue())
                await ctx.send(embed=embed)
                logger.info(f"Playing song: {song['title']}")
            else:
                logger.info("Queue is now empty.")
                embed = discord.Embed(title="Queue Empty", description="The queue is empty.", color=discord.Color.red())
                await ctx.send(embed=embed)
                
        except Exception as e:
            embed = discord.Embed(
                title="Playback Error",
                description=f"An error occurred during playback",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            logger.error(f"Error during playback: {e}", exc_info=True)
    
    @commands.hybrid_command(name="help", with_app_command=True)
    async def help_command(self, ctx,*, command: str = None):
        """Displays the help message with available commands or detailed info for a specific command."""
        embed = discord.Embed(title="Help", color=discord.Color.blue())

        if command is None:
            embed.add_field(name="Songs Players", value=(
                "`play` - Plays song from the given song query.\n"
                "`playnow` - Stops current playback, clears the queue, and immediately plays... \n"
                "`sourceplay` - Plays audio from the given URL or query. ...\n"
            ), inline=False)

            embed.add_field(name="Playback Control", value=(
                "`pause` - Pauses the current song.\n"
                "`resume` - Resumes the current song.\n"
                "`skip` - Skips the currently playing song and plays the next song in the queue.\n"
                "`stop` - Stops the current song and clears the queue.\n"
                "`disconnect` - Disconnects the bot from the voice channel.\n"
                "`queue` - Gives you list of upcomming songs.\n"
            ), inline=False)

            embed.add_field(name="Sources", value=(
                "`sitelist` - Lists the websites from which you can play audio.\n"
            ), inline=False)

            embed.add_field(name="No Category", value="`help` - Shows this message", inline=False)
            embed.set_footer(text="Type `!help [command]` for more info on a command.")
        else:
            # Detailed info for a specific command
            command_info = {
                'play': "`play` - Plays song from the given song query. This command starts playing the song that matches the given query.",
                'playnow': "`playnow` - Stops current playback, clears the queue, and immediately plays the specified song. This command is useful if you want to clear the queue and play a new song immediately.",
                'sourceplay': "`sourceplay` - Plays media from the given URL or query. For a list of supported URLs, use `sitelist`. This command is used to play media from a specified URL or query.",
                'pause': "`pause` - Pauses the current song. Use this command if you want to temporarily stop the playback of the current song.",
                'resume': "`resume` - Resumes the current song. Use this command to continue playback if a song was previously paused.",
                'skip': "`skip` - Skips the currently playing song and plays the next song in the queue. This command is used to skip the current song and proceed to the next one.",
                'stop': "`stop` - Stops the current song and clears the queue. Use this command to stop the playback and remove all songs from the queue.",
                'disconnect': "`disconnect` - Disconnects the bot from the voice channel. Use this command when you want to stop the bot from playing music and disconnect it from the voice channel.",
                'queue':" queue Gives you list of all upcomming songs from the queue with their indexes you can use `skip` command to jump to the corrosponding index of the song",
                'sitelist': "`sitelist` - Lists the websites from which you can play audio. This command provides a list of supported websites for audio playback.",
                'help': "`help` - Shows this help message. Use this command to get information about all available commands."
            }

            description = command_info.get(command.lower(), "Command not found. Please provide a valid command.")
            embed.add_field(name=f"Help for `{command}`", value=description, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="play", with_app_command=True)
    async def play(self, ctx, *, query=None):
        """Play a song from a search query."""
        try:
            if query is None:
                embed = discord.Embed(
                    title="Error",
                    description=f"A required argument is missing: `query`.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            if not await self.is_bot_connected_to_voice(ctx):
                if not await self.join(ctx):
                    return
            elif not await self.is_user_authorized_to_control(ctx):
                return
            
            processing_embed = discord.Embed(
                title="Processing...",
                description="Your request is being processed. Please wait a moment.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=processing_embed)
    
            song = search_song(query)
            if song['url']:
                self.Queue.put(song)
                
                if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                    await self.play_song(ctx)
                    return
                
                embed = discord.Embed(
                    title="Added to Queue",
                    description=f"**{song['title']}** has been added to the `queue`.",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                logger.info(f"Added song to queue: {song['title']}")
            else:
                embed = discord.Embed(
                    title="Search Error",
                    description="No results found for your query.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred while processing your request",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            logger.error(f"Error in play command: {e}")
            
    @commands.hybrid_command(name="sourceplay", with_app_command=True)
    async def sourceplay(self, ctx, *, query=None):
        """Play any media from a YouTube URL or query."""
        try:
            if query is None:
                embed = discord.Embed(
                    title="Error",
                    description=f"A required argument is missing: query.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            if not await self.is_bot_connected_to_voice(ctx):
                if not await self.join(ctx):
                    return
            elif not await self.is_user_authorized_to_control(ctx):
                return
            
            processing_embed = discord.Embed(
                title="Processing...",
                description="Your request is being processed. Please wait a moment.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=processing_embed)
            
            song = search_by_query(query)
            if song['url']:
                self.Queue.put(song)
                
                if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                    await self.play_song(ctx)
                    return
                
                embed = discord.Embed(
                    title="Added to Queue",
                    description=f"**{song['title']}** has been added to the queue.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
                logger.info(f"Added media to queue: {song['title']}")
            else:
                embed = discord.Embed(
                    title="Search Error",
                    description="No results found for your query.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred while processing your request",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            logger.error(f"Error in sourceplay command: {e}")
            
    @commands.hybrid_command(name="playnow", with_app_command=True)
    async def playnow(self, ctx, *, query=None):
        try:
            
            await self.stop(ctx)
            await self.play(ctx,query=query)
            
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred while processing your request",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            logger.error(f"Error in playnow command: {e}")
        
    @commands.hybrid_command(name="pause", with_app_command=True)
    async def pause(self, ctx):
        """Pause the currently playing song."""
        if await self.is_user_authorized_to_control(ctx) and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            embed = discord.Embed(title="Paused", description="Playback has been paused.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            logger.info("Playback paused.")
        else:
            embed = discord.Embed(
                title="Error",
                description="No song is currently playing.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="resume", with_app_command=True)
    async def resume(self, ctx):
        """Resume the paused song."""
        if await self.is_user_authorized_to_control(ctx) and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            embed = discord.Embed(title="Resumed", description="Playback has resumed.", color=discord.Color.green())
            await ctx.send(embed=embed)
            logger.info("Playback resumed.")
        else:
            embed = discord.Embed(
                title="Error",
                description="No song is currently paused.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="skip", with_app_command=True)
    async def skip(self, ctx, index=None):
        """
        Command to skip the current song and play the next one.

        Args:
            ctx (commands.Context): The context in which the command was invoked.
            index (int, optional): The index of the song in the queue to skip to. Defaults to None, which skips to the next song.
        """
        try:
            if not await self.is_user_authorized_to_control(ctx):
                return

            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                if index is not None:
                    index = int(index) - 1
                    self.Queue.shuffle_index(index, 0)

                # Stop the current song to skip to the next 
                ctx.voice_client.stop() # after= will call self.play_song() automatically
                embed_skip = discord.Embed(title="Song Skipped", color=discord.Color.orange())
                await ctx.send(embed=embed_skip)
                logger.info("Song skipped.")
                
            else:
                embed = discord.Embed(title="No Song Playing", description="There is currently no song playing.", color=discord.Color.red())
                await ctx.send(embed=embed)
                logger.warning("Attempted to skip when no song was playing.")
        
        except (ValueError, IndexError):
            embed = discord.Embed(
                title="Error",
                description="Please provide a valid index (e.g., 1).",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            logger.error(f"Invalid input for index: {index}")
    
        except Exception as e:
            embed = discord.Embed(title="Error", description="Something went wrong!", color=discord.Color.red())
            await ctx.send(embed=embed)
            logger.error(f"Error during skip command: {e}")


    @commands.hybrid_command(name="stop", with_app_command=True)
    async def stop(self, ctx):
        """Stop the playback and clear the queue."""
        if await self.is_user_authorized_to_control(ctx):
            self.Queue.clear()
            self.auto_play = False
            ctx.voice_client.stop()
            embed = discord.Embed(title="Stopped", description="Playback has been stopped, and the queue is cleared.", color=discord.Color.red())
            await ctx.send(embed=embed)
            logger.info("Playback stopped and queue cleared.")
    
    @commands.hybrid_command(name="disconnect", with_app_command=True)
    async def disconnect(self, ctx):
        """Disconnect the bot from the voice channel."""
        try:
            if await self.is_user_authorized_to_control(ctx):
                await self.stop(ctx)
                await ctx.voice_client.disconnect()
                self.current_ctx = None
                embed = discord.Embed(
                    title="Disconnected",
                    description="The bot has been successfully disconnected from the voice channel.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
                logger.info("Bot disconnected from voice channel.")
            else:
                embed = discord.Embed(
                    title="Error",
                    description="Bot is not connected to a voice channel.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
            
        except Exception as e:
                embed = discord.Embed(
                    title="Disconnection Error",
                    description=f"An error occurred while attempting to disconnect:`.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                logger.error(f"Error during disconnection: {e}", exc_info=True)
    
    @commands.hybrid_command(name="queue", with_app_command=True)
    async def queue(self, ctx):
        """Display the current song queue."""
        try:
            if self.Queue.is_empty():
                embed = discord.Embed(
                    title="Queue Empty",
                    description="There are no songs in the queue.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            embed = format_queue(self.Queue.queue())
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred while retrieving the queue",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            logger.error(f"Error in queue command: {e}")
            
    @commands.hybrid_command(name="volume", with_app_command=True)
    async def volume(self, ctx, volume = None):
        """Set the volume level or return the current volume if no value is provided."""
        if await self.is_user_authorized_to_control(ctx):
            try:
                if volume is None:
                    embed = discord.Embed(
                        title="Current Volume",
                        description=f"The current volume is :{self.current_volume}%",
                        color=discord.Color.blue()
                    )
                    await ctx.send(embed=embed)
                else:
                    volume= int(volume)
                    if not 0 <= volume <= 100:
                        embed = discord.Embed(
                            title="Invalid Volume",
                            description="Volume must be between 0 and 100.",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)
                        return
                    
                    self.current_volume = volume
                    ctx.voice_client.source.volume = self.current_volume / 100
                    embed = discord.Embed(title="Volume Set", description=f"Volume has been set to {volume}%.", color=discord.Color.green())
                    await ctx.send(embed=embed)
                    logger.info(f"Volume set to {volume}%.")
                    
            except ValueError:
                embed = discord.Embed(
                    title="Invalid Volume Level",
                    description="Please enter a volume level between 0 to 100.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                logger.error(f"Invalid Volume Level input:{volume}")
            
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handles voice state updates, including when a member leaves the voice channel."""
        if self.current_ctx and self.current_ctx.voice_client and before.channel and not after.channel and member == self.current_ctx.author:
            # Notify that the member has left the voice channel
            embed = discord.Embed(
                title="Voice Channel Update",
                description=f"{member.mention} has left the voice channel. The bot will now disconnect.",
                color=discord.Color.red()
            )
            message= await self.current_ctx.send(embed=embed)
            tempctx = await bot.get_context(message)
            # Log the event
            logger.info(f"{member} has left the voice channel. Disconnecting the bot.")
            
            # Disconnect the bot from the voice channel
            await self.disconnect(tempctx)
                
if __name__ == '__main__':
    bot = Spoty_bot()
    bot.run(discord_token)
