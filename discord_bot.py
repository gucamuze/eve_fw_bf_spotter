import discord
import os
import time
import datetime
from dotenv import load_dotenv
from discord.ext import commands, tasks
from eve_bf_spotter import bf_spotter_get_bf_completion, task_must_run

load_dotenv()
token = os.getenv('BOT_TOKEN')
bot_channel_id = int(os.getenv('BOT_CHANNEL_ID'))
next_task_scheduled_time = None

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

@tasks.loop(minutes=1)
async def background_task():
    global next_task_scheduled_time
    if task_must_run(next_task_scheduled_time):
        print("Task run")
        channel = bot.get_channel(bot_channel_id)
        if channel:
            results = await bf_spotter_get_bf_completion()
            if results is not None:
                if results[1] is not None:
                    await channel.send(results[1])
                next_task_scheduled_time = results[0]
                print(f"Next task run: {next_task_scheduled_time}")

@bot.event
async def on_ready():
    print(f'Logged as {bot.user}')
    background_task.start()


     
bot.run(token)