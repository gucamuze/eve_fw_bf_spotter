import discord
import os
from icecream import ic
from datetime import datetime, timedelta
from dotenv import load_dotenv
from discord.ext import tasks, commands
from eve_bf_spotter import bf_spotter_get_bf_completion, task_must_run

load_dotenv()
token = os.getenv('BOT_TOKEN')
bot_channel_id = int(os.getenv('BOT_CHANNEL_ID'))
bot_channel_id_galmil = int(os.getenv('BOT_CHANNEL_ID_GALMIL'))

next_task_scheduled_time = None
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
bot_channel: discord.channel = None

async def bot_send_message(message: discord.Embed | str):
    global bot_channel
    if bot_channel:
        if (type(message) is discord.Embed):
            await bot_channel.send(embed=message)
        elif type(message) is str:
            await bot_channel.send(message)
    else:
        print("Channel not found")

async def send_battlefield_status_to_channel(all_bf_infos: list[dict], custom_time = None):
    for bf_infos in all_bf_infos:
        battlefield_message = discord.Embed(
            title=f"{bf_infos['system_name']} -- {bf_infos['bf_type']} battlefield {bf_infos['outcome']}",
            timestamp=datetime.now() if custom_time is None else custom_time,
            color= discord.Color.green() if bf_infos['outcome'] == "won" else discord.Color.red()
        )
        if bf_infos["system_vp_percent"] is not None:
            battlefield_message.add_field(name="System contest:",
                                            value=f"{bf_infos['system_vp_percent']:.2f}%",
                                            inline=False)
        if not custom_time:
            time = datetime.now()
        battlefield_message.add_field(name=f"Next {bf_infos['bf_type']} battlefield time estimate:",
                                        value=f'{(time + timedelta(hours=2)).strftime("%A, %B %d, %Y %I:%M:%S %p -- EVE time")}',
                                        inline=False)
        await bot_send_message(battlefield_message)

# TODO: Check if system is in the actual list of fw systems
def is_valid_system(system: str) -> bool:
    return True
    
def is_valid_bf_type(bf_type: str) -> bool:
    return bf_type.lower() == "offensive" or bf_type.lower() == "defensive"

def is_valid_bf_status(bf_status: str) -> bool:
    return bf_status.lower() == "won" or bf_status.lower() == "lost"
    
def check_all_add_command_args(args: tuple[str]) -> str | None:
    if len(args) != 4:
        return f"Add command: invalid number of args, needs 3, got {len(args)} instead"
    error_message = ""
    if not is_valid_system(args[1]):
        error_message += "invalid system"
    if not is_valid_bf_type(args[2]):
        error_message += f'{", " if not is_valid_system(args[1]) else ""}invalid type'
    if not is_valid_bf_status(args[3]):
        error_message += f'{", " if not is_valid_system(args[1]) or not is_valid_bf_type(args[2]) else ""}invalid status'
    return f"Add command: {error_message}" if error_message else None

# valid add command => !add_bf [system, bf_type, bf_status, time]
# example: !add_bf Heydieles offensive won 17:30
async def add_custom_bf(command: str) -> bool:
    args = tuple(map(str, command.split(" ")))
    error_message = check_all_add_command_args(args)
    if error_message is not None:
        await bot_send_message(error_message)
    else:
        custom_bf = {"system_name" : args[1],
                     "bf_type" : args[2],
                     "outcome" : args[3],
                     "system_vp_percent" : None}
        print(custom_bf)
        await send_battlefield_status_to_channel([custom_bf])
        

@bot.event
async def on_message(message: discord.message):
    if message.author.id != bot.user.id and message.channel.id == bot_channel_id:
        if message.content.startswith(("!edit_bf", "!add_bf", "!delete_bf")):
            if message.content.startswith("!add_bf"):
                await add_custom_bf(message.content)
            else:
                await bot_send_message(f"Command {message.content} not yet implemented")
        else:
            await bot_send_message("Invalid command")
    

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
    global bot_channel
    bot_channel = bot.get_channel(bot_channel_id)
    # await channel.send("TEST")
    # message_history = bot_channel.history(limit=100)
    # async for message in message_history:
    #     if message.author.id == bot.user.id:
    #         ic(message)
    print(f'Logged as {bot.user}, {bot.user.id}')    
    background_task.start()
    

if __name__ == "__main__" :
    bot.run(token)
    