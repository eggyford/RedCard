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
EPHEMERAL = True # Set this false if u wanna debug easier
BLACKLIST_FILE = 'blacklist.json'
CONFIG_FILE = 'config.json'

try:
    with open(BLACKLIST_FILE, 'r') as f:
        blacklisted_users = json.load(f)
except FileNotFoundError:
    blacklisted_users = []

try: 
    with open(CONFIG_FILE, 'r') as f:
        config_file = json.load(f)
except FileNotFoundError:
    print('set up /config')
    config_file = []

GUILD_ID = discord.Object(id=guild)
PENDING_CHANNEL_ID = config_file[0]
LOGS_CHANNEL_ID = config_file[1]
MAX_FILE_SIZE = config_file[2]
COMMAND_COOLDOWN = config_file[3]
COMMAND_RATE_LIMIT = config_file[4]
for config in config_file:
    print(config)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='$', intents=intents)

# -------------------------------- BOT FUNCTION -------------------------------

    # -------------------------------- REPORT --------------------------------

@bot.tree.command(name='report', description='report someone', guild=GUILD_ID)
@app_commands.describe(
    name='Roblox username.',
    link='Link video evidence.',
    attachment='Attach video evidence.'
)
@app_commands.checks.cooldown(COMMAND_RATE_LIMIT, COMMAND_COOLDOWN, key=lambda i: i.user.id)
async def report(ctx: discord.Interaction, name: str, link: Optional[str] = None, attachment: Optional[discord.Attachment] = None):
    if ctx.user.id in blacklisted_users:
        await ctx.response.send_message('You have been blacklisted from making reports.', ephemeral=EPHEMERAL)
        
        del ctx
        gc.collect()
        return
        
    if attachment is not None:
        attachmentSizeMB = attachment.size / 1024 / 1024
        if attachmentSizeMB >= MAX_FILE_SIZE:
            await ctx.response.send_message(content=f'File size limit is {MAX_FILE_SIZE}MB.\nTry uploading to https://www.youtu.be and sending the link instead.', ephemeral=EPHEMERAL)
            
            del ctx, attachment
            gc.collect()
            return

    guild = ctx.guild
    pendingChannel = guild.get_channel(PENDING_CHANNEL_ID)

    if link is None and attachment is None:
        await ctx.response.send_message('Please provide evidence for your report.', ephemeral=EPHEMERAL)
        
        del ctx
        gc.collect()
        return
    
    await ctx.response.send_message('Processing your report...', ephemeral=EPHEMERAL)
    
    embed = discord.Embed(title=f'Player Reported: {name}', 
                          color=0xff8080)
    
    thumbnails = ['https://media.discordapp.net/attachments/1366645416430669857/1402167998910824481/caption.gif?ex=689985b5&is=68983435&hm=936e14918616642fbbcf88828b88f1c9740339fea0bca121a9dc274ba9d39f2c&=&width=750&height=750',
                  'https://media.discordapp.net/attachments/1356789044113051819/1403655176606191636/attachment.png?ex=68990000&is=6897ae80&hm=d2ac218c58e7f0b1839b17155b29e38de00be507ac517d4a80a5b66dba33384b&=&format=webp&quality=lossless&width=750&height=750',
                  'https://media.discordapp.net/attachments/1356789044113051819/1403994323426611280/attachment.png?ex=6899931b&is=6898419b&hm=523edb3b37ac91b08971ffc2661f194ee475548769055e3a1a24bc8cfe4fe4b4&=&format=webp&quality=lossless&width=750&height=750',
                  'https://media.discordapp.net/attachments/1356789044113051819/1403995864866754590/attachment.png?ex=6899948b&is=6898430b&hm=e774536589bb88e48f317e97b5676c77d06f21b0092b2e0cca63445c40a17fd7&=&format=webp&quality=lossless&width=750&height=750']
    
    embed.set_thumbnail(url=thumbnails[random.randint(0,len(thumbnails)-1)])

    if link is not None:
        embed.add_field(name='',
                        value=f'❯ Reported by: {ctx.user.mention}\n❯ {link}',
                        inline=False)
    else:
        embed.add_field(name='',
                        value=f'❯ Reported by: {ctx.user.mention}',
                        inline=False)
    
    embed.set_footer(text=f'{ctx.user.id}',
                    icon_url="https://cdn-icons-png.flaticon.com/32/5524/5524644.png")

    reacts = ['✅', '❌', '🛃']
    if attachment is not None:
        pendingReport = await pendingChannel.send(embed=embed, file=await attachment.to_file())
    else:
        pendingReport = await pendingChannel.send(embed=embed)
    
    for react in reacts:
        await pendingReport.add_reaction(react)

    await ctx.followup.send(content='Report sent.', ephemeral=EPHEMERAL)

    del ctx, name, link, attachment, embed, pendingReport, thumbnails, reacts
    gc.collect()

    return

