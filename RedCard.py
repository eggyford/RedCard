import discord
from discord.ext import commands
from discord import app_commands
import logging
from dotenv import load_dotenv
import os
from typing import Optional
import json
import random
import gc

load_dotenv()

token = os.getenv('DISCORD_TOKEN')
guild = os.getenv('ID')
GUILD_ID = discord.Object(id=guild) # set to None to make updates global
EPHEMERAL = False # Set this false if u wanna debug easier
BLACKLIST_FILE = 'blacklist.json'
CONFIG_FILE = 'config.json'
MODSTATS_FILE = 'modstats.json'

try: # load blacklisted users from json
    with open(BLACKLIST_FILE, 'r') as f:
        blacklist_file = json.load(f)
except FileNotFoundError:
    blacklist_file = {}

try: # load server config from json
    with open(CONFIG_FILE, 'r') as f:
        config_file = json.load(f)
except FileNotFoundError:
    print('set up /config')
    config_file = {}

try:
    with open(MODSTATS_FILE, 'r') as f:
        modstats_file = json.load(f)
except FileNotFoundError:
    modstats_file = {}

# for config in config_file:
#     print(config)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='$', intents=intents)


# -------------------------------- BOT FUNCTION -------------------------------

def getcooldown(ctx: discord.Interaction):
    return app_commands.Cooldown(per=config_file[str(ctx.guild_id)]['cooldown'],
                                 rate=config_file[str(ctx.guild_id)]['rateLimit'])

    # -------------------------------- REPORT --------------------------------

@bot.tree.command(name='report', description='Report someone', guild=GUILD_ID)
@app_commands.describe(
    name='Roblox username.',
    link='Link video evidence.',
    attachment='Attach video evidence.',
    description='Type of report being submitted.'
)
@app_commands.checks.dynamic_cooldown(getcooldown, 
                                      key=lambda i: i.user.id)
