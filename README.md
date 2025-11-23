# Discord Music Bot

A feature-rich Discord music bot that plays music from YouTube in voice channels.

## Features

- 🎵 Play music from YouTube (search or direct URLs)
- ⏯️ Pause, resume, and skip tracks
- 🔁 Loop modes (single song, entire queue)
- 📋 Queue management
- 🔊 Volume control
- 🎮 Easy-to-use commands

## Commands

- `!play <song>` or `!p <song>` - Play a song (searches YouTube)
- `!pause` - Pause the current song
- `!resume` - Resume playing
- `!skip` - Skip to next song in queue
- `!stop` - Stop playing and clear the queue
- `!queue` or `!q` - Show the current queue
- `!loop [off/single/queue]` - Set loop mode
- `!volume <0-200>` or `!vol <number>` - Adjust volume (default: 75%)
- `!join` - Join your voice channel
- `!leave` or `!dc` - Leave voice channel and clear queue

## Deployment on Railway

### Prerequisites
- A Discord bot token from [Discord Developer Portal](https://discord.com/developers/applications)
- A [Railway.app](https://railway.app) account

### Setup Steps

1. **Fork or clone this repository**

2. **Create a new project on Railway:**
   - Go to [Railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Select this repository

3. **Add environment variable:**
   - In Railway project settings, go to "Variables"
   - Add: `DISCORD_BOT_TOKEN` = `your-bot-token-here`

4. **Deploy:**
   - Railway will automatically detect the `Procfile` and deploy
   - Your bot will start running automatically!

### Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application or select your existing one
3. Go to the "Bot" tab:
   - Copy your bot token for Railway
   - Enable these Privileged Gateway Intents:
     - ✅ MESSAGE CONTENT INTENT (required)
     - ✅ SERVER MEMBERS INTENT (optional)
     - ✅ PRESENCE INTENT (optional)
4. Go to "OAuth2" → "URL Generator":
   - Select scopes: `bot`
   - Select permissions: `Connect`, `Speak`, `Send Messages`, `Read Messages/View Channels`
   - Copy the generated URL and use it to invite the bot to your server

## Requirements

- Python 3.11+
- discord.py
- yt-dlp
- youtube-search-python
- PyNaCl
- FFmpeg (automatically installed on Railway)

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable
export DISCORD_BOT_TOKEN="your-token-here"

# Run the bot
python main.py
```

## Notes

- The bot requires FFmpeg for audio processing (included in Railway)
- Voice connections require UDP access (not available on Replit)
- Free tier on Railway includes enough hours for testing

## License

MIT License - feel free to modify and use as you wish!
