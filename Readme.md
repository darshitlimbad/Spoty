# Spoty Discord Bot

Welcome to Spoty, your ultimate Discord music companion! Spoty offers seamless audio streaming and management within your Discord server. Below is a guide to using the bot and its commands.

## Commands

- **`play`**: Plays song from the given song query. This command starts playing the song that matches the given query.
- **`playnow`**: Stops current playback, clears the queue, and immediately plays the specified song. This command is useful if you want to clear the queue and play a new song immediately.
- **`sourceplay`**: Plays media from the given URL or query. For a list of supported URLs, see `sitelist`. This command is used to play media from a specified URL or query.
- **`pause`**: Pauses the current song. Use this command if you want to temporarily stop the playback of the current song.
- **`resume`**: Resumes the current song. Use this command to continue playback if a song was previously paused.
- **`skip`**: Skips the currently playing song and plays the next song in the queue. This command is used to skip the current song and proceed to the next one.
- **`stop`**: Stops the current song and clears the queue. Use this command to stop the playback and remove all songs from the queue.
- **`disconnect`**: Disconnects the bot from the voice channel. Use this command when you want to stop the bot from playing music and disconnect it from the voice channel.
- **`queue`**: Gives you a list of all upcoming songs in the queue with their indexes. You can use the `skip` command to jump to the corresponding index of the song.
- **`repeat`**: Toggles repeat mode for the currently playing media.
- **`sitelist`**: Lists the websites from which you can play audio. This command provides a list of supported websites for audio playback.
- **`help`**: Shows this help message. Use this command to get information about all available commands.

## Setup

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/darshitlimbad/Spoty.git
   ``` 

2. **Install Dependencies:**

   Ensure you have Python 3.8+ installed. Then install the required libraries:

    ```bash
    pip install discord.py
    pip install yt_dlp
    ```

    Additionally, make sure you have [FFMPEG](https://ffmpeg.org/download.html) downloaded and installed.

3. **Configure Your Bot:**

    Give your bot all of the permission and then,
    Create a `config.json` file in the root directory with the following structure:

    ```json
    {
        "TOKEN": "YOUR_DISCORD_BOT_TOKEN",
        "PREFIX": "!",
        "ADMINID": "YOUR_DISCORD_ADMIN_ID"  
    }
    ``` 
    Node: ADMINID is optional if you don't want to give admin id just make it any number like 1232 any thing.

4. **Run the Bot:**

   Execute the bot script:

   ```bash
   python main.py
   ``` 

## Development

To contribute or customize the bot, follow these steps:

1. **Fork the Repository** and create a new branch for your changes.
2. **Make Your Changes** and test thoroughly.
3. **Submit a Pull Request** with a clear description of your modifications.
## License

IDK :)

## Contact

For any issues or questions, feel free to reach out (please don't :) )