@app_commands.choices(description=[
    app_commands.Choice(name='Aimbot', value='Aimbot'),
    app_commands.Choice(name='Flying', value='Flying'),
    app_commands.Choice(name='Esp', value='Esp'),
    app_commands.Choice(name='Shooting through walls', value='Wallbang'),
    app_commands.Choice(name='Other', value='Other')
])
async def report(ctx: discord.Interaction, name: str, link: Optional[str] = None, attachment: Optional[discord.Attachment] = None, description: app_commands.Choice[str] = None):
    print(f'Report called from {ctx.guild.id}')
    if ctx.user.id in blacklist_file[str(ctx.guild_id)]: # stop if user blacklisted
        await ctx.response.send_message('You have been blacklisted from making reports.', ephemeral=EPHEMERAL)
        
        del ctx
        gc.collect()
        return
        
    if attachment is not None:
        attachmentSizeMB = attachment.size / 1024 / 1024
        if attachmentSizeMB >= config_file[str(ctx.guild_id)]['maxFileSize']: # stop if uploaded file bigger than upload limit
            await ctx.response.send_message(content=f'File size limit is {config_file[str(ctx.guild_id)]['maxFileSize']}MB.\nTry uploading to https://www.youtu.be and sending the link instead.', ephemeral=EPHEMERAL)
            
            del ctx, attachment
            gc.collect()
            return

    guild = ctx.guild
    pendingChannel = guild.get_channel(config_file[str(ctx.guild_id)]['pendingChannel'])
    rolePing = discord.utils.get(ctx.guild.roles, name='reportPings')

    if link is None and attachment is None: # stop if no evidence included in report
        await ctx.response.send_message('Please provide evidence for your report.', ephemeral=EPHEMERAL)
        
        del ctx
        gc.collect()
        return
    
    await ctx.response.send_message('Processing your report...', ephemeral=EPHEMERAL) # report submitted
    
    embed = discord.Embed(title=f'Player Reported: {name}', 
                          color=0xff8080)
    
    thumbnails = ['https://media.discordapp.net/attachments/1366645416430669857/1402167998910824481/caption.gif?ex=689985b5&is=68983435&hm=936e14918616642fbbcf88828b88f1c9740339fea0bca121a9dc274ba9d39f2c&=&width=750&height=750',
                  'https://media.discordapp.net/attachments/1356789044113051819/1403655176606191636/attachment.png?ex=68990000&is=6897ae80&hm=d2ac218c58e7f0b1839b17155b29e38de00be507ac517d4a80a5b66dba33384b&=&format=webp&quality=lossless&width=750&height=750',
                  'https://media.discordapp.net/attachments/1356789044113051819/1403994323426611280/attachment.png?ex=6899931b&is=6898419b&hm=523edb3b37ac91b08971ffc2661f194ee475548769055e3a1a24bc8cfe4fe4b4&=&format=webp&quality=lossless&width=750&height=750',
                  'https://media.discordapp.net/attachments/1356789044113051819/1403995864866754590/attachment.png?ex=6899948b&is=6898430b&hm=e774536589bb88e48f317e97b5676c77d06f21b0092b2e0cca63445c40a17fd7&=&format=webp&quality=lossless&width=750&height=750',
                  'https://media.discordapp.net/attachments/1279324733313384522/1460207126902472704/attachment.gif?ex=6966bc1c&is=69656a9c&hm=c3da011547e4d538d49fb297f3d6a757b47e51f10558280c88ba187b0cba3a0f&=&format=webp&quality=lossless&width=750&height=750',
                  'https://media.discordapp.net/attachments/1454603190258630877/1458795835730038866/caption.gif?ex=696636fe&is=6964e57e&hm=e2448429503a069594ee20c232dfa1a6981abde0a70aa99a3f798fa33270e422&=&format=webp&quality=lossless&width=750&height=750',
                  'https://media.discordapp.net/attachments/1383249818058489956/1388327413884391444/dvoraps_with_diddy.gif?ex=696645e9&is=6964f469&hm=852828251fd62ae804346d7cb84a162a12aedaaa43cd8011e38e4f8a81b751ed&=&format=webp&quality=lossless&width=750&height=750',
                  'https://media.discordapp.net/attachments/1279324733313384522/1458797257322401894/attachment.gif?ex=69663851&is=6964e6d1&hm=447863ed012e76d2c3590b20c2016c68fef230f1c16c3cbc3d7213a6eb4d0bfe&=&format=webp&quality=lossless&width=750&height=750',
                  'https://media.discordapp.net/attachments/1418045419472289931/1455661632532385833/image.gif?ex=6966ad8a&is=69655c0a&hm=1c3a8ce575dde6f0c9b6f5aacb4f9f407c5b459b43aab4f87b49cd0fc980c27d&=&format=webp&quality=lossless&width=750&height=750',
                  'https://media.discordapp.net/attachments/1279324733313384522/1456927739830472805/attachment.gif?ex=6966ab71&is=696559f1&hm=dafc96ed4ac09f2fb7cab737c47e780467ae5da12f4c38f069487663264a0d46&=&format=webp&quality=lossless&width=750&height=750']    
    
    embed.set_thumbnail(url=random.choice(thumbnails))
    
    embedMessage = f'❯ Reported by: {ctx.user.mention}'
    if link is not None:
        embedMessage += f'\n❯ Link: {link}'
    if description is not None:
        embedMessage += f'\n❯ Description: {description.value}'

    embed.add_field(name='',
                    value=embedMessage,
                    inline=False)
    
    embed.set_footer(text=f'{ctx.user.id}', # redcard png as the footer icon
                    icon_url='https://cdn-icons-png.flaticon.com/32/5524/5524644.png')

    if attachment is not None:
        pendingReport = await pendingChannel.send(f'<@&{rolePing.id}>', embed=embed, file=await attachment.to_file()) # send report to pending channel, depends on if file attached
    else:
        pendingReport = await pendingChannel.send(f'<@&{rolePing.id}>', embed=embed)
    
    reacts = ['✅', '❌', '🛃'] # pending report reactions: accept, deny, blacklist
    for react in reacts:
        await pendingReport.add_reaction(react)

    await ctx.followup.send(content='Report sent.', ephemeral=EPHEMERAL) # notify user report sent

    del ctx, name, link, attachment, embed, pendingReport, thumbnails, reacts # free up memory
    gc.collect()

    return

