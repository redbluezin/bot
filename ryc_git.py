import discord
from discord.ext import commands
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import json
import os
import requests

# =========================
# CONFIG
# =========================

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
API_KEY = os.getenv('API_KEY')

DATA_FILE = "acct.json"
LOG_FILE = "log.txt"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# JSON
# =========================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def log(text):
    with open(LOG_FILE, "a") as f:
        f.write(text + "\n")

# =========================
# IA
# =========================

def ask_ai(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta-llama/llama-3.3-70b-instruct",
        "messages": [
            {"role": "system", "content": "Você é um assistente direto chamado Aria."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 300
    }

    r = requests.post(url, json=data, headers=headers)
    j = r.json()

    if "error" in j:
        return None

    return j["choices"][0]["message"]["content"]

# =========================
# HELPERS
# =========================

def get_guild(data, guild_id):
    guild_id = str(guild_id)
    if guild_id not in data:
        data[guild_id] = {"usuarios": {}}
    return data[guild_id]

def get_logged_user(usuarios, user_id):
    for name, u in usuarios.items():
        if u.get("logado") == user_id:
            return name, u
    return None, None

def pegar_avatar(user: discord.Member):
    url = user.avatar.url if user.avatar else user.default_avatar.url
    response = requests.get(url)
    return Image.open(BytesIO(response.content)).convert("RGBA")

# =========================
# DELETE AUTOMÁTICO DE COMANDOS
# =========================

@bot.before_invoke
async def auto_delete(ctx):
    if ctx.command and ctx.command.name != "ai":
        try:
            await ctx.message.delete()
        except:
            pass

# =========================
# ON READY
# =========================

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")
    activity = discord.Game(name="!helpme")
    await bot.change_presence(activity=activity)


# =========================
# REGISTRO
# =========================

@bot.command()
async def registro(ctx, nome, senha):
    data = load_data()
    guild = get_guild(data, ctx.guild.id)
    usuarios = guild["usuarios"]

    if nome in usuarios:
        return await ctx.send("nome já existe ❌")

    usuarios[nome] = {
        "senha": senha,
        "adm": False,
        "usos": 20,
        "logado": False
    }

    save_data(data)
    await ctx.send("conta criada ✔")

# =========================
# LOGIN
# =========================

@bot.command()
async def login(ctx, nome, senha):
    data = load_data()
    guild = get_guild(data, ctx.guild.id)
    usuarios = guild["usuarios"]

    user = usuarios.get(nome)

    if not user or user["senha"] != senha:
        return await ctx.send("login falhou ❌")

    user["logado"] = ctx.author.id

    save_data(data)
    await ctx.send("logado ✔")

# =========================
# LOGOUT
# =========================

@bot.command()
async def logout(ctx):
    data = load_data()
    guild = get_guild(data, ctx.guild.id)
    usuarios = guild["usuarios"]

    for u in usuarios.values():
        if u["logado"] == ctx.author.id:
            u["logado"] = False
            save_data(data)
            return await ctx.send("deslogado ✔")

    await ctx.send("você não está logado ❌")

# =========================
# HELP
# =========================

@bot.command()
async def helpme(ctx):
    await ctx.send(
        "> **COMANDOS**\n"
        "> ❓!helpme\n"
        "> 📝!registro nome senha\n"
        "> 📄!login nome senha\n"
        "> ❌!logout\n"
        "> ✍️!ai texto\n"
        "> 🎁!gift user qtd\n"
        "> ♥️!ship user user\n"
        "> 👑!setup user qtd"
    )

# =========================
# AI
# =========================

@bot.command()
async def ai(ctx, *, texto):
    data = load_data()
    guild = get_guild(data, ctx.guild.id)
    usuarios = guild["usuarios"]

    name, user = get_logged_user(usuarios, ctx.author.id)

    if not user:
        return await ctx.send("você precisa estar logado ❌")

    if user["usos"] <= 0:
        return await ctx.send("sem usos ❌")

    resposta = ask_ai(texto)

    if not resposta:
        return await ctx.send("erro na IA 😓")

    user["usos"] -= 1
    save_data(data)

    await ctx.send(resposta)

# =========================
# GIFT
# =========================

@bot.command()
async def gift(ctx, alvo, qtd: int):
    data = load_data()
    guild = get_guild(data, ctx.guild.id)
    usuarios = guild["usuarios"]

    name, user = get_logged_user(usuarios, ctx.author.id)

    if not user:
        return await ctx.send("loga primeiro ❌")

    if alvo not in usuarios:
        return await ctx.send("usuário não existe ❌")

    if user["usos"] < qtd:
        return await ctx.send("sem usos ❌")

    user["usos"] -= qtd
    usuarios[alvo]["usos"] += qtd

    save_data(data)

    log(f"{name} emprestou {qtd} usos para {alvo} no servidor {ctx.guild.id}")

    await ctx.send("transferido ✔")

# =========================
# SHIP
# =========================

@bot.command()
async def ship(ctx, user1: discord.Member, user2: discord.Member):

    # 🖼️ base 1200x600
    base = Image.open("base.png").convert("RGBA").resize((1200, 600))
    draw = ImageDraw.Draw(base)

    # 👤 avatars
    avatar1 = pegar_avatar(user1).resize((220, 220))
    avatar2 = pegar_avatar(user2).resize((220, 220))

    # 🔵 máscara circular
    mask = Image.new("L", (220, 220), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, 220, 220), fill=255)

    # 📍 posições mais equilibradas
    base.paste(avatar1, (200, 100), mask)
    base.paste(avatar2, (780, 100), mask)

    # ✍️ fonte
    font = ImageFont.truetype("Arial.ttf",60)

    # 🧾 nomes centralizados automaticamente

    def draw_center_text(draw, text, font, center_x, y):
        text_width = draw.textbbox((0, 0), text,font=font)[2]
        x = center_x - text_width // 2
        draw.text((x, y), text, fill="white", font=font)


    # centros dos avatares
    user1_center_x = 200 + 110 - 20   # avatar (220px / 2)
    user2_center_x = 780 + 110

    draw_center_text(draw, user1.name, font,user1_center_x, 350)
    draw_center_text(draw, user2.name, font,user2_center_x, 350)

    # 💘 porcentagem fake (melhorzinho agora)
    percent = (hash(user1.id + user2.id) % 101)

    draw.text((520, 250), f"{percent}% 💘", fill="red", font=font)

    # 📤 enviar
    buffer = BytesIO()
    base.save(buffer, "PNG")
    buffer.seek(0)

    await ctx.send(file=discord.File(buffer, "ship.png"))

# =========================
# SETUP (ADM)
# =========================

@bot.command()
async def setup(ctx, alvo, qtd: int):
    data = load_data()
    guild = get_guild(data, ctx.guild.id)
    usuarios = guild["usuarios"]

    name, user = get_logged_user(usuarios, ctx.author.id)

    if not user or not user["adm"]:
        return await ctx.send("sem permissão ❌")

    if alvo not in usuarios:
        return await ctx.send("usuário não existe ❌")

    usuarios[alvo]["usos"] += qtd

    save_data(data)

    log(f"{name} (id {ctx.author.id}) gerou {qtd} usos para {alvo} no servidor {ctx.guild.id}")

    await ctx.send("adicionado ✔")

# =========================
# RUN
# =========================

bot.run(DISCORD_TOKEN)
