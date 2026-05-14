import discord
from discord.ext import commands

from config import DISCORD_TOKEN, SERVER_ID

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready():
    bot.tree.clear_commands(guild=None)
    await bot.tree.sync()
    await bot.load_extension("cogs.issues")
    await bot.load_extension("cogs.webhook")
    await bot.load_extension("cogs.stats")
    await bot.load_extension("cogs.activity")
    guild = discord.Object(id=SERVER_ID)
    bot.tree.clear_commands(guild=guild)
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)
    print(f"Bot online: {bot.user}")


bot.run(DISCORD_TOKEN)
