import random
import discord
from discord import app_commands
from discord.ext import commands

TOKEN = "ODUwNTQxODkzMDgyNjc3Mjc5.G5mZw8.kkznyZW3WRvLiJ0ush4hLFK1GmiYd_gMkdWrXU"

# Intents básicos
intents = discord.Intents.default()

# Criando o bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Evento quando o bot liga
@bot.event
async def on_ready():
    print(f"Bot online como: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Erro ao sincronizar: {e}")

# Slash command /dado
@bot.tree.command(name="dado", description="Gera um número aleatório entre 1 e 100")
async def dado(interaction: discord.Interaction):
    num = random.randint(1, 100)
    await interaction.response.send_message(f"🎲 Seu número é: **{num}**")

bot.run(TOKEN)
