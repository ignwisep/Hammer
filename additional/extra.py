import discord
import re
import asyncio
import json
import time as t
import aiohttp, requests
from deep_translator import GoogleTranslator
from langdetect import detect
import datetime
import pytz
import aiohttp
import discord
from discord import ActivityType
import os,hashlib,sys
from pystyle import Center, Colorate, Colors
from main import send, senderror,config
from discord.ext import commands, tasks
# verify()
tasks_dict = {}

class extra(commands.Cog):
    def __init__(self, bot):
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)        
        self.bot = bot
        self.file_path = "database/automessages.json"        
        self.tasks = {} 
        self.url = "https://discord.com/api/v9/users/@me/settings"
        self.statuses = []
        self.presence = ['idle', 'dnd', 'invisible', 'online']
        self.change_status_task = None
        self.change_presence_task = None
        self.am_tasks_dict = {}
        self.token = self.load_token()
        self.config_file_path = "config.json"
        self.config = self.load_config(self.config_file_path)
        self.time_zone = self.config.get("time_zone")
        self.ping_scan = config.get("ping_scan", False) 
        # self.start_all_tasks()         
        self.afk_users = {}         

    @commands.Cog.listener()
    async def on_message(self, message):
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)        
        color = int(config.get("embed_colour").lstrip("#"), 16)
        embed_webhook_url = config.get("embed_mode_webhook_url")            
        self.time_zone = self.config.get("time_zone")
        self.ping_scan = config.get("ping_scan", False)
        self.webhook_url = config.get("ping_scan_webhook_url", None)         
        if message.author.bot or message.author == self.bot.user:
            return

        if self.bot.user in message.mentions:
            for user in message.mentions:
                if user.id in self.afk_users and user.id != message.author.id:
                    afk_message = self.afk_users.get(user.id, {}).get('message', 'No reason provided.')
                    content = f"{user.display_name} is AFK\n<a:SPY_STORE:1329411121832267806> **Reason: {afk_message}**"
                    try:
                        webhook = discord.Webhook.from_url(embed_webhook_url, client=self.bot)
                        embed = discord.Embed(description=content, color=discord.Color(color))            
                        webhook_message = await webhook.send(embed=embed, wait=True)
                        msg = await webhook_message.forward(message.channel)
                        await webhook_message.delete()
                        await msg.delete(delay=30)
                    except discord.Forbidden:
                        await message.channel.send(content, delete_after=30)
                        try:
                            await webhook_message.delete()
                        except Exception:
                            pass
            if self.ping_scan:
                channel_type = (
                    "DM" if isinstance(message.channel, discord.DMChannel)
                    else "Text Channel" if isinstance(message.channel, discord.TextChannel)
                    else "Group Chat"
                )
                server_name = message.guild.name if message.guild else "None"
                message_link = f"[Click here to view the message]({message.jump_url})"
                tz = pytz.timezone(self.time_zone)
                time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

                embed = discord.Embed(
                    title=f"{self.bot.user.name} Got Pinged <a:SPY_STORE:1330831246162399332>",
                    color=0x00ffcc
                )
                embed.add_field(name="Time", value=time, inline=False)
                embed.add_field(name="From", value=f"{message.author.name} | {message.author.id}", inline=False)
                embed.add_field(name="Server Name", value=server_name, inline=False)
                embed.add_field(name="Channel Type", value=channel_type, inline=False)
                embed.add_field(name="Message Link", value=message_link, inline=False)
                embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else "https://cdn.discordapp.com/attachments/1295434516134891541/1335560956885073920/9332-default-discord-pfp.png?ex=67a09d91&is=679f4c11&hm=c6dce188d6d92cde7d29d91217a59590f50990e91e4ed6cc0c63b89252403d9a&")
                if self.webhook_url:
                    try:
                        webhook = discord.Webhook.from_url(self.webhook_url, client=self.bot)
                        await webhook.send(f"{self.bot.user.mention}", embed=embed)
                    except Exception as e:
                        print(f"Failed to send webhook: {e}")
                else:
                    print("Webhook URL is not defined.")

    def load_config(self, config_file_path):
        with open(config_file_path, 'r') as config_file:
            config = json.load(config_file)
        return config

    def load_token(self):
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        return config.get("token")

    @commands.command()
    async def user(self, ctx):
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")
        description = (
            f"<a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253>\n"
            f"<:SPY_STORE:1329255509735378985> **`[REQUIRED] | <OPTIONAL>`** <a:SPY_STORE:1329357365031731221>\n"
            f"<a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253>\n"    
            f"<:SPY_STORE:1329365754222608466> | **Set AFK** **:** **`{prefix}afk [reason]`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Remove AFK** **:** **`{prefix}unafk`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Change Hypesquad** **:** **`{prefix}hypesquad`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Show 1st Msg** **:** **`{prefix}firstm`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Start Auto Msgs** **:** **`{prefix}amstart [chnl_id] [time in s] [msg]`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Stop Auto Msgs** **:** **`{prefix}amstop [channel_id|all]`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Show Auto Msgs List** **:** **`{prefix}amlist`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Add Trigger** **:** **`{prefix}trigger+ [trigger] [response]`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Remove Trigger** **:** **`{prefix}trigger- [trigger]`**\n"
            f"<:SPY_STORE:1329365754222608466> | **List Triggers** **:** **`{prefix}triggerlist`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Add React** **:** **`{prefix}areact+ [trigger] [emoji]`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Remove React** **:** **`{prefix}areact- [trigger]`**\n"
            f"<:SPY_STORE:1329365754222608466> | **List Reacts** **:** **`{prefix}areactlist`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Solve Math** **:** **`{prefix}math [equation]`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Set Timer** **:** **`{prefix}timer [time]`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Define Word** **:** **`{prefix}define [word]`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Translate** **:** **`{prefix}translate [text]`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Leave all servers** **:** **`{prefix}leaveall`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Close dm** **:** **`{prefix}closedm`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Close all dms** **:** **`{prefix}closedms`**\n"
            f"<:SPY_STORE:1329365754222608466> | **Show discord ID** **:** **`{prefix}showid [object]`**\n"
            f"<a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253>"
        )
        await send(ctx, "<:SPY_STORE:1329152544055754794>__User Commands__<a:SPY_STORE:1329152680492535808>", description)

    @commands.command(aliases=['id'])
    async def showid(self, ctx, object: str):
        if object.startswith("<#") and object.endswith(">"):
            # Channel mention
            channel_id = object[2:-1]
            await send(ctx,f"Discord ID:",f"**Channel:** <#{channel_id}>\n**Channel ID:** {channel_id}")
            await ctx.send(channel_id)
        elif object.startswith("<@") and object.endswith(">"):
            # User mention
            user_id = object[2:-1]
            await send(ctx,f"Discord ID:",f"**User:** <@{user_id}>\n**User ID:** {user_id}")
            await ctx.send(user_id)
        else:
            await ctx.send("<a:SPY_STORE:1329411121832267806> Please mention a valid channel or user.",delete_after=30)

    @commands.command()
    async def leaveall(self, ctx):
        for guild in self.bot.guilds:
            if guild != ctx.guild:
                try:
                    await guild.leave() 
                except:
                    pass

    @commands.command(aliases=['closeall'])
    async def closedms(self, ctx):
        try:
            for channel in self.bot.private_channels:
                if isinstance(channel, discord.DMChannel):
                    await channel.close()
        except discord.Forbidden:
            pass

    @commands.command()
    async def closedm(self, ctx):    
        if isinstance(ctx, discord.DMChannel):
            try:
                await ctx.channel.close()                   
            except:
                pass

    @commands.command(name='hypesquad', aliases=['changehypesquad'])
    async def change_hypesquad(self, ctx):
        choices = {
            1: "bravery",
            2: "brilliance",
            3: "balanced"
        }

        await send(ctx, "Hypesquads", "`[1]` **bravery**\n`[2]` **brilliance**\n`[3]` **balanced**\n\n-# enter your choice: `1, 2, 3`", "30")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30)
            choice = int(msg.content)
        except asyncio.TimeoutError:
            await senderror(ctx, "Timeout", "You took too long to respond; command timed out")
            return
        except ValueError:
            await senderror(ctx, "Hypesquad", "Invalid choice, please enter: `1, 2, 3`")
            return

        headers = {
            'Authorization': self.config.get('token')
        }

        payload = {
            'house_id': choice
        }

        try:
            await send(ctx, "Hypesquad", f"<a:SPY_STORE:1329411121832267806> Changing hypesquad to {choices.get(choice, 'unknown')}", "5")
            response = requests.post(
                "https://discord.com/api/v9/hypesquad/online",
                json=payload,
                headers=headers
            )

            if response.status_code == 204:
                await send(ctx, "Hypesquad", f"<a:SPY_STORE:1329411121832267806> Hypesquad changed successfully to {choices.get(choice, 'your choice')}", "20")
            elif response.status_code == 401:
                await senderror(ctx, "Hypesquad", "Token invalid or expired")
            elif response.status_code == 429:
                await senderror(ctx, "Hypesquad", "Please wait for 2 minutes")
            else:
                await senderror(ctx, "Error", "An unknown error occurred")
        except requests.exceptions.RequestException as e:
            await senderror(ctx, "Error", f"`-` An error occurred: `{str(e)}`")


    async def close(self):
        await self.bot.http_session.close()

    @commands.command()
    async def afk(self, ctx, *, message: str = "No reason provided"):
        await ctx.message.delete()
        self.afk_users[ctx.author.id] = {'time': datetime.datetime.utcnow(), 'message': message}
        await send(ctx, "Afk set!", f"<a:SPY_STORE:1329411121832267806> I have marked you as AFK in all servers, with reason: `{message}`\n","10")

    @commands.command(name='unafk')
    async def removeafk(self, ctx):
        await ctx.message.delete()
        if ctx.author.id in self.afk_users:
            del self.afk_users[ctx.author.id]
            await send(ctx, "AFK Removed", "<a:SPY_STORE:1329411121832267806> Welcome back, I successfully removed your AFK.","10")
        else:
            await senderror(ctx, "Error", "You are not AFK.")

    @commands.command(name='areact+', aliases=['areactadd'])
    async def autoreactadd(self, ctx, trigger_word: str, *emojis: str):
        await ctx.message.delete()
        try:
            with open('database/autoreactions.json', 'r', encoding='utf-8') as f:
                reactions = json.load(f)
        except FileNotFoundError:
            reactions = {}

        trigger_word = trigger_word.lower()
        emoji_list = " ".join(emojis)

        if trigger_word in reactions:
            current_emojis = reactions[trigger_word].split()
            current_emojis.extend(emoji for emoji in emojis if emoji not in current_emojis)
            reactions[trigger_word] = " ".join(current_emojis)
        else:
            reactions[trigger_word] = emoji_list

        with open('database/autoreactions.json', 'w', encoding='utf-8') as f:
            json.dump(reactions, f, ensure_ascii=False, indent=4)
        await send(ctx, "Auto-react added", f"<a:SPY_STORE:1329411121832267806> **Auto-react `{trigger_word}` added with emojis: {emoji_list}.**", "30")

    @commands.command(name='areact-', aliases=['areactremove', 'areactrem'])
    async def autoreactremove(self, ctx, trigger_word: str, *emojis: str):
        await ctx.message.delete()
        try:
            with open('database/autoreactions.json', 'r', encoding='utf-8') as f:
                reactions = json.load(f)
        except FileNotFoundError:
            reactions = {}
        trigger_word = trigger_word.lower()
        if trigger_word in reactions:
            if emojis:
                current_emojis = reactions[trigger_word].split()
                updated_emojis = [emoji for emoji in current_emojis if emoji not in emojis]
                if updated_emojis:
                    reactions[trigger_word] = " ".join(updated_emojis)
                else:
                    del reactions[trigger_word]
            else:
                del reactions[trigger_word]

            with open('database/autoreactions.json', 'w', encoding='utf-8') as f:
                json.dump(reactions, f, ensure_ascii=False, indent=4)

            removed_emojis = " ".join(emojis) if emojis else "all emojis"
            await send(ctx, "Auto-react removed", f"<a:SPY_STORE:1329411121832267806> **Auto-react trigger with word `{trigger_word}` has been removed**.", "30")
        else:
            await send(ctx, "Error", f"**No auto-reaction found for `{trigger_word}`.**", "30")

    @commands.command(name='areactlist')
    async def autoreactlist(self, ctx):
        await ctx.message.delete()
        try:
            with open('database/autoreactions.json', 'r', encoding='utf-8') as f:
                reactions = json.load(f)
        except FileNotFoundError:
            reactions = {}

        if reactions:
            response_content = "**Here is the list of auto-react triggers**\n\n"
            for trigger_word, emojis in reactions.items():
                response_content += f"**`{trigger_word}` :** {emojis}\n"
        else:
            response_content = "No auto-reactions found."

        await send(ctx, "Auto-react List", response_content, "30")

    @commands.command()
    async def firstm(self,ctx):
        await ctx.message.delete()
        if isinstance(ctx.channel, discord.DMChannel):
            channel = ctx.channel
            message_link = f"https://discord.com/channels/@me/{channel.id}/MESSAGE_ID"
        elif isinstance(ctx.channel, discord.TextChannel):
            channel = ctx.channel
            message_link = f"https://discord.com/channels/{ctx.guild.id}/{channel.id}/MESSAGE_ID"
        else:
            await ctx.send("This command can only be used in DMs or guild channels.")
            return
        async for message in channel.history(limit=1, oldest_first=True):
            oldest_message = message
            break
        if oldest_message:
            sender = oldest_message.author.mention
            sendername = oldest_message.author.name
            utc_time = oldest_message.created_at.replace(tzinfo=pytz.utc)
            time=pytz.timezone(self.time_zone)
            ist_time = utc_time.astimezone(time)
            timestamp = ist_time.strftime("%d-%m-%Y %H:%M:%S")
            if isinstance(ctx.channel, discord.TextChannel):
                message_link = f"https://discord.com/channels/{ctx.guild.id}/{channel.id}/{oldest_message.id}"
            else:
                message_link = f"https://discord.com/channels/@me/{channel.id}/{oldest_message.id}"
            response = f"<a:SPY_STORE:1329411121832267806> **Sender :** **{sender} | `{sendername}`**\n<a:SPY_STORE:1329411121832267806> **Message :** [**`Click Me`**]({message_link})\n<a:SPY_STORE:1329411121832267806> **Sent at :** `{timestamp}`"
            await send(ctx,"First msg",response)

    @commands.Cog.listener()
    async def on_ready(self):
        self.start_all_tasks()

    def load_data(self):
        with open(self.file_path, "r") as f:
            return json.load(f)

    def save_data(self, data):
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)

    def start_all_tasks(self):
        """Start tasks for all channels saved in the JSON file."""
        data = self.load_data()
        for channel_id, messages in data.items():
            for message_data in messages:
                self.start_task(int(channel_id), message_data["time"], message_data["message"])

    def start_task(self, channel_id, time_in_seconds, message):
        """Start a repeating task for a specific channel."""
        if channel_id not in self.tasks:
            self.tasks[channel_id] = []

        @tasks.loop(seconds=time_in_seconds)
        async def send_message():
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(message)
                except Exception as e:
                    pass
            else:
                pass

        send_message.start()
        self.tasks[channel_id].append(send_message)

    def stop_task(self, channel_id):
        if channel_id in self.tasks:
            for task in self.tasks[channel_id]:
                task.cancel()
            del self.tasks[channel_id]

    @commands.command(name="amstart",aliases=['automessage'])
    async def amadd(self, ctx, channel_id: int, time_in_seconds: int, *, message: str):
        await ctx.message.delete()
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                await ctx.send(f"<a:SPY_STORE:1329411121832267806> **Channel with ID `{channel_id}` not found.**")
                return

            data = self.load_data()

            if str(channel_id) not in data:
                data[str(channel_id)] = []

            data[str(channel_id)].append({
                "time": time_in_seconds,
                "message": message
            })

            self.save_data(data)
            self.start_task(channel_id, time_in_seconds, message)

            await ctx.send(f"<a:SPY_STORE:1329411121832267806> **Auto message task for  channel <#{channel_id}> (ID: `{channel_id}`). has been started**",delete_after = 30)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name="amstop",aliases=['amrem','amremove'])
    async def amremove(self, ctx, channel_id: int):
        await ctx.message.delete()
        data = self.load_data()
        if str(channel_id) not in data:
            await ctx.send(f"<a:SPY_STORE:1329411121832267806> **No Auto messages task found for channel ID `{channel_id}`.**",delete_after=20)
            return
        self.stop_task(channel_id)
        del data[str(channel_id)]
        self.save_data(data)
        await ctx.send(f"<a:SPY_STORE:1329411121832267806> **Auto messages for channel ID `{channel_id}` has been stopped.**",delete_after=20)


    @commands.command(name="amlist")
    async def amlist(self, ctx):
        await ctx.message.delete()
        try:
            with open(self.file_path, "r") as file:
                tasks_data = json.load(file)
        except FileNotFoundError:
            await ctx.send("<a:SPY_STORE:1329411121832267806> No active Auto-message tasks found.", delete_after=20)
            return
        if not tasks_data:
            await ctx.send("<a:SPY_STORE:1329411121832267806> No active Auto-message tasks found.", delete_after=20)
            return
        tasks_list = ""
        for channel_id, messages in tasks_data.items():
            tasks_list += f"**Channel <#{channel_id}>**\n"
            for message_data in messages:
                tasks_list += f"  - **Message**: {message_data['message']}\n"
                tasks_list += f"  - **Interval**: {message_data['time']} seconds\n\n"
        await send(ctx, "<a:SPY_STORE:1329411121832267806> **Active Auto-Message Tasks**", tasks_list)

    @commands.command(name="amclear")
    async def amclear(self, ctx):
        for channel_id in list(self.tasks.keys()):
            self.stop_task(channel_id)
        with open(self.file_path, "w") as file:
            json.dump({}, file)

        await ctx.send("<a:SPY_STORE:1329411121832267806>** All auto messages tasks have been cleared.**")

    @commands.command(aliases=['trigger+', 'addtrigger'])
    async def triggeradd(self,ctx, trigger , *,response: str):
        await ctx.message.delete()

        with open('database/triggers.json', 'r') as file:
            data = json.load(file)

        data[trigger] = response

        with open('database/triggers.json', 'w') as file:
            json.dump(data, file, indent=4)

        await send(
            ctx,
            header="trigger Added",
            description=f"<a:SPY_STORE:1329411121832267806> **Trigger**: `{trigger}`\n**Response**: {response}",
        )

    @commands.command(aliases=['trigger-', 'remtrigger'])
    async def triggerremove(self,ctx, trigger: str):
        await ctx.message.delete()
        with open('database/triggers.json', 'r') as file:
            data = json.load(file)

        if trigger in data:
            del data[trigger]

            with open('database/triggers.json', 'w') as file:
                json.dump(data, file, indent=4)

            await send(
                ctx,
                header="Trigger Removed",
                description=f"<a:SPY_STORE:1329411121832267806> **Trigger**: `{trigger}` has been successfully removed.",
            )
        else:
            await send(
                ctx,
                header="Trigger Not Found",
                description=f"<a:SPY_STORE:1329411121832267806> **Trigger**: `{trigger}` could not be found.",
            )

    @commands.command(aliases=['listtrigger', 'tlist'])
    async def triggerlist(self,ctx):
        await ctx.message.delete()
        with open('database/triggers.json', 'r') as file:
            data = json.load(file)

        responses = '\n'.join([f"<a:SPY_STORE:1329411121832267806> **`{trigger}`** : **`{response}`**" for trigger, response in data.items()])
        await send(
            ctx,
            header="Trigger List",
            description=f"{responses}",
        )

    @commands.command(aliases=['solve','simplify'])
    async def math(self,ctx, *, equation):
        api_endpoint = 'https://api.mathjs.org/v4/'        
        await ctx.message.delete()
        response = requests.get(api_endpoint, params={'expr': equation})
        if response.status_code == 200:
            result = response.text
            await send(ctx,"Math Calculation",f"<a:SPY_STORE:1329411121832267806> **Equation :** `{equation}`\n<a:SPY_STORE:1329411121832267806> **Answer :** `{result}`")

    @commands.command()
    async def timer(self,ctx, target_time: str):
        await ctx.message.delete()
        try:
            unit = target_time[-1]
            value = int(target_time[:-1])
            if unit == 's':
                seconds = value
            elif unit == 'm':
                seconds = value * 60
            elif unit == 'h':
                seconds = value * 3600
            elif unit == 'd':
                seconds = value * 86400
            else:
                await send(ctx,"Invalid format", "Invalid units! use 's' for seconds, 'm' for minutes, 'h' for hours, or 'd' for days.")
                return
            future_time = int(t.time()) + seconds
            await send(ctx,"Timer",f"**Timer ending**\n# <t:{future_time}:R>.\n",f"{seconds}")
            await asyncio.sleep(seconds)
            await ctx.send(f"{ctx.author.mention} , timer of {target_time} has been ended!")
        except ValueError:
            await ctx.send("Invalid input! Please enter the time like `10s`, `5m`, `2h`, or `1d`.")

    @commands.command()
    async def define(self,ctx, *, word):
        await ctx.message.delete()
        api_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

        response = requests.get(api_url)

        if response.status_code == 200:
            data = response.json()
            if data:
                word_data = data[0]
                word_meanings = word_data['meanings']

                meanings_list = []
                for meaning in word_meanings:
                    part_of_speech = meaning['partOfSpeech']
                    definitions = meaning['definitions']

                    def_text = f"**{part_of_speech.capitalize()}:**\n"
                    for i, definition in enumerate(definitions, start=1):
                        def_text += f"{i}. {definition['definition']}\n"
                        if 'example' in definition:
                            def_text += f"   *Example: {definition['example']}*\n"

                    meanings_list.append(def_text)

                result_text = f"<a:SPY_STORE:1329411121832267806> **{word.capitalize()}**\n\n" + '\n<a:SPY_STORE:1329411121832267806> '.join(meanings_list)
                await send(ctx,"Word Defination",result_text)


    @commands.command()
    async def translate(self, ctx, *, text: str = None):
        await ctx.message.delete()
        if text is None:
            if ctx.message.reference and ctx.message.reference.resolved:
                referenced_message = ctx.message.reference.resolved
                text = referenced_message.content
            else:
                return await ctx.send("❌ Please provide text or reply to a message containing text.")

        try:
            source_language = detect(text)
        except:
            source_language = "unknown"
        
        try:
            translated_text = GoogleTranslator(source='auto', target='en').translate(text)
        except Exception as e:
            return await send(ctx, "Translation Error", f"`{e}`")

        response_message = (
            f"<a:SPY_STORE:1329411121832267806> **Original Text:** {text}\n"
            f"<a:SPY_STORE:1329411121832267806> **Detected Language:** {source_language}\n"
            f"<a:SPY_STORE:1329411121832267806> **Translated Text:** {translated_text}"
        )

        await send(ctx, "Translator", response_message)


    def cog_unload(self):
        if self.change_status_task and self.change_status_task.is_running():
            self.change_status_task.cancel()
        if self.change_presence_task and self.change_presence_task.is_running():
            self.change_presence_task.cancel()
            
    def get_emoji_from_text(self, text):
        # Regex to match custom emojis: <:name:id>
        emoji_regex = r"(<a?:\w+:\d+>)"
        match = re.search(emoji_regex, text)
        if match:
            emoji = match.group(1)
            emoji_parts = emoji.strip('<>').split(':')
            emoji_name = emoji_parts[1]
            emoji_id = emoji_parts[2]
            return re.match(emoji_regex, text)
        return None
    
    def parse_status(self, status):
        emoji_regex = r"<a?:\w+:(\d+)>"
        match = re.search(emoji_regex, status)
        if match:
            emoji_id = match.group(1)
            emoji_name = re.search(r"<a?:([a-zA-Z0-9_]+):\d+>", status).group(1)
            message = re.sub(emoji_regex, "", status).strip()
            return emoji_name, emoji_id, message
        return None, None, status    

    def load_config(self, path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file at '{path}' not found.")
        except json.JSONDecodeError:
            raise ValueError(f"Config file at '{path}' is not valid JSON.")

    async def set_status(self, emoji_name=None, emoji_id=None, message=None):
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": self.config.get("token")}
            custom_status = {}
            if emoji_name:
                custom_status["emoji_name"] = emoji_name
            if emoji_id:
                custom_status["emoji_id"] = emoji_id
            if message:
                custom_status["text"] = message
            json_data = {"status": "dnd", "custom_status": custom_status}
            async with session.patch(self.url, headers=headers, json=json_data):
                pass

    async def set_presence(self, presence):
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": self.config.get("token")}
            json_data = {"status": presence}
            async with session.patch(self.url, headers=headers, json=json_data) as response:
                if response.status != 200:
                    print(f"Failed to set presence: {response.status}")

    @tasks.loop(seconds=3)
    async def change_status(self):
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        interval = config.get("status_rotator_interval_in_seconds")         
        for emoji, text in self.statuses:
            if emoji:
                emoji_parts = re.match(r"<a?:([a-zA-Z0-9_]+):(\d+)>", emoji)
                emoji_name = emoji_parts.group(1) if emoji_parts else None
                emoji_id = emoji_parts.group(2) if emoji_parts else None
                await self.set_status(emoji_name, emoji_id, text)
            else:
                await self.set_status(None, None, text)
            await asyncio.sleep(interval)

    @tasks.loop(seconds=3)    
    async def change_presence(self):    
        for presence in self.presence:
            await self.set_presence(presence)
            await asyncio.sleep(1)   


    @commands.command(aliases=['setrot'])
    async def setrotator(self, ctx, *, statuses):
        await ctx.message.delete()
        raw_statuses = statuses.split(',')
        self.statuses = []
        for status in raw_statuses:
            status = status.strip()

            emoji_match = re.match(r"<a?:[a-zA-Z0-9_]+:\d+>", status)
            if emoji_match:
                emoji = emoji_match.group(0)
                text = status.replace(emoji, "").strip() or ""
                emoji_parts = emoji.strip('<>').split(':')
                emoji_name = emoji_parts[1]
                emoji_id = emoji_parts[2]
                self.statuses.append((f"<:{emoji_name}:{emoji_id}>", text))  # Using the format for storing emoji
            else:
                self.statuses.append(("", status))
        await send(ctx, "Status Rotator", f"Rotator has been set successfuly", "20")

        if not self.change_status.is_running():
            self.change_status.start()
    @commands.command(aliases=['stoprot'])
    async def stoprotator(self, ctx):
        await ctx.message.delete()
        self.change_status.stop()
        await send(ctx, "Status rotator", "<a:SPY_STORE:1329411121832267806> Rotator stopped", "10")
        await self.set_status("")        

    @commands.command(aliases=["setstat"])
    async def setstatus(self, ctx, *, status):
        await ctx.message.delete()
        if hasattr(self, "change_status"):
            self.change_status.stop()  # Stop the loop if it exists
        
        # Parse the status to extract emoji and text
        emoji_name, emoji_id, message = self.parse_status(status)

        # Call the set_status method
        await self.set_status(emoji_name=emoji_name, emoji_id=emoji_id, message=message)
        await send(ctx, "Set status", f"<a:SPY_STORE:1329411121832267806> Your status has been set to {status}", "10")

    @commands.command(aliases=['clearstat','clearstatus','removestat','remstatus','remstat'])
    async def removestatus(self, ctx):
        await ctx.message.delete()
        await self.set_status("")
        await send(ctx, "Clear status", f"<a:SPY_STORE:1329411121832267806> Your status has been cleared", "10")

    @commands.command(aliases=['seton'])
    async def online(self, ctx):
        await ctx.message.delete()
        self.change_presence.cancel()        
        await self.set_presence("online")       
        await ctx.send(f"**<:SPY_STORE:1329412343964106752> Your presence set to Online.**",delete_after=30)

    @commands.command(aliases=['setdnd'])
    async def dnd(self, ctx):
        await ctx.message.delete()
        self.change_presence.cancel()        
        await self.set_presence("dnd")
        await ctx.send(f"**<:SPY_STORE:1329412300557258782> Your presence set to DND.**",delete_after=30)

    @commands.command(aliases=['setidle'])
    async def idle(self, ctx):
        await ctx.message.delete()
        self.change_presence.cancel()        
        await self.set_presence("idle")
        await ctx.send(f"**<:SPY_STORE:1329412355981049886> Your presence set to Idle.**",delete_after=30)

    @commands.command(aliases=['setinv','offline','off'])
    async def invisible(self, ctx):
        await ctx.message.delete()
        self.change_presence.cancel()         
        await self.set_presence("invisible")
        await ctx.send(f"**<:SPY_STORE:1329412330928341024> Your presence set to offline.**",delete_after=30)

    @commands.command(aliases=['prescycle'])
    async def presencecycle(self, ctx):
        await ctx.message.delete()
        if self.change_presence.is_running():
            self.change_presence.cancel()
            await ctx.send("**<a:SPY_STORE:1329365156475699201> | Presence cycling stopped.**",delete_after=30)
        else:
            self.change_presence.start()
            await ctx.send("**<a:SPY_STORE:1329365156475699201> | Presence cycling started.**",delete_after=30)        

    @commands.command(aliases=['listen'])
    async def listening(self, ctx, *, message):
        await ctx.message.delete()
        await self.bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=message,
        ))
        await send(ctx, "Listening", f"<a:SPY_STORE:1329411121832267806> Listening activity with message `{message}` created", "10")

    @commands.command(aliases=['watch'])
    async def watching(self, ctx, *, message):
        await ctx.message.delete()
        await self.bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=message,
        ))
        await send(ctx, "Watching", f"<a:SPY_STORE:1329411121832267806> Watching activity with message `{message}` created", "10")

    @commands.command(aliases=['stream'])
    async def streaming(self, ctx, *, message):
        await ctx.message.delete()
        await self.bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.streaming,
            name=message,
        ))       
        await send(ctx, "Streaming", f"<a:SPY_STORE:1329411121832267806> Streaming activity with message `{message}` created", "10")

    @commands.command(aliases=['play'])
    async def playing(self, ctx, *, message):
        await ctx.message.delete()
        await self.bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.playing,
            name=message,
        ))
        await send(ctx, "Playing", f"<a:SPY_STORE:1329411121832267806> Playing activity with message `{message}` created", "10")

    @commands.command(aliases=['compete'])
    async def competing(self, ctx, *, message):
        await ctx.message.delete()
        await self.bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.competing,
            name=message,
        ))
        await send(ctx, "Competing", f"<a:SPY_STORE:1329411121832267806> Competing activity with message `{message}` created", "10")

    @commands.command(aliases=['stopact', 'stopactivity', 'actstop', 'activitystop'])
    async def stop_activity(self, ctx):
        await ctx.message.delete()
        await self.bot.change_presence(activity=None)
        await send(ctx, "Activity Stopped", "<a:SPY_STORE:1329411121832267806> Activity stopped", "10")

    @commands.command()
    async def activity(self, ctx):
        try:
            await ctx.message.delete()
        except discord.NotFound:
            pass 
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        prefix = config.get("prefix")        
        help_message = (
            f"<a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253>\n"
            f"<:SPY_STORE:1329255509735378985> **`[REQUIRED] | <OPTIONAL>`** <a:SPY_STORE:1329357365031731221>\n"
            f"<a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253>\n"            
            f"<a:SPY_STORE:1329365156475699201> | **Set Status** **»** **`{prefix}setstat [text]`**\n"
            f"<a:SPY_STORE:1329365156475699201> | **Clear Status** **»** **`{prefix}clearstat`**\n"
            f"<a:SPY_STORE:1329365156475699201> | **Online** **»** **`{prefix}online`**\n"
            f"<a:SPY_STORE:1329365156475699201> | **Idle** **»** **`{prefix}idle`**\n"
            f"<a:SPY_STORE:1329365156475699201> | **DND** **»** **`{prefix}dnd`**\n"
            f"<a:SPY_STORE:1329365156475699201> | **Offline** **»** **`{prefix}invisible`**\n"                                    
            f"<a:SPY_STORE:1329365156475699201> | **Presence Cycle** **»** **`{prefix}prescycle`**\n"
            f"<a:SPY_STORE:1329365156475699201> | **Listening** **»** **`{prefix}listen [message]`**\n"
            f"<a:SPY_STORE:1329365156475699201> | **Watching** **»** **`{prefix}watch [message]`**\n"
            f"<a:SPY_STORE:1329365156475699201> | **Streaming** **»** **`{prefix}stream [message]`**\n"
            f"<a:SPY_STORE:1329365156475699201> | **Playing** **»** **`{prefix}play [message]`**\n"
            f"<a:SPY_STORE:1329365156475699201> | **Competing** **»** **`{prefix}compete [message]`**\n"
            f"<a:SPY_STORE:1329365156475699201> | **Stop Activity** **»** **`{prefix}stopact`**\n"
            f"<a:SPY_STORE:1329365156475699201> | **Status Rotator** **»** **`{prefix}setrot [text1],[text2]..`**\n"
            f"<a:SPY_STORE:1329365156475699201> | **Stop Rotator** **»** **`{prefix}stoprot`**\n"
            f"<a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253><a:SPY_STORE:1329386865807327253>"        
        )
        await send(ctx, "<:SPY_STORE:1329152544055754794>__Activity Commands__<a:SPY_STORE:1329152680492535808>", help_message)

    def _get_activity_type(self, activity):
        activity_type_map = {
            'playing': ActivityType.playing,
            'watching': ActivityType.watching,
            'listening': ActivityType.listening,
            'streaming': ActivityType.streaming,
            'competing': ActivityType.competing
        }
        return activity_type_map.get(activity.lower(), ActivityType.playing)        


async def setup(bot):
    await bot.add_cog(extra(bot))
