import discord
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from discord.ext import tasks
from eve_bf_spotter import bf_spotter_get_bf_completion, task_must_run

load_dotenv()
token = os.getenv('BOT_TOKEN')
bot_channel_id = int(os.getenv('BOT_CHANNEL_ID'))
next_task_scheduled_time = None

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

async def send_battlefield_status_to_channel(all_bf_infos):
    channel = bot.get_channel(bot_channel_id)
    if channel:
        for bf_infos in all_bf_infos:
            battlefield_message = discord.Embed(
                title=f"{bf_infos['system_name']} -- {bf_infos['bf_type']} battlefield {bf_infos['outcome']}",
                timestamp=datetime.now(),
                color= discord.Color.green() if bf_infos['outcome'] == "won" else discord.Color.red()
            )
            battlefield_message.add_field(name="System contest:", value=f"{bf_infos['system_vp_percent']:.2f}%", inline=False)
            battlefield_message.add_field(name=f"Next {bf_infos['bf_type']} battlefield time estimate:",
                                          value=f'{(datetime.now() + timedelta(hours=2)).strftime("%A, %B %d, %Y %I:%M:%S %p -- EVE time")}',
                                          inline=False)
            await channel.send(embed=battlefield_message)
            
    

@tasks.loop(minutes=1)
async def background_task():
    global next_task_scheduled_time
    if task_must_run(next_task_scheduled_time):
        print("Task run")
        results = await bf_spotter_get_bf_completion()
        if results is not None:
            if results[1]:
                await send_battlefield_status_to_channel(results[1])
            next_task_scheduled_time = results[0]
            print(f"Next task run: {next_task_scheduled_time}")
        else:
            print("BF_spotter not working, ESI might be unreachable")

@bot.event
async def on_ready():
    print(f'Logged as {bot.user}')    
    background_task.start()
     
bot.run(token)