# cogs/fun.py
import discord
from discord.ext import commands
from config import EMOJIS
from utils import embeds, checks
import database as db
import random

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gifs = {
            "marry": "https://media.tenor.com/6D6v0JlU1LkAAAAi/marry-me-marry.gif",
            "goodnight": "https://media.tenor.com/0t-dKzVlKhwAAAAi/goodnight-gif.gif",
            "ez": "https://media.tenor.com/xT5I5m5l2GgAAAAi/ez.gif"
        }
    
    async def get_member(self, ctx, user_input=None):
        """جلب العضو من منشن أو ريبلاي أو ID"""
        if ctx.message.reference and not user_input:
            msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            return msg.author
        
        if user_input:
            try:
                if user_input.isdigit():
                    return await ctx.guild.fetch_member(int(user_input))
                return await commands.MemberConverter().convert(ctx, user_input)
            except:
                return None
        return None
    
    # ========== أمر MARRY ==========
    @commands.command(name="marry", aliases=["ارتبط"])
    async def marry(self, ctx, *, user_input=None):
        """الارتباط بشخص - !marry @user"""
        partner = await self.get_member(ctx, user_input)
        
        if not partner:
            return await ctx.send(embed=embeds.error_embed("Invalid User", "Please mention someone to marry, reply to their message, or provide an ID."))
        
        if partner == ctx.author:
            return await ctx.send(embed=embeds.error_embed("Cannot Marry", "You cannot marry yourself!"))
        
        # التحقق من أن الشخص غير مرتبط بالفعل
        existing_marriage = await db.get_married(ctx.author.id, ctx.guild.id)
        if existing_marriage:
            return await ctx.send(embed=embeds.error_embed("Already Married", f"You are already married to <@{existing_marriage}>."))
        
        existing_partner_marriage = await db.get_married(partner.id, ctx.guild.id)
        if existing_partner_marriage:
            return await ctx.send(embed=embeds.error_embed("Partner Already Married", f"{partner.mention} is already married to someone else."))
        
        # إضافة الزواج
        await db.marry(ctx.author.id, partner.id, ctx.guild.id)
        
        embed = discord.Embed(
            title=f"{EMOJIS['marry']} Congratulations! 🎉",
            description=f"{ctx.author.mention} and {partner.mention} are now married!",
            color=discord.Color.pink()
        )
        embed.set_image(url=self.gifs["marry"])
        embed.set_footer(text="May your love last forever!")
        
        await ctx.send(embed=embed)
    
    # ========== أمر DIVORCE ==========
    @commands.command(name="divorce", aliases=["طلاق"])
    async def divorce(self, ctx):
        """الطلاق - !divorce"""
        partner_id = await db.get_married(ctx.author.id, ctx.guild.id)
        
        if not partner_id:
            return await ctx.send(embed=embeds.error_embed("Not Married", "You are not married to anyone."))
        
        partner = ctx.guild.get_member(int(partner_id))
        partner_name = partner.mention if partner else f"<@{partner_id}>"
        
        await db.divorce(ctx.author.id, ctx.guild.id)
        
        embed = embeds.warning_embed(
            "Divorced 💔",
            f"{ctx.author.mention} and {partner_name} are now divorced."
        )
        await ctx.send(embed=embed)
    
    # ========== أمر GOODNIGHT ==========
    @commands.command(name="goodnight", aliases=["gn", "تصبح_على_خير"])
    async def goodnight(self, ctx, *, user_input=None):
        """أتمنى تصبح على خير - !goodnight @user"""
        target = await self.get_member(ctx, user_input)
        
        if not target:
            target = ctx.author
        
        messages = [
            "Good night! Sleep tight! 🌙",
            "Sweet dreams! 💫",
            "Sleep well and wake up refreshed! 😴",
            "May your dreams be beautiful! ✨",
            "Rest well, tomorrow is a new day! 🌅"
        ]
        
        embed = discord.Embed(
            title=f"{EMOJIS['marry']} Goodnight!",
            description=f"{ctx.author.mention} wishes {target.mention} a good night!\n\n*{random.choice(messages)}*",
            color=discord.Color.dark_blue()
        )
        embed.set_image(url=self.gifs["goodnight"])
        
        await ctx.send(embed=embed)
    
    # ========== أمر EZ (ترول) ==========
    @commands.command(name="ez", aliases=["ارزع"])
    @commands.has_permissions(administrator=True)
    @checks.admin_only()
    async def ez(self, ctx, *, user_input=None):
        """أمر ترول - !ez @user (يحتاج تأكيد)"""
        target = await self.get_member(ctx, user_input)
        
        if not target:
            return await ctx.send(embed=embeds.error_embed("Invalid User", "Please mention someone to use this on, reply to their message, or provide an ID."))
        
        if target == ctx.author:
            return await ctx.send(embed=embeds.error_embed("Cannot EZ", "You cannot use this on yourself!"))
        
        # نظام التأكيد
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == "!ez"
        
        confirm_embed = discord.Embed(
            title=f"{EMOJIS['warning']} Confirmation Required",
            description=f"Are you sure you want to use `!ez` on {target.mention}?\nType `!ez` again within 10 seconds to confirm.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=confirm_embed)
        
        try:
            await self.bot.wait_for("message", timeout=10.0, check=check)
            
            # تنفيذ الأمر
            embed = discord.Embed(
                title=f"{EMOJIS['warning']} EZ!",
                description=f"{ctx.author.mention} just demolished {target.mention}! Get rekt! 🎯",
                color=discord.Color.red()
            )
            embed.set_image(url=self.gifs.get("ez", "https://media.tenor.com/xT5I5m5l2GgAAAAi/ez.gif"))
            
            await ctx.send(embed=embed)
            
        except TimeoutError:
            await ctx.send(embed=embeds.error_embed("Cancelled", "Command cancelled. No confirmation received."))
    
    # ========== أمر SET GIF (تخصيص الـ GIF) ==========
    @commands.command(name="setgif", aliases=["تعيين_جيف"])
    @commands.has_permissions(administrator=True)
    @checks.admin_only()
    async def set_gif(self, ctx, command_name=None, *, gif_url=None):
        """تخصيص GIF لأمر - !setgif marry https://gif.link"""
        if not command_name or not gif_url:
            return await ctx.send(embed=embeds.error_embed("Missing Arguments", "Usage: `!setgif <command> <gif_url>`\nCommands: marry, goodnight, ez"))
        
        if command_name.lower() not in self.gifs:
            return await ctx.send(embed=embeds.error_embed("Invalid Command", f"Command must be one of: {', '.join(self.gifs.keys())}"))
        
        self.gifs[command_name.lower()] = gif_url
        
        embed = embeds.success_embed(
            "GIF Updated",
            f"GIF for `{command_name}` has been updated successfully."
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))