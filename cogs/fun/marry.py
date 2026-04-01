# cogs/fun/marry.py
import discord
from discord.ext import commands
import random
import asyncio
from config import COLORS, EMOJIS
from utils.helpers import get_member, send_permanent
from utils.embeds import error_embed
from utils.checks import check_permission
import database as db

class Marry(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_requests = {}  # {user_id: {"partner": partner_id, "ctx": ctx}}
        self.gifs = {
            "marry": "https://media.tenor.com/6D6v0JlU1LkAAAAi/marry-me-marry.gif",
            "request_marry": "https://media.tenor.com/8XJmNqV0YkQAAAAi/proposal-marry.gif"
        }
    
    @commands.command(name="marry", aliases=["ارتبط"])
    @check_permission("marry")
    async def marry(self, ctx, *, user_input=None):
        """الارتباط بشخص - !marry @user أو ريبلاي"""
        
        partner = await get_member(ctx, user_input)
        
        if not partner:
            await send_permanent(ctx, error_embed("Invalid User", "Please mention someone to marry, reply to their message, or provide an ID."))
            return
        
        if partner == ctx.author:
            await send_permanent(ctx, error_embed("Cannot Marry", "You cannot marry yourself!"))
            return
        
        # التحقق من أن الشخص غير مرتبط
        existing_marriage = await db.get_married(ctx.author.id, ctx.guild.id)
        if existing_marriage:
            await send_permanent(ctx, error_embed("Already Married", f"You are already married to <@{existing_marriage}>."))
            return
        
        existing_partner_marriage = await db.get_married(partner.id, ctx.guild.id)
        if existing_partner_marriage:
            await send_permanent(ctx, error_embed("Partner Already Married", f"{partner.mention} is already married to someone else."))
            return
        
        # إرسال طلب الزواج
        await self.send_marry_request(ctx, partner)
    
    async def send_marry_request(self, ctx, partner):
        """إرسال طلب زواج مع أزرار قبول ورفض"""
        
        embed = discord.Embed(
            title=f"{EMOJIS['request_marry']} Marriage Request!",
            description=f"{ctx.author.mention} wants to marry {partner.mention}!\n\nDo you accept?",
            color=COLORS["info"]
        )
        embed.set_image(url=self.gifs["request_marry"])
        embed.set_footer(text="You have 60 seconds to respond")
        
        # أزرار القبول والرفض
        view = discord.ui.View(timeout=60)
        accept_button = discord.ui.Button(style=discord.ButtonStyle.success, label="Accept", emoji="💍", custom_id=f"marry_accept_{ctx.author.id}_{partner.id}")
        reject_button = discord.ui.Button(style=discord.ButtonStyle.danger, label="Reject", emoji="❌", custom_id=f"marry_reject_{ctx.author.id}_{partner.id}")
        view.add_item(accept_button)
        view.add_item(reject_button)
        
        # تخزين الطلب
        self.pending_requests[f"{ctx.author.id}_{partner.id}"] = {
            "requester": ctx.author.id,
            "target": partner.id,
            "ctx": ctx,
            "channel": ctx.channel
        }
        
        # إرسال الطلب في الشات
        await ctx.send(embed=embed, view=view)
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.type == discord.InteractionType.component:
            return
        
        custom_id = interaction.data["custom_id"]
        
        # معالجة طلب الزواج
        if custom_id.startswith("marry_accept_"):
            parts = custom_id.split("_")
            requester_id = int(parts[2])
            target_id = int(parts[3])
            
            # التحقق من أن المستخدم هو المستهدف
            if interaction.user.id != target_id:
                await interaction.response.send_message("❌ This request is not for you!", ephemeral=True)
                return
            
            # التحقق من أن الطلب لا يزال موجود
            request_key = f"{requester_id}_{target_id}"
            if request_key not in self.pending_requests:
                await interaction.response.send_message("❌ This request has expired!", ephemeral=True)
                return
            
            # التحقق من أن المستخدمين غير مرتبطين
            existing_marriage = await db.get_married(requester_id, interaction.guild.id)
            if existing_marriage:
                await interaction.response.send_message("❌ The requester is already married!", ephemeral=True)
                return
            
            existing_partner_marriage = await db.get_married(target_id, interaction.guild.id)
            if existing_partner_marriage:
                await interaction.response.send_message("❌ You are already married!", ephemeral=True)
                return
            
            # تنفيذ الزواج
            await db.marry(requester_id, target_id, interaction.guild.id)
            
            # إزالة الطلب
            del self.pending_requests[request_key]
            
            # رسالة النجاح
            requester = interaction.guild.get_member(requester_id)
            target = interaction.guild.get_member(target_id)
            
            messages = [
                "Congratulations! May your love last forever! 💕",
                "What a beautiful couple! 🥰",
                "Love is in the air! 💘",
                "A match made in heaven! 👰🤵"
            ]
            
            embed = discord.Embed(
                title=f"{EMOJIS['marry']} Congratulations! 🎉",
                description=f"{requester.mention} and {target.mention} are now married!\n\n*{random.choice(messages)}*",
                color=COLORS["success"]
            )
            embed.set_image(url=self.gifs["marry"])
            
            await interaction.response.send_message(embed=embed)
        
        elif custom_id.startswith("marry_reject_"):
            parts = custom_id.split("_")
            requester_id = int(parts[2])
            target_id = int(parts[3])
            
            # التحقق من أن المستخدم هو المستهدف
            if interaction.user.id != target_id:
                await interaction.response.send_message("❌ This request is not for you!", ephemeral=True)
                return
            
            # إزالة الطلب
            request_key = f"{requester_id}_{target_id}"
            if request_key in self.pending_requests:
                del self.pending_requests[request_key]
            
            requester = interaction.guild.get_member(requester_id)
            
            embed = discord.Embed(
                title="💔 Marriage Request Rejected",
                description=f"{requester.mention}, {interaction.user.mention} has rejected your marriage proposal.",
                color=COLORS["error"]
            )
            
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Marry(bot))