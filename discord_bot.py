import discord
import os
from icecream import ic
from datetime import datetime
from dotenv import load_dotenv
from discord.ext import tasks

from eve_bf_spotter import bf_spotter_get_bf_completion, task_must_run
from bf_bot_commands import dispatch_message, send_battlefield_status_to_all_channels, add_custom_bf

load_dotenv()
token: str = os.getenv('BOT_TOKEN')
test_channel_id: int = int(os.getenv('BOT_CHANNEL_ID'))
galmil_channel_id: int = int(os.getenv('BOT_CHANNEL_ID_GALMIL'))
all_channels_ids: list[int] = [test_channel_id, galmil_channel_id]
all_channels: list[discord.TextChannel] = []

next_task_scheduled_time: datetime | None = None
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
        
@bot.event
async def on_message(message: discord.message):
    test_channel = all_channels[0]
    # TODO: message.channel.id == all_channels_ids[0] will need to be message.channel.id in all_channels_id
    if message.author.id != bot.user.id and message.channel.id == test_channel.id:
        if message.content.startswith(("!edit_bf", "!add_bf", "!delete_bf")):
            if message.content.startswith("!add_bf"):
                await add_custom_bf(message.content, all_channels)
            else:
                await dispatch_message(f"Command {message.content} not yet implemented", test_channel)
        else:
            await dispatch_message("Invalid command", test_channel)
    

@tasks.loop(minutes=1)
async def background_task():
    global next_task_scheduled_time
    if task_must_run(next_task_scheduled_time):
        print("Task run")
        results = await bf_spotter_get_bf_completion()
        if results is not None:
            if results[1]:
                await send_battlefield_status_to_all_channels(results[1], all_channels)
            next_task_scheduled_time = results[0]
            print(f"Next task run: {next_task_scheduled_time}")
        else:
            print("BF_spotter not working, ESI might be unreachable")

@bot.event
async def on_ready():
    global all_channels
    
    print(f'Logged as {bot.user}, {bot.user.id}')
    for channel_id in all_channels_ids:
        all_channels.append(bot.get_channel(channel_id))
    background_task.start()

if __name__ == "__main__" :
    bot.run(token)
    