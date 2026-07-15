import discord
from discord.ext import commands
from discord import ui, ButtonStyle
import asyncio
import os # لإدارة التوكن بأمان

# إعدادات البوت
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# كلاس الأزرار (Close, Claim, Hold)
class TicketActionsView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Close", style=ButtonStyle.danger, custom_id="close_btn")
    async def close(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("سيتم حذف القناة خلال 5 ثوانٍ...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @ui.button(label="Claim", style=ButtonStyle.primary, custom_id="claim_btn")
    async def claim(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(f"تم استلام التذكرة بواسطة {interaction.user.mention}")

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
        
        channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
        await interaction.followup.send(f"تم إنشاء تذكرتك بنجاح في: {channel.mention}", ephemeral=True)
        
        welcome_embed = discord.Embed(
            title=f"Welcome to {channel_name}",
            description="The support team will be with you shortly.\n**Category:** ticket",
            color=discord.Color.green()
        )
        await channel.send(embed=welcome_embed, view=TicketActionsView())
        
        detailed_welcome = f"""# 👋 مرحبًا {member.mention}
شكرًا لتواصلك معنا عبر التذكرة **`{channel_name}`**.
سيقوم أحد أعضاء فريق الدعم الفني بالرد على تذكرتك في أقرب وقت ممكن.
شكرًا لتفهمك، **adhm0127** ❤️"""
        
        await channel.send(detailed_welcome)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    embed = discord.Embed(
        title="⚔️ Flaron Mc | نظام التذاكر",
        description="يرجى الضغط على الزر أدناه لفتح تذكرة جديدة.",
        color=discord.Color.dark_gray()
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/1522296835706847365/1527005566038310962/Picsart_26-07-15_20-33-44-745.jpg")
    await ctx.send(embed=embed, view=TicketView())

@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(TicketActionsView())
    print(f'البوت {bot.user} متصل الآن!')

# تشغيل البوت باستخدام المتغير البيئي
bot.run(os.environ['TOKEN'])