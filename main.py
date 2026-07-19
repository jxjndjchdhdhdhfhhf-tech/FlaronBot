import discord
from discord.ext import commands
from discord import ui, ButtonStyle
import asyncio
import os
import sqlite3

# --- دالة إضافة النقاط (جديدة) ---
def add_staff_points(user_id, amount=5):
    conn = sqlite3.connect('staff_points.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS points (user_id INTEGER PRIMARY KEY, score INTEGER DEFAULT 0)')
    cursor.execute('INSERT OR IGNORE INTO points (user_id, score) VALUES (?, 0)', (user_id,))
    cursor.execute('UPDATE points SET score = score + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

# إعدادات البوت
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# قائمة الرتب المشتركة
STAFF_ROLE_IDS = [
    1521502153129197609, 1526922584258510959, 
    1526927634951442502, 1527199174615896064, 1526929542512640181,
    1526932395406921875, 1526931929180536843, 1526932471583739936
]

# كلاس أزرار التقييم بالنجوم
class RatingView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def send_thanks(self, interaction, rating):
        for child in self.children:
            child.disabled = True
            if child.custom_id == f"rate_{rating}":
                child.style = ButtonStyle.success
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"شكراً لتقييمك: {rating} نجوم! ⭐", ephemeral=True)

    @ui.button(label="⭐", style=ButtonStyle.secondary, custom_id="rate_1")
    async def rate_1(self, interaction: discord.Interaction, button: ui.Button):
        await self.send_thanks(interaction, 1)
    
    @ui.button(label="⭐⭐", style=ButtonStyle.secondary, custom_id="rate_2")
    async def rate_2(self, interaction: discord.Interaction, button: ui.Button):
        await self.send_thanks(interaction, 2)

    @ui.button(label="⭐⭐⭐", style=ButtonStyle.secondary, custom_id="rate_3")
    async def rate_3(self, interaction: discord.Interaction, button: ui.Button):
        await self.send_thanks(interaction, 3)

    @ui.button(label="⭐⭐⭐⭐", style=ButtonStyle.secondary, custom_id="rate_4")
    async def rate_4(self, interaction: discord.Interaction, button: ui.Button):
        await self.send_thanks(interaction, 4)

    @ui.button(label="⭐⭐⭐⭐⭐", style=ButtonStyle.secondary, custom_id="rate_5")
    async def rate_5(self, interaction: discord.Interaction, button: ui.Button):
        await self.send_thanks(interaction, 5)

