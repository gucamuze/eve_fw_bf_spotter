import discord
from icecream import ic
from datetime import datetime, timedelta


## MESSAGING AND DISPATCH ##
############################
async def bot_send_message_to_channel(message: discord.Embed | str, channel: discord.TextChannel):
    if (type(message) is discord.Embed):
        await channel.send(embed=message)
    elif type(message) is str:
        await channel.send(message)

# Sends message or Embed to all channels by default or to specified channel
async def dispatch_message(message: discord.Embed | str, send_to: list[discord.TextChannel] | discord.TextChannel):
    if type(send_to) is list:
        for channel in send_to:
            await bot_send_message_to_channel(message, channel)
    elif type(send_to) is discord.TextChannel:
        await bot_send_message_to_channel(message, channel=send_to)
    else:
        print("Dispatch: invalid channel !")
        ic(message, send_to)

async def send_battlefield_status_to_all_channels(all_bf_infos: list[dict],
                                                  all_channels: list[discord.TextChannel],
                                                  custom_time = None):
    for bf_infos in all_bf_infos:
        bf_emote = ":shield:" if bf_infos['bf_type'] == "Defensive" else ":crossed_swords:"
        battlefield_message = discord.Embed(
            title=f"{bf_emote} {bf_infos['system_name']} -- {bf_infos['bf_type']} battlefield {bf_infos['outcome']}",
            timestamp=datetime.now() if custom_time is None else custom_time,
            color= discord.Color.green() if bf_infos['outcome'] == "won" else discord.Color.red()
        )
        if bf_infos["system_vp_percent"] is not None:
            battlefield_message.add_field(name="System contest:",
                                            value=f"{bf_infos['system_vp_percent']:.2f}%",
                                            inline=False)
        if bf_infos["system_adv"] is not None:
            adv = bf_infos['system_adv']
            faction_adv = ""
            if adv > 0:
                faction_adv = "Gallente"
            elif adv < 0:
                faction_adv = "Caldari"
            battlefield_message.add_field(name="System advantage:",
                                            value=f"{abs(adv)}% {faction_adv}",
                                            inline=False)

        if not custom_time:
            bf_time: datetime = datetime.now()
        battlefield_message.add_field(name=f"Next {bf_infos['bf_type']} battlefield time estimate:",
                                        value=f'<t:{(bf_time + timedelta(hours=3)).strftime("%s")}>',
                                        inline=False)
        await dispatch_message(battlefield_message, all_channels)
        
############################

## COMMANDS ##
##############

# CHECKS #

# TODO: Check if system is in the actual list of fw systems
def is_valid_system(system: str) -> bool:
    return True
    
def is_valid_bf_type(bf_type: str) -> bool:
    return bf_type.lower() == "offensive" or bf_type.lower() == "defensive"

def is_valid_bf_status(bf_status: str) -> bool:
    return bf_status.lower() == "won" or bf_status.lower() == "lost"
    
def check_all_add_command_args(args: tuple[str]) -> str | None:
    if len(args) != 4:
        return f"Add command: invalid number of args, needs 3, got {len(args) - 1} instead"
    error_message = ""
    if not is_valid_system(args[1]):
        error_message += "invalid system"
    if not is_valid_bf_type(args[2]):
        error_message += f'{", " if not is_valid_system(args[1]) else ""}invalid type'
    if not is_valid_bf_status(args[3]):
        error_message += f'{", " if not is_valid_system(args[1]) or not is_valid_bf_type(args[2]) else ""}invalid status'
    return f"Add command: {error_message}" if error_message else None

# COMMAND DISPATCH #

# valid add command => !add_bf [system, bf_type, bf_status, time]
# example: !add_bf Heydieles offensive won 17:30
async def add_custom_bf(command: str, send_to: discord.TextChannel | list[discord.TextChannel]) -> bool:
    args = tuple(map(str, command.split(" ")))
    error_message = check_all_add_command_args(args)
    if error_message is not None:
        await dispatch_message(error_message, send_to[0])
    else:
        #TODO: Fetch vp / adv dynamically
        custom_bf = {"system_name" : args[1],
                     "bf_type" : args[2],
                     "outcome" : args[3],
                     "system_vp_percent" : None,
                     "system_adv" : None}
        print(custom_bf)
        await send_battlefield_status_to_all_channels([custom_bf], send_to[0])