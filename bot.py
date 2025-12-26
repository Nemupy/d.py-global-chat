import asyncio
import discord
from discord.ext import commands
import datetime
import os

TOKEN = "YOUR_TOKEN"

COGS_EXTENSIONS = [
    "cogs.gc_join",
    "cogs.gc_leave",
    "cogs.gc_message",
    "cogs.gc_delete",
    "cogs.gc_edit",
    "cogs.gc_mute"
]

intents = discord.Intents.all()
activity = discord.Activity(name="Test", type=discord.ActivityType.competing)

bot = commands.Bot(command_prefix="!", intents=intents, activity=activity)


@bot.event
async def on_ready():
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] INFO: Logged in as {bot.user} (ID: {bot.user.id})")
    guild = discord.Object(1357910973201121473)
    await bot.tree.sync(guild=guild)
    print(f"[{current_time}] INFO: Command tree synced for guild {guild.id}.")
    await bot.tree.sync()
    print(f"[{current_time}] INFO: Command tree synced successfully.")


async def load_extension():
    await bot.load_extension("jishaku")
    for cog in COGS_EXTENSIONS:
        await bot.load_extension(cog)


async def main():
    async with bot:
        await load_extension()
        await bot.start(TOKEN)

asyncio.run(main())