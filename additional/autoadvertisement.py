import discord
from discord.ext import commands
import json
from main import send,senderror
import os

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

    # Ensure all keys exist
    for key in default_data:
        if key not in data:
            data[key] = default_data[key]

    save_ads(data)  # Save back the updated/corrected structure
    return data


def save_ads(data):
    with open(ADS_FILE, "w") as f:
        json.dump(data, f, indent=4)

class AutoAdvertise(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ads = load_ads()

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
        if trigger not in self.ads["triggers"]:
            return await senderror(ctx, "Not Found", f"No ad exists with trigger `{trigger}`.")
        del self.ads["triggers"][trigger]
        self.ads["aliases"] = {k: v for k, v in self.ads["aliases"].items() if v != trigger}
        save_ads(self.ads)
        await send(ctx, "Ad Removed", f"Trigger `{trigger}` removed.")

    @commands.command(aliases=["adguild+", "guildadd"])
    async def adguildadd(self, ctx, guild_id: int):
        if guild_id in self.ads["guilds"]:
            return await senderror(ctx, "Already Exists", f"Guild `{guild_id}` is already added.")
        self.ads["guilds"].append(guild_id)
        save_ads(self.ads)
        await send(ctx, "Guild Added", f"Guild `{guild_id}` added to the allowlist.")

    @commands.command(aliases=["delguild","remguild",'adguild-'])
    async def adguildrem(self, ctx, guild_id: int):
        if guild_id not in self.ads["guilds"]:
            return await senderror(ctx, "Not Found", f"Guild `{guild_id}` is not in the list.")
        self.ads["guilds"].remove(guild_id)
        save_ads(self.ads)
        await send(ctx, "Guild Removed", f"Guild `{guild_id}` removed from the allowlist.")

    @commands.command(aliases=['adalias+','aliasad+'])
    async def adaliasadd(self, ctx, trigger: str, alias: str):
        if trigger not in self.ads["triggers"]:
            return await senderror(ctx, "Invalid Trigger", f"Trigger `{trigger}` doesn't exist.")
        self.ads["aliases"][alias] = trigger
        save_ads(self.ads)
        await send(ctx, "Alias Added", f"Alias `{alias}` will now trigger ad `{trigger}`.")

    @commands.command(aliases=["aliasdel", "removead", "adalias-"])
    async def adaliasrem(self, ctx, alias: str):
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

async def setup(bot):
    await bot.add_cog(AutoAdvertise(bot))