@report.error
async def report_error(ctx: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await ctx.response.send_message(str(error), ephemeral=EPHEMERAL)
    del ctx, error
    gc.collect()

    # -------------------------------- PENDING REPORTS --------------------------------

@bot.event
async def on_raw_reaction_add(ctx: discord.RawReactionActionEvent):
    react = ctx.emoji.name
    channel = bot.get_channel(ctx.channel_id)
    message = await channel.fetch_message(ctx.message_id)
    member = await bot.fetch_user(message.embeds[0].footer.text)
    guild = bot.get_guild(GUILD_ID)

    if ctx.channel_id != PENDING_CHANNEL_ID:
        return
    
    if ctx.user_id == bot.user.id:
        return

    if message.author.id != bot.user.id:
        return

    if react == '✅':
        logsChannel = await bot.fetch_channel(LOGS_CHANNEL_ID)
        moderator = await bot.fetch_user(ctx.user_id)

        embedToSend = discord.Embed()
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

    if react == '❌':        
        logsChannel = await bot.fetch_channel(LOGS_CHANNEL_ID)
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
    
    if react == '🛃':
        logsChannel = await bot.fetch_channel(LOGS_CHANNEL_ID)
        user = await bot.fetch_user(message.embeds[0].footer.text)
        moderator = await bot.fetch_user(ctx.user_id)
        
        if user.id not in blacklisted_users:
            with open(BLACKLIST_FILE, 'w') as f:
                blacklisted_users.append(user.id)
                json.dump(blacklisted_users, f)

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

    del embedToSend, message, ctx, channel, react, guild
    gc.collect()
    return

    # -------------------------------- USER BLACKLIST --------------------------------

@bot.tree.command(name='blacklist', description='Blacklist user', guild=GUILD_ID)
@app_commands.describe(
    user='User to blacklist.'
)
async def blacklist(ctx:discord.Interaction, user: discord.Member):
    if not ctx.user.guild_permissions.kick_members:
        await ctx.response.send_message('No perms twuzzo', ephemeral=EPHEMERAL)

        del ctx
        gc.collect()
        return

    if user.id not in blacklisted_users:
        blacklisted_users.append(user.id)
        with open(BLACKLIST_FILE, 'w') as f:
            json.dump(blacklisted_users, f)
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
    if not ctx.user.guild_permissions.kick_members:
        await ctx.response.send_message('No perms twuzzo', ephemeral=EPHEMERAL)
        
        del ctx
        gc.collect()
        return

    if user.id in blacklisted_users:
        blacklisted_users.remove(user.id)
        with open(BLACKLIST_FILE, 'w') as f:
            json.dump(blacklisted_users, f)
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
    logschannel='Set Logs Channel',
    maxfilesize='Set Max File Size (MB)',
    cooldown='Set Report Command Cooldown (Seconds)',
    ratelimit='Set how many reports can be sent before cooldown'
)
async def config(ctx: discord.Interaction, pendingchannel: Optional[discord.TextChannel] = None, logschannel: Optional[discord.TextChannel] = None, maxfilesize: Optional[int] = None, cooldown: Optional[int] = None, ratelimit: Optional[int] = None):
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message('No perms twuzzo', ephemeral=EPHEMERAL)
        
        del ctx
        gc.collect()
        return
    
    if pendingchannel is not None:
        global PENDING_CHANNEL_ID
        PENDING_CHANNEL_ID = pendingchannel.id

        try:
            with open(CONFIG_FILE, 'w') as f:
                config_file[0] = pendingchannel.id
                json.dump(config_file, f)
        except FileNotFoundError as e:
            print(f'Unfuck this bruh: {e}')
            return

    if logschannel is not None:
        global LOGS_CHANNEL_ID
        LOGS_CHANNEL_ID = logschannel.id

        try:
            with open(CONFIG_FILE, 'w') as f:
                config_file[1] = logschannel.id
                json.dump(config_file, f)
        except FileNotFoundError as e:
            print(f'Unfuck this bruh: {e}')
            return
        
    if maxfilesize is not None:
        global MAX_FILE_SIZE
        MAX_FILE_SIZE = maxfilesize

        try:
            with open(CONFIG_FILE, 'w') as f:
                config_file[2] = maxfilesize
                json.dump(config_file, f)
        except FileNotFoundError as e:
            print(f'Unfuck this bruh: {e}')
            return
    
    if cooldown is not None:
        global COMMAND_COOLDOWN
        COMMAND_COOLDOWN = cooldown

        try:
            with open(CONFIG_FILE, 'w') as f:
                config_file[3] = cooldown
                json.dump(config_file, f)
        except FileNotFoundError as e:
            print(f'Unfuck this bruh: {e}')
            return
        
    if ratelimit is not None:
        global COMMAND_RATE_LIMIT
        COMMAND_RATE_LIMIT = ratelimit

        try:
            with open(CONFIG_FILE, 'w') as f:
                config_file[4] = ratelimit
                json.dump(config_file, f)
        except FileNotFoundError as e:
            print(f'Unfuck this bruh: {e}')
            return
    await ctx.response.send_message('Configured.', ephemeral=EPHEMERAL)

    del ctx
    gc.collect()
    return

@bot.tree.command(name='viewconfig', description='View what channels are being used by RedCard', guild=GUILD_ID)
async def viewconfig(ctx: discord.Interaction):
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message('No perms twuzzo', ephemeral=EPHEMERAL)
        
        del ctx
        gc.collect()
        return
    
    guild = ctx.guild
    try:
        embed = discord.Embed()
        embed.add_field(name='',
                        value=f'Pending channel: {guild.get_channel(PENDING_CHANNEL_ID).jump_url}\nLog channel: {guild.get_channel(LOGS_CHANNEL_ID).jump_url}\nMax file size: {MAX_FILE_SIZE}MB\nCooldown: {COMMAND_COOLDOWN} seconds\nRate Limit: {COMMAND_RATE_LIMIT}',
                        inline = False)
        await ctx.response.send_message(embed=embed, ephemeral=EPHEMERAL)
    except Exception as e:
        await ctx.response.send_message(e, ephemeral=EPHEMERAL)

    del ctx
    gc.collect()
    return

# --------------------------------- BOT SETUP ---------------------------------

@bot.event
async def on_ready():
    print('primed and ready')

    try:
        guild = GUILD_ID
        synced = await bot.tree.sync(guild=guild)
        print(f'synced {len(synced)} commands to {guild.id}')

    except Exception as e:
        print(f'Shit broke: {e}')

bot.run(token, log_handler=handler, log_level=logging.DEBUG)