@report.error
async def report_error(ctx: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await ctx.response.send_message(str(error), ephemeral=EPHEMERAL) # tell user they are on cooldown
    del ctx, error
    gc.collect()

    # -------------------------------- PENDING REPORTS --------------------------------

@bot.event
async def on_raw_reaction_add(ctx: discord.RawReactionActionEvent):
    react = ctx.emoji.name # reaction that was pressed
    channel = bot.get_channel(ctx.channel_id) # channel message reacted in (this fires for ALL reactions. needed for filter)
    message = await channel.fetch_message(ctx.message_id) # message reacted to

    if ctx.channel_id != config_file[str(ctx.guild_id)]['pendingChannel']: # check message being reacted to is in the pending channel 
        return
    
    if ctx.user_id == bot.user.id: # pass over the bot self-reacting during the message creation
        return

    if message.author.id != bot.user.id: # check if message from bot
        return
    
    member = await bot.fetch_user(message.embeds[0].footer.text) # gets user who made report from footer of embed 

    if react == '✅': # accept report
        logsChannel = await bot.fetch_channel(config_file[str(ctx.guild_id)]['logChannel'])
        moderator = await bot.fetch_user(ctx.user_id)

        embedToSend = discord.Embed() # Probably could make this look better but I cba
        embedToSend.title = f'Report Accepted: {message.embeds[0].title[17:]}'
        embedToSend.color = 0x44ff44
        embedToSend.set_thumbnail(url = message.embeds[0].thumbnail.url)
        embedToSend.add_field(name='',
                              value=f'{message.embeds[0].fields[0].value}\n❯ Accepted by: {moderator.mention}',
                              inline=False)
        embedToSend.set_footer(text=message.embeds[0].footer.text,
                               icon_url=message.embeds[0].footer.icon_url)
        
        dmEmbed = discord.Embed(color=0x44ff44)
        dmEmbed.add_field(name='',
                          value=f'Your report on {message.embeds[0].title[17:]} was accepted.',
                          inline=False)

        if len(message.attachments) != 0:
            await logsChannel.send(embed=embedToSend, file=await message.attachments[0].to_file())
        else:
            await logsChannel.send(embed=embedToSend)
            
        try:
            await member.send(embed=dmEmbed)
        except Exception as e:
            print(e)

        await message.delete()

    if react == '❌': # deny report
        logsChannel = await bot.fetch_channel(config_file[str(ctx.guild_id)]['logChannel'])
        moderator = await bot.fetch_user(ctx.user_id)

        embedToSend = discord.Embed()
        embedToSend.title = f'Report Denied: {message.embeds[0].title[17:]}'
        embedToSend.color = 0xff4444
        embedToSend.set_thumbnail(url = message.embeds[0].thumbnail.url)
        embedToSend.add_field(name='',
                              value=f'{message.embeds[0].fields[0].value}\n❯ Denied by: {moderator.mention}',
                              inline=False)
        embedToSend.set_footer(text=message.embeds[0].footer.text,
                               icon_url=message.embeds[0].footer.icon_url)
        
        dmEmbed = discord.Embed(color=0xff4444)
        dmEmbed.add_field(name='',
                          value=f'Your report on {message.embeds[0].title[17:]} was declined.',
                          inline=False)

        if len(message.attachments) != 0:
            await logsChannel.send(embed=embedToSend, file=await message.attachments[0].to_file())
        else:
            await logsChannel.send(embed=embedToSend)

        try:
            await member.send(embed=dmEmbed)
        except Exception as e:
            print(e)

        await message.delete()
    
    if react == '🛃': # blacklist user from making reports
        logsChannel = await bot.fetch_channel(config_file[str(ctx.guild_id)]['logChannel'])
        user = await bot.fetch_user(message.embeds[0].footer.text)
        moderator = await bot.fetch_user(ctx.user_id)
        
        if user.id not in blacklist_file[str(ctx.guild_id)]:
            with open(BLACKLIST_FILE, 'w') as f:
                blacklist_file[str(ctx.guild_id)].append(user.id)
                json.dump(blacklist_file, f, indent=4)

        embedToSend = discord.Embed()
        embedToSend.title = f'Blacklisted'
        embedToSend.color = 0x3abade
        embedToSend.set_thumbnail(url = message.embeds[0].thumbnail.url)
        embedToSend.add_field(name='',
                              value=f'❯ User blacklisted: {user.mention}\n❯ Blacklisted by: {moderator.mention}',
                              inline=False)
        embedToSend.set_footer(text=message.embeds[0].footer.text,
                               icon_url=message.embeds[0].footer.icon_url)
        
        dmEmbed = discord.Embed(color=0x3abade)
        dmEmbed.add_field(name='',
                          value=f'You have been blacklisted from making reports.',
                          inline=False)

        await logsChannel.send(embed=embedToSend)

        try:
            await member.send(embed=dmEmbed)
        except Exception as e:
            print(e)
        await message.delete()

    if str(ctx.member.id) not in modstats_file[str(ctx.guild_id)]:
        modstats_file[str(ctx.guild_id)][str(ctx.member.id)] = 0
    modstats_file[str(ctx.guild_id)][str(ctx.member.id)] += 1

    try:
        with open(MODSTATS_FILE, 'w') as f: # update modstats json
            json.dump(modstats_file, f, indent=4)
    except Exception as e:
        print(e)
    
    del embedToSend, message, ctx, channel, react
    gc.collect()
    return

    # -------------------------------- USER BLACKLIST --------------------------------

@bot.tree.command(name='blacklist', description='Blacklist user', guild=GUILD_ID)
@app_commands.describe(
    user='User to blacklist.'
)
async def blacklist(ctx:discord.Interaction, user: discord.Member):
    print(f'Blacklist called from {ctx.guild.id}')
    if not ctx.user.guild_permissions.kick_members: # only mods can run this
        await ctx.response.send_message('No perms twuzzo', ephemeral=EPHEMERAL)

        del ctx
        gc.collect()
        return

    if user.id not in blacklist_file:
        blacklist_file[str(ctx.guild_id)].append(user.id)
        with open(BLACKLIST_FILE, 'w') as f: # write to blacklist json
            json.dump(blacklist_file, f, indent=4)
        await ctx.response.send_message(f'{user.mention} has been blacklisted.', ephemeral=EPHEMERAL)
    else:
        await ctx.response.send_message(f'{user.mention} is already blacklisted.', ephemeral=EPHEMERAL)

    del ctx
    gc.collect() 
    return

@bot.tree.command(name='unblacklist', description='Unblacklist user', guild=GUILD_ID)
@app_commands.describe(
    user='User to unblacklist.'
)
async def unblacklist(ctx:discord.Interaction, user: discord.Member):
    print(f'Unblacklist called from {ctx.guild.id}')
    if not ctx.user.guild_permissions.kick_members: # only mods can run this
        await ctx.response.send_message('No perms twuzzo', ephemeral=EPHEMERAL)
        
        del ctx
        gc.collect()
        return

    if user.id in blacklist_file[str(ctx.guild_id)]:
        blacklist_file[str(ctx.guild_id)].remove(user.id)
        with open(BLACKLIST_FILE, 'w') as f: # write to blacklist json
            json.dump(blacklist_file, f, indent=4)
        await ctx.response.send_message(f'{user.mention} has been unblacklisted.', ephemeral=EPHEMERAL)
    else:
        await ctx.response.send_message(f'{user.mention} is not blacklisted.', ephemeral=EPHEMERAL)

    del ctx
    gc.collect()
    return

    # -------------------------------- CONFIG --------------------------------

@bot.tree.command(name='config', description='Configure channel IDs', guild=GUILD_ID)
@app_commands.describe(
    pendingchannel='Set Pending Channel',
    logchannel='Set Log Channel',
    maxfilesize='Set Max File Size (MB)',
    cooldown='Set Report Command Cooldown (Seconds)',
    ratelimit='Set how many reports can be sent before cooldown'
)
async def config(ctx: discord.Interaction, pendingchannel: Optional[discord.TextChannel] = None, logchannel: Optional[discord.TextChannel] = None, maxfilesize: Optional[int] = None, cooldown: Optional[int] = None, ratelimit: Optional[int] = None):
    print(f'Config called from {ctx.guild.id}')
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message('No perms twuzzo', ephemeral=EPHEMERAL)
        
        del ctx
        gc.collect()
        return
    
    if not discord.utils.get(ctx.guild.roles, name='reportPings'):
        await ctx.guild.create_role(reason='Config', name='reportPings')
    
    if str(ctx.guild_id) not in config_file:
        config_file[str(ctx.guild_id)] = {'pendingChannel': None, 
                                          'logChannel': None, 
                                          'maxFileSize': 0, 
                                          'cooldown': 0, 
                                          'rateLimit': 0}
    if str(ctx.guild.id) not in blacklist_file:
        blacklist_file[str(ctx.guild.id)] = []
    if str(ctx.guild.id) not in modstats_file:
        modstats_file[str(ctx.guild.id)] = {}


    try:
        with open(CONFIG_FILE, 'w') as f: # write to config json
            config_file[str(ctx.guild_id)]['pendingChannel'] =  config_file[str(ctx.guild_id)]['pendingChannel']    if pendingchannel is None else pendingchannel.id
            config_file[str(ctx.guild_id)]['logChannel'] =      config_file[str(ctx.guild_id)]['logChannel']        if logchannel is None else logchannel.id
            config_file[str(ctx.guild_id)]['maxFileSize'] =     config_file[str(ctx.guild_id)]['maxFileSize']       if maxfilesize is None else maxfilesize
            config_file[str(ctx.guild_id)]['cooldown'] =        config_file[str(ctx.guild_id)]['cooldown']          if cooldown is None else cooldown
            config_file[str(ctx.guild_id)]['rateLimit'] =       config_file[str(ctx.guild_id)]['rateLimit']         if ratelimit is None else ratelimit
            json.dump(config_file, f, indent=4)
    except FileNotFoundError as e:
        print(f'Unfuck this bruh: {e}')
        return
    
    try:
        with open(BLACKLIST_FILE, 'w') as f:
            json.dump(blacklist_file, f, indent=4)
    except FileNotFoundError as e:
        print(f'Unfuck this bruh: {e}')

    try:
        with open(MODSTATS_FILE, 'w') as f:
            json.dump(modstats_file, f, indent=4)
    except FileNotFoundError as e:
        print(f'Unfuck this bruh: {e}')
            
    await ctx.response.send_message('Configured.', ephemeral=EPHEMERAL)

    del ctx
    gc.collect()
    return

@bot.tree.command(name='viewconfig', description='View what channels are being used by RedCard', guild=GUILD_ID)
async def viewconfig(ctx: discord.Interaction):
    print(f'Viewconfig called from {ctx.guild.id}')
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message('No perms twuzzo', ephemeral=EPHEMERAL)
        
        del ctx
        gc.collect()
        return
    
    if str(ctx.guild.id) not in config_file:
        await ctx.response.send_message('Set up /config', ephemeral=EPHEMERAL)

        del ctx
        gc.collect()
        return
    
    guild = ctx.guild
    pendingChannel =    guild.get_channel(config_file[str(ctx.guild_id)]['pendingChannel']).jump_url    if guild.get_channel(config_file[str(ctx.guild_id)]['pendingChannel']) is not None else None # check if valid
    logChannel =        guild.get_channel(config_file[str(ctx.guild_id)]['logChannel']).jump_url        if guild.get_channel(config_file[str(ctx.guild_id)]['logChannel']) is not None else None # check if valid
    maxFileSize =       config_file[str(ctx.guild_id)]['maxFileSize']
    cooldown =          config_file[str(ctx.guild_id)]['cooldown']
    rateLimit =         config_file[str(ctx.guild_id)]['rateLimit']

    try:
        embed = discord.Embed()
        embed.add_field(name='',
                        value=f'Pending channel: {pendingChannel}\nLog channel: {logChannel}\nMax file size: {maxFileSize}MB\nCooldown: {cooldown} seconds\nRate Limit: {rateLimit}',
                        inline = False)
        await ctx.response.send_message(embed=embed, ephemeral=EPHEMERAL)
    except Exception as e:
        await ctx.response.send_message(e, ephemeral=EPHEMERAL)

    del ctx
    gc.collect()
    return

    # --------------------------------- STAFF PINGS ---------------------------------

@bot.tree.command(name='active', description='Toggle report pings', guild=GUILD_ID)
async def active(ctx: discord.Interaction):
    print(f'Active called from {ctx.guild.id}')
    if not ctx.user.guild_permissions.kick_members:
        await ctx.response.send_message('No perms twuzzo', ephemeral=EPHEMERAL)
        return

    role = discord.utils.get(ctx.guild.roles, name='reportPings')

    if not role:
        await ctx.response.send_message('reportPings role doesnt exist', ephemeral=EPHEMERAL)
        return
    
    if role in ctx.user.roles:
        await ctx.user.remove_roles(role)
        await ctx.response.send_message('Marked offline.', ephemeral=EPHEMERAL)
    else:
        await ctx.user.add_roles(role)
        await ctx.response.send_message('Marked online.', ephemeral=EPHEMERAL)

    return

    # --------------------------------- MOD STATS ---------------------------------

@bot.tree.command(name='modstats', description='Get completed reports of staff', guild=GUILD_ID)
@app_commands.describe(
    staff='staff id'
)
async def modstats(ctx: discord.Interaction, staff: Optional[discord.Member] = None):
    print(f'Modstats called from {ctx.guild.id}')
    if staff is None:
        staff = ctx.user

    if str(staff.id) in modstats_file[str(ctx.guild_id)]:
        await ctx.response.send_message(f'{staff} has {modstats_file[str(ctx.guild_id)][str(staff.id)]} moderations', ephemeral=EPHEMERAL)
    else:
        await ctx.response.send_message(f'{staff} has no moderations', ephemeral=EPHEMERAL)

    return


@bot.tree.command(name='setmodstats', description='Set completed reports of staff', guild=GUILD_ID)
@app_commands.describe(
    staff='staff id',
    numlogs='number of logs'
)
async def setmodstats(ctx: discord.Interaction, staff: discord.Member, numlogs: int):
    print(f'Setmodstats called from {ctx.guild.id}')
    modstats_file[str(ctx.guild_id)][str(staff.id)] = numlogs

    await ctx.response.send_message(f'{staff} modstats set to {numlogs}', ephemeral=EPHEMERAL)

    try:
        with open(MODSTATS_FILE, 'w') as f:
            json.dump(modstats_file, f, indent=4)
    except Exception as e:
        print(e)

    return

@bot.tree.command(name='listmodstats', description='List all user modstats in descending order', guild=GUILD_ID)
async def listmodstats(ctx: discord.Interaction):
    print(f'Listmodstats called from {ctx.guild.id}')
    sortedModstats = sorted(modstats_file[str(ctx.guild_id)].items(), key=lambda item: item[1], reverse=True)
    
    modstatsString = ''.join(f'<@{k}>: {v}\n' for k, v in sortedModstats)
    embed = discord.Embed()
    embed.add_field(name='Modstats list',
                    value=modstatsString,
                    inline=False)
    
    await ctx.response.send_message(embed=embed)
    
    return

    # --------------------------------- OVERWRITE ---------------------------------

@bot.tree.command(name='overwrite', description='Overwrite a report', guild=GUILD_ID)
@app_commands.describe(
    reportid='message ID'
)
async def overwrite(ctx: discord.Interaction, reportid: str):
    print(f'Overwrite called from {ctx.guild.id}')
    try:
        reportidAsInt = int(reportid)
        channel = bot.get_channel(config_file[str(ctx.guild_id)]['logChannel'])
        message = await channel.fetch_message(reportidAsInt)

        if message.author.id != bot.user.id:
            await ctx.response.send_message('Nice try idiot', ephemeral=EPHEMERAL)
            return

        embed = message.embeds[0]

        newEmbed = discord.Embed()
        newEmbed.set_thumbnail(url=embed.thumbnail.url)
        newEmbed.set_footer(text=embed.footer.text)


        if embed.color.value == 0xff4444:
            newEmbed.color = 0x44ff44
            newEmbed.title = embed.title.replace('Denied', 'Accepted', 1)
            newEmbed.add_field(name='',
                               value=embed.fields[0].value + f'\n❯ Overwritten by: {ctx.user.mention}',
                               inline=False)
        
        elif embed.color.value == 0x44ff44:
            newEmbed.color = 0xff4444
            newEmbed.title = embed.title.replace('Accepted', 'Denied', 1)
            newEmbed.add_field(name='',
                               value=embed.fields[0].value + f'\n❯ Overwritten by: {ctx.user.mention}',
                               inline=False)
            
        elif embed.color.value == 0x3abade:
            await ctx.response.send_message(f'Do /unblacklist. I\'m not coding this shit.', ephemeral=EPHEMERAL)
            return
        
        else:
            await ctx.response.send_message(f'Uhh something broke screenshot this and send to FreakyFentFold. \n{reportid}')
            return

        try:
            file = await message.attachments[0].to_file()
            await ctx.response.send_message(embed=newEmbed, file=file) 
        except:
            await ctx.response.send_message(embed=newEmbed)

        await message.delete()

    except discord.errors.NotFound:
        await ctx.response.send_message(f'Report not found', ephemeral=EPHEMERAL)
    except Exception as e:
        await ctx.response.send_message(e, ephemeral=EPHEMERAL)
        print(e)

    await ctx.response.send_message(f'{reportid} overwritten.')
    return

# --------------------------------- BOT SETUP ---------------------------------

@bot.event
async def on_ready():
    print('primed and ready')

    try:
        guild = GUILD_ID
        synced = await bot.tree.sync(guild=guild)
        print(f'synced {len(synced)} commands to {guild.id}')
        await bot.change_presence(activity=discord.Game(name='/report'))

    except Exception as e:
        print(f'Shit broke: {e}')

@bot.event
async def on_guild_join(guild: discord.Guild):
    if str(guild.id) not in config_file:
        config_file[str(guild.id)] = {
            'pendingChannel': None,
            'logChannel': None,
            'maxFileSize': 0,
            'cooldown': 0,
            'rateLimit': 1
        }
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_file, f, indent=4)
    except FileNotFoundError as e:
        print(f'Unfuck this shit bruh: {e}')

bot.run(token, log_handler=handler, log_level=logging.DEBUG)