# كلاس الأزرار (Close, Claim, Hold)
class TicketActionsView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Close", style=ButtonStyle.danger, custom_id="close_btn")
    async def close(self, interaction: discord.Interaction, button: ui.Button):
        # إضافة 5 نقاط عند الإغلاق
        add_staff_points(interaction.user.id, 5)
        
        embed = discord.Embed(
            title="Thank you for your feedback!",
            description=f"Your ticket `{interaction.channel.name}` has been closed. We'd love to hear your feedback!\n\n[Click here to view the transcript](https://example.com)\n\n**Your Rating**\nPlease rate your experience below:",
            color=discord.Color.green()
        )
        
        try:
            await interaction.user.send(embed=embed, view=RatingView())
        except discord.Forbidden:
            await interaction.channel.send("⚠️ لم أتمكن من إرسال رسالة التقييم إلى الخاص لأن إعدادات الرسائل الخاصة لديك مغلقة.")

        await interaction.response.send_message("تم إغلاق التذكرة وإضافة 5 نقاط. سيتم حذف القناة خلال 5 ثوانٍ...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @ui.button(label="Claim", style=ButtonStyle.primary, custom_id="claim_btn")
    async def claim(self, interaction: discord.Interaction, button: ui.Button):
        # التحقق من أن المستخدم لديه إحدى رتب الاستاف
        user_role_ids = [role.id for role in interaction.user.roles]
        if any(role_id in STAFF_ROLE_IDS for role_id in user_role_ids):
            # إضافة 5 نقاط عند الاستلام
            add_staff_points(interaction.user.id, 5)
            
            await interaction.channel.edit(name=f"claimed-{interaction.user.name.lower()[:10]}")
            button.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"✅ تم استلام التذكرة بواسطة {interaction.user.mention} (+5 نقاط)")
        else:
            await interaction.response.send_message("عذراً، لا تملك الصلاحية لاستلام التذاكر!", ephemeral=True)

    @ui.button(label="Hold", style=ButtonStyle.secondary, custom_id="hold_btn")
    async def hold(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("التذكرة الآن في وضع الانتظار.")

# كلاس نظام فتح التيكيت
class TicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="فتح تيكيت 🎫", style=ButtonStyle.green, custom_id="open_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        member = interaction.user
        channel_name = f"ticket-{member.name.lower()}"
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        for role_id in STAFF_ROLE_IDS:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
        
        await interaction.followup.send(f"تم إنشاء تذكرتك بنجاح في: {channel.mention}", ephemeral=True)
        
        staff_mentions = " ".join([f"<@&{rid}>" for rid in STAFF_ROLE_IDS if guild.get_role(rid)])
        await channel.send(f"🔔 **تذكرة جديدة!** {staff_mentions}\nيرجى من أحد الموظفين استلام التذكرة بالضغط على زر **Claim**.")
        
        welcome_embed = discord.Embed(
            title=f"Welcome to {channel_name}",
            description="The support team will be with you shortly.\n**Category:** ticket",
            color=discord.Color.green()
        )
        await channel.send(embed=welcome_embed, view=TicketActionsView())
        
        detailed_welcome = f"""# 👋 مرحبًا {member.mention}

شكرًا لتواصلك معنا عبر التذكرة **`{channel_name}`** في قسم **`ticket`**.

## 📌 ملاحظات مهمة

* يرجى **عدم عمل منشن** لفريق الدعم أو الاستاف داخل التذكرة.
* يتم مراجعة جميع التذاكر والرد عليها حسب **الترتيب والأولوية**.
* قد يؤدي تكرار المنشن إلى اتخاذ إجراءات تحد من إمكانية استخدام نظام التذاكر.

## 🛠️ نطاق الدعم الفني

يدعم فريقنا فقط المشاكل المتعلقة بـ:

* 🌐 الاستضافة
* 🖥️ المواقع الإلكترونية
* 🤖 خدمات الديسكورد

**ولا يشمل الدعم:**

* الملفات الخاصة بك
* الأكواد البرمجية
* الإضافات والسكربتات
* التعديلات أو الإعدادات التي قمت بها بنفسك

## ⏳ يرجى التحلي بالصبر

سيقوم أحد أعضاء فريق الدعم الفني بالرد على تذكرتك في أقرب وقت ممكن.

شكرًا لتفهمك وتعاونك، **adhm0127** ❤️"""
        
        await channel.send(detailed_welcome)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    embed = discord.Embed(
        title="⚔️ Flaron Mc | نظام التذاكر",
        description="""مرحباً بك في نظام التذاكر الخاص بـ **Flaron Mc**!
يرجى الضغط على الزر أدناه لفتح تذكرة جديدة.

⚠️ **ملاحظة هامة:**
• يرجى التحلي بالصبر وعدم عمل منشن (Ping) للإدارة.
• سيتم إغلاق التذكرة بعد حل المشكلة.

شكراً لتعاونك معنا! 🤝""",
        color=discord.Color.dark_gray()
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/1522296835706847365/1527005566038310962/Picsart_26-07-15_20-33-44-745.jpg")
    
    await ctx.send(embed=embed, view=TicketView())

@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(TicketActionsView())
    bot.add_view(RatingView())
    
    activity = discord.Game(name="Tickets 🎫")
    await bot.change_presence(activity=activity)
    
    print(f'البوت {bot.user} متصل الآن!')

bot.run(os.environ['TOKEN'])
