import discord
from discord.ext import commands
import json, os, datetime, random

TOKEN = "ใส่โทเคนบอทตรงนี้"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="/", intents=intents)

DB_FILE = "database.json"

# ---------------- Database ----------------
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({}, f)
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def check_user(user_id):
    db = load_db()
    if str(user_id) not in db:
        db[str(user_id)] = {
            "points": 0,
            "exp": 0,
            "level": 1,
            "last_checkin": None
        }
        save_db(db)
    return db

# ---------------- Role Config ----------------
ROLE_COST = 200            # แต้มที่ใช้ในการสุ่มยศ
LEVEL_ROLES = {            # ยศปลดล็อกตามเลเวล
    5:  "Beginner",
    10: "Intermediate",
    20: "Advanced"
}

RANDOM_ROLES = [           # ยศที่สามารถสุ่มได้
    "Lucky",
    "Special",
    "VIP"
]

# ---------------- View ปุ่ม Check-in ----------------
class CheckinView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ เช็คอิน", style=discord.ButtonStyle.green, custom_id="checkin_button")
    async def checkin(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = check_user(interaction.user.id)
        user = db[str(interaction.user.id)]
        today = str(datetime.date.today())

        if user["last_checkin"] == today:
            await interaction.response.send_message("⚠️ วันนี้คุณเช็คอินไปแล้ว!", ephemeral=True)
            return

        reward = 50
        exp_gain = 1
        user["points"] += reward
        user["exp"] += exp_gain
        user["last_checkin"] = today

        # อัปเดตเลเวล
        new_level = user["exp"] // 5 + 1
        if new_level > user["level"]:
            user["level"] = new_level
            await unlock_role(interaction, user["level"])

        save_db(db)
        await interaction.response.send_message(
            f"🎉 {interaction.user.mention} เช็คอินสำเร็จ!\n+{reward} แต้ม, +{exp_gain} EXP\nเลเวล: {user['level']}",
            ephemeral=True
        )

# ---------------- ฟังก์ชันปลดล็อกยศ ----------------
async def unlock_role(interaction, level):
    guild = interaction.guild
    member = interaction.user

    if level in LEVEL_ROLES:
        role_name = LEVEL_ROLES[level]
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await member.add_roles(role)
            await interaction.followup.send(
                f"🔓 {member.mention} ปลดล็อกยศ **{role_name}** แล้ว!", ephemeral=True
            )

# ---------------- คำสั่ง ----------------
@bot.command()
async def checkin(ctx):
    view = CheckinView()
    await ctx.send("กดปุ่มด้านล่างเพื่อเช็คอินและรับแต้ม/EXP ⬇️", view=view)

@bot.command()
async def points(ctx):
    db = check_user(ctx.author.id)
    user = db[str(ctx.author.id)]
    await ctx.send(
        f"💰 {ctx.author.mention}\nแต้ม: {user['points']} | EXP: {user['exp']} | เลเวล: {user['level']}"
    )

@bot.command()
async def buyrole(ctx):
    db = check_user(ctx.author.id)
    user = db[str(ctx.author.id)]

    if user["points"] < ROLE_COST:
        await ctx.send(f"❌ ต้องมีอย่างน้อย {ROLE_COST} แต้มถึงจะสุ่มยศได้!")
        return

    user["points"] -= ROLE_COST
    role_name = random.choice(RANDOM_ROLES)
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"🎲 {ctx.author.mention} ใช้ {ROLE_COST} แต้ม และสุ่มได้ยศ **{role_name}** !")
    else:
        await ctx.send(f"⚠️ ไม่พบยศ {role_name} ในเซิร์ฟเวอร์!")

    save_db(db)

# ---------------- Event ----------------
@bot.event
async def on_ready():
    bot.add_view(CheckinView())  # โหลดปุ่มใหม่ทุกครั้งที่บอทเปิด
    print(f"✅ Logged in as {bot.user}")

bot.run(TOKEN)
