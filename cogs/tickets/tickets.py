# cogs/tickets/tickets.py
import discord
from discord.ext import commands
import asyncio
import re
from datetime import datetime
import sys
import os

# إضافة المجلد الرئيسي للمشروع إلى sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# الآن استورد config و database
from config import COLORS, EMOJIS
import database as db

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_tickets = {}
        self.panel_message_id = None
        self.panel_channel_id = None
    
    # ========== أوامر الإعداد ==========
    @commands.group(name="ticket", aliases=["t"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def ticket(self, ctx):
        embed = discord.Embed(
            title="🎫 Ticket System",
            description="**Commands:**\n"
                       "`!ticket setup` - Setup ticket system\n"
                       "`!ticket panel` - Send ticket panel\n"
                       "`!ticket logs #channel` - Set logs channel\n"
                       "`!ticket staff @role` - Set staff role\n"
                       "`!ticket category <id>` - Set ticket category by ID",
            color=COLORS["info"]
        )
        await ctx.send(embed=embed, delete_after=15)
    
    @ticket.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def ticket_setup(self, ctx):
        category = discord.utils.get(ctx.guild.categories, name="TICKETS")
        if not category:
            category = await ctx.guild.create_category("TICKETS")
        await db.set_ticket_category(ctx.guild.id, category.id)
        embed = discord.Embed(
            title="✅ Ticket System Setup",
            description=f"**Category:** {category.mention}\n\nUse `!ticket panel` to send the ticket panel.",
            color=COLORS["success"]
        )
        await ctx.send(embed=embed, delete_after=10)
    
    @ticket.command(name="panel")
    @commands.has_permissions(administrator=True)
    async def ticket_panel(self, ctx, channel: discord.TextChannel = None):
        if not channel:
            channel = ctx.channel
        
        self.panel_channel_id = channel.id
        
        embed = discord.Embed(
            title="505 Ticket System",
            description="Welcome to 505 Services  !\n\nPlease select a ticket type below to create a support ticket.",
            color=COLORS["info"]
        )
        embed.set_image(url="https://media.discordapp.net/attachments/1481632627558715565/1485515148478120116/file_000000002a44720aa8ea74a5d90c8596.png?ex=69c41f8a&is=69c2ce0a&hm=9b9b0b3eb6a02a866c2015799ac782c343ab938f47c8147bc54dd6667214bedb&=&format=webp&quality=lossless&width=1664&height=902")
        embed.set_footer(text="Drive 505 | Made by Saivy")
        
        view = discord.ui.View(timeout=None)
        
        buttons = ["Inquiry", "Suggestion", "Complaint", "Staff Apply", "Verification", "Help"]
        
        for label in buttons:
            custom_id = label.lower().replace(" ", "_")
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label=label, custom_id=f"ticket_{custom_id}"))
        
        msg = await channel.send(embed=embed, view=view)
        self.panel_message_id = msg.id
        await ctx.send(f"✅ Ticket panel sent to {channel.mention}", delete_after=5)
    
    @ticket.command(name="logs")
    @commands.has_permissions(administrator=True)
    async def ticket_logs(self, ctx, channel: discord.TextChannel):
        await db.set_ticket_logs(ctx.guild.id, channel.id)
        await ctx.send(f"✅ Ticket logs set to {channel.mention}", delete_after=5)
    
    @ticket.command(name="staff")
    @commands.has_permissions(administrator=True)
    async def ticket_staff(self, ctx, role: discord.Role):
        await db.set_ticket_staff_role(ctx.guild.id, role.id)
        await ctx.send(f"✅ Staff role set to {role.mention}", delete_after=5)
    
    @ticket.command(name="category")
    @commands.has_permissions(administrator=True)
    async def ticket_category(self, ctx, category_id: str):
        try:
            category_id_int = int(category_id)
            category = ctx.guild.get_channel(category_id_int)
            if category and isinstance(category, discord.CategoryChannel):
                await db.set_ticket_category(ctx.guild.id, category.id)
                await ctx.send(f"✅ Ticket category set to {category.name} (`{category.id}`)", delete_after=5)
            else:
                await ctx.send("❌ Invalid category ID! Please provide a valid category ID.", delete_after=5)
        except ValueError:
            await ctx.send("❌ Please provide a valid category ID (numbers only).", delete_after=5)
    
    # ========== إنشاء التذكرة ==========
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.type == discord.InteractionType.component:
            return
        
        custom_id = interaction.data["custom_id"]
        
        if custom_id.startswith("ticket_"):
            ticket_type = custom_id.split("_")[1]
            for t_id, data in self.active_tickets.items():
                if data["user_id"] == interaction.user.id:
                    await interaction.response.send_message("❌ You already have an open ticket!", ephemeral=True)
                    return
            await self.create_ticket(interaction, ticket_type)
        
        elif custom_id.startswith("accept_"):
            ticket_id = int(custom_id.split("_")[1])
            await self.accept_ticket(interaction, ticket_id)
        
        elif custom_id.startswith("close_"):
            ticket_id = int(custom_id.split("_")[1])
            await self.close_ticket(interaction, ticket_id)
        
        elif custom_id.startswith("invite_"):
            ticket_id = int(custom_id.split("_")[1])
            await self.invite_user(interaction, ticket_id)
        
        elif custom_id.startswith("rate_"):
            parts = custom_id.split("_")
            ticket_id = int(parts[1])
            rating = int(parts[2])
            await self.save_rating(interaction, ticket_id, rating)
    
    async def create_ticket(self, interaction, ticket_type):
        category_id = await db.get_ticket_category(interaction.guild.id)
        staff_role_id = await db.get_ticket_staff_role(interaction.guild.id)
        
        if not category_id:
            await interaction.response.send_message("❌ Ticket system not set up! Contact an admin.", ephemeral=True)
            return
        
        category = interaction.guild.get_channel(int(category_id))
        staff_role = interaction.guild.get_role(int(staff_role_id)) if staff_role_id else None
        
        type_names = {
            "inquiry": "inquiry", "suggestion": "suggestion", "complaint": "complaint",
            "staff_apply": "staff-apply", "verification": "verification", "help": "help"
        }
        
        ticket_name = f"{type_names.get(ticket_type, 'ticket')}-{interaction.user.name}"
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        
        channel = await interaction.guild.create_text_channel(
            name=ticket_name, category=category, overwrites=overwrites,
            reason=f"Ticket created by {interaction.user}"
        )
        
        ticket_id = len(self.active_tickets) + 1
        self.active_tickets[ticket_id] = {
            "channel_id": channel.id, "user_id": interaction.user.id,
            "ticket_type": ticket_type, "staff_id": None,
            "created_at": datetime.now(), "transcript": []
        }
        
        await self.send_ticket_message(channel, interaction.user, ticket_type, ticket_id, staff_role)
        await interaction.response.send_message(f"✅ Ticket created! {channel.mention}", ephemeral=True)
        await self.log_ticket_created(interaction.guild, interaction.user, ticket_type, ticket_id)
    
    async def send_ticket_message(self, channel, user, ticket_type, ticket_id, staff_role):
        type_icons = {"inquiry": "📋", "suggestion": "💡", "complaint": "⚠️", "staff_apply": "👑", "verification": "✅", "help": "❓"}
        
        embed = discord.Embed(
            title=f"{type_icons.get(ticket_type, '🎫')} Ticket #{ticket_id} - {ticket_type.title()}",
            description=f"**Created by:** {user.mention}\n**Type:** {ticket_type.title()}\n\nPlease describe your issue and staff will assist you shortly.",
            color=COLORS["info"]
        )
        
        # صورة في التذكرة
        embed.set_image(url="https://cdn.discordapp.com/attachments/1444544689092038666/1485578853756829809/IMG_20260323_104525.png?ex=69c3b21f&is=69c2609f&hm=d599a4cde606a75739cb450d3fc17209430399cdbabada81fa062ff594b03472&")
        
        embed.set_footer(text=f"Ticket ID: {ticket_id}")
        
        view = discord.ui.View(timeout=None)
        
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label="Accept", custom_id=f"accept_{ticket_id}"))
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label="Close", custom_id=f"close_{ticket_id}"))
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label="Invite", custom_id=f"invite_{ticket_id}"))
        
        staff_mention = staff_role.mention if staff_role else "@here"
        await channel.send(f"{staff_mention} {user.mention}", embed=embed, view=view)
    
    async def accept_ticket(self, interaction, ticket_id):
        if ticket_id not in self.active_tickets:
            await interaction.response.send_message("❌ Ticket not found!", ephemeral=True)
            return
        
        data = self.active_tickets[ticket_id]
        channel = interaction.guild.get_channel(data["channel_id"])
        
        if not channel:
            await interaction.response.send_message("❌ Ticket channel not found!", ephemeral=True)
            return
        
        data["staff_id"] = interaction.user.id
        
        embed = discord.Embed(title="✅ Ticket Accepted", description=f"**Accepted by:** {interaction.user.mention}\n\nStaff will assist you shortly.", color=COLORS["success"])
        await channel.send(embed=embed)
        await interaction.response.send_message("✅ Ticket accepted!", ephemeral=True)
        await self.log_ticket_accepted(interaction.guild, interaction.user, ticket_id)
    
    async def close_ticket(self, interaction, ticket_id):
        if ticket_id not in self.active_tickets:
            await interaction.response.send_message("❌ Ticket not found!", ephemeral=True)
            return
        
        data = self.active_tickets[ticket_id]
        channel = interaction.guild.get_channel(data["channel_id"])
        user = interaction.guild.get_member(data["user_id"])
        
        transcript = await self.get_transcript(channel)
        
        if user:
            await self.send_rating(user, ticket_id)
        
        await interaction.response.send_message("🔒 Closing ticket in 5 seconds...", ephemeral=True)
        await asyncio.sleep(5)
        
        if channel:
            await channel.delete(reason=f"Ticket closed by {interaction.user}")
        
        await self.log_ticket_closed(interaction.guild, interaction.user, ticket_id, transcript)
        del self.active_tickets[ticket_id]
    
    async def invite_user(self, interaction, ticket_id):
        if ticket_id not in self.active_tickets:
            await interaction.response.send_message("❌ Ticket not found!", ephemeral=True)
            return
        
        data = self.active_tickets[ticket_id]
        channel = interaction.guild.get_channel(data["channel_id"])
        
        if not channel:
            await interaction.response.send_message("❌ Ticket channel not found!", ephemeral=True)
            return
        
        modal = discord.ui.Modal(title="Invite User")
        user_input = discord.ui.TextInput(label="User ID or Mention", placeholder="Enter user ID or mention...", required=True)
        modal.add_item(user_input)
        
        async def on_submit(i):
            user_id = re.sub(r'[<@!>]', '', user_input.value)
            if user_id.isdigit():
                user = await interaction.guild.fetch_member(int(user_id))
                if user:
                    await channel.set_permissions(user, view_channel=True, send_messages=True, read_message_history=True)
                    await i.response.send_message(f"✅ {user.mention} has been added!", ephemeral=True)
                    await channel.send(f"👋 {user.mention} has been added by {interaction.user.mention}")
                else:
                    await i.response.send_message("❌ User not found!", ephemeral=True)
            else:
                await i.response.send_message("❌ Invalid user ID!", ephemeral=True)
        
        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)
    
    async def send_rating(self, user, ticket_id):
        embed = discord.Embed(
            title="📝 Rate Your Support Experience",
            description=f"Thank you for using our ticket system!\n\nPlease rate your experience with ticket **#{ticket_id}**.",
            color=COLORS["info"]
        )
        
        view = discord.ui.View(timeout=60)
        ratings = [("⭐ 1", "1"), ("⭐⭐ 2", "2"), ("⭐⭐⭐ 3", "3"), ("⭐⭐⭐⭐ 4", "4"), ("⭐⭐⭐⭐⭐ 5", "5")]
        
        for label, value in ratings:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label=label, custom_id=f"rate_{ticket_id}_{value}"))
        
        await user.send(embed=embed, view=view)
    
    async def save_rating(self, interaction, ticket_id, rating):
        embed = discord.Embed(title="✅ Rating Saved", description=f"Thank you for rating ticket **#{ticket_id}** with **{rating} stars**!", color=COLORS["success"])
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        logs_channel_id = await db.get_ticket_logs(interaction.guild.id)
        if logs_channel_id:
            logs_channel = interaction.guild.get_channel(int(logs_channel_id))
            if logs_channel:
                rating_embed = discord.Embed(title="⭐ Ticket Rating", description=f"**Ticket ID:** #{ticket_id}\n**Rating:** {rating} stars\n**User:** {interaction.user.mention}", color=COLORS["success"])
                await logs_channel.send(embed=rating_embed)
    
    async def get_transcript(self, channel):
        transcript = []
        if channel:
            async for message in channel.history(limit=200, oldest_first=True):
                transcript.append({
                    "author": str(message.author), "content": message.content,
                    "timestamp": message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                })
        return transcript
    
    async def log_ticket_created(self, guild, user, ticket_type, ticket_id):
        logs_id = await db.get_ticket_logs(guild.id)
        if logs_id:
            logs = guild.get_channel(int(logs_id))
            if logs:
                embed = discord.Embed(title="🎫 Ticket Created", description=f"**User:** {user.mention}\n**Type:** {ticket_type.title()}\n**ID:** #{ticket_id}", color=COLORS["success"])
                await logs.send(embed=embed)
    
    async def log_ticket_accepted(self, guild, staff, ticket_id):
        logs_id = await db.get_ticket_logs(guild.id)
        if logs_id:
            logs = guild.get_channel(int(logs_id))
            if logs:
                embed = discord.Embed(title="✅ Ticket Accepted", description=f"**Staff:** {staff.mention}\n**ID:** #{ticket_id}", color=COLORS["success"])
                await logs.send(embed=embed)
    
    async def log_ticket_closed(self, guild, closer, ticket_id, transcript):
        logs_id = await db.get_ticket_logs(guild.id)
        if logs_id:
            logs = guild.get_channel(int(logs_id))
            if logs:
                embed = discord.Embed(title="🔒 Ticket Closed", description=f"**Closed by:** {closer.mention}\n**ID:** #{ticket_id}", color=COLORS["warning"])
                await logs.send(embed=embed)
                
                if transcript:
                    transcript_text = "\n".join([f"[{msg['timestamp']}] {msg['author']}: {msg['content']}" for msg in transcript])
                    import io
                    file = discord.File(io.StringIO(transcript_text), filename=f"ticket_{ticket_id}.txt")
                    await logs.send(f"📝 Transcript for ticket #{ticket_id}", file=file)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        for t_id, data in self.active_tickets.items():
            if data["channel_id"] == message.channel.id:
                data["transcript"].append({
                    "author": str(message.author), "content": message.content,
                    "timestamp": message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                })
                break

async def setup(bot):
    bot.add_cog(TicketSystem(bot))