import discord
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('BOT_TOKEN')
bot_channel_id = int(os.getenv('BOT_CHANNEL_ID'))

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'Logged as {bot.user}')
    channel = bot.get_channel(bot_channel_id)
    if channel:
        await channel.send("Bot online !")
    else:
        print("Channel not found, check channel ID")
    
    
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

bot.run(token)