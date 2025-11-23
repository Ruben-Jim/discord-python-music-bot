import discord
from discord.ext import commands
import yt_dlp
from youtube_search import YoutubeSearch
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Queue & loop storage
bot.music_queue = {}
bot.loop_mode = {}  # 0=off, 1=single, 2=all

ytdl_format_options = {
    'format':
    'bestaudio/best',
    'noplaylist':
    True,
    'nocheckcertificate':
    True,
    'ignoreerrors':
    False,
    'quiet':
    True,
    'no_warnings':
    True,
    'default_search':
    'auto',
    'source_address':
    '0.0.0.0',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

ffmpeg_options = {
    'before_options':
    '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -filter:a "volume=0.75"'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, volume=0.75):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')

    @classmethod
    async def from_url(cls, url, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=False))
        if 'entries' in data:
            data = data['entries'][0]
        return cls(discord.FFmpegPCMAudio(data['url'], **ffmpeg_options),
                   data=data)


async def play_next(ctx):
    guild_id = ctx.guild.id
    if not bot.music_queue.get(guild_id):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        return

    queue = bot.music_queue[guild_id]
    loop = bot.loop_mode.get(guild_id, 0)

    if loop == 1:  # single
        song = queue[0]
    elif loop == 2:  # all
        song = queue[0]
        queue.append(queue.pop(0))
    else:
        song = queue.pop(0)

    player = await YTDLSource.from_url(song['url'], loop=bot.loop)
    ctx.voice_client.play(player,
                          after=lambda e: asyncio.run_coroutine_threadsafe(
                              play_next(ctx), bot.loop))

    embed = discord.Embed(title="Now Playing",
                          description=player.title,
                          color=0x00ff00)
    if player.duration:
        mins, secs = divmod(player.duration, 60)
        embed.add_field(name="Duration",
                        value=f"{mins}:{secs:02d}",
                        inline=True)
    embed.set_thumbnail(url=player.thumbnail)
    embed.set_footer(text=f"Requested by {song['requester']}")
    await ctx.send(embed=embed)


@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online and ready to play music!")


# ===================== COMMANDS =====================


@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(f"Joined {channel}")
    else:
        await ctx.send("You need to be in a voice channel first!")


@bot.command(aliases=['dc', 'disconnect'])
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        bot.music_queue.pop(ctx.guild.id, None)
        bot.loop_mode.pop(ctx.guild.id, None)
        await ctx.send("Disconnected and cleared everything.")
    else:
        await ctx.send("I'm not in a voice channel.")


@bot.command(aliases=['p', 'play'])
async def play(ctx, *, query: str):
    if not ctx.voice_client:
        await ctx.invoke(join)

    # Search YouTube if not a URL
    if not query.startswith("http"):
        results = YoutubeSearch(query, max_results=1).to_dict()
        if not results:
            return await ctx.send("No results found.")
        url = f"https://www.youtube.com/watch?v={results[0]['id']}"
        title = results[0]['title']
    else:
        url = query
        title = query

    # Add to queue
    bot.music_queue.setdefault(ctx.guild.id, []).append({
        "url":
        url,
        "title":
        title,
        "requester":
        ctx.author.display_name
    })

    embed = discord.Embed(title="Added to queue",
                          description=title,
                          color=0x5865F2)
    embed.set_footer(text=f"Position #{len(bot.music_queue[ctx.guild.id])}")
    await ctx.send(embed=embed)

    # Start playing if nothing is playing
    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        await play_next(ctx)


@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ Skipped!")


@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸ Paused")


@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶ Resumed")


@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        bot.music_queue[ctx.guild.id].clear()
        await ctx.send("⏹ Stopped and cleared queue")


@bot.command(aliases=['q'])
async def queue(ctx):
    songs = bot.music_queue.get(ctx.guild.id, [])
    if not songs:
        return await ctx.send("Queue is empty")
    text = "\n".join(f"{i+1}. **{s['title']}** — {s['requester']}"
                     for i, s in enumerate(songs[:15]))
    embed = discord.Embed(title=f"Queue ({len(songs)} songs)",
                          description=text,
                          color=0x5865F2)
    await ctx.send(embed=embed)


@bot.command()
async def loop(ctx, mode: str | None = None):
    if mode is None:
        current = bot.loop_mode.get(ctx.guild.id, 0)
        modes = ["off", "single", "queue"]
        return await ctx.send(f"Loop mode: **{modes[current]}**")

    mode = mode.lower()
    if mode in ["off", "0"]:
        bot.loop_mode[ctx.guild.id] = 0
        msg = "off"
    elif mode in ["single", "one", "1"]:
        bot.loop_mode[ctx.guild.id] = 1
        msg = "single song"
    elif mode in ["all", "queue", "2"]:
        bot.loop_mode[ctx.guild.id] = 2
        msg = "entire queue"
    else:
        return await ctx.send("Usage: !loop [off | single | queue]")
    await ctx.send(f"Loop mode → **{msg}**")


@bot.command(aliases=['vol'])
async def volume(ctx, vol: int):
    if ctx.voice_client and ctx.voice_client.source:
        vol = max(0, min(200, vol))
        ctx.voice_client.source.volume = vol / 100
        await ctx.send(f"Volume set to {vol}%")


# =============== RUN THE BOT ===============
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    print("❌ Error: DISCORD_BOT_TOKEN environment variable not set!")
    print("Please add your Discord bot token as a secret.")
    exit(1)
    
bot.run(TOKEN)
