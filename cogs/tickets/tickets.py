# cogs/tickets/tickets.py
import asyncio
import html
import io
import os
import re
import sys
from datetime import datetime, timezone

import aiohttp
import discord
from discord.ext import commands

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import config
from config import COLORS
import database as db

CLAIM_ROLE_ID = 1485557337677889658
ADMIN_COMMAND_ROLE_ID = int(getattr(config, "STAFF_ROLE", "1485545225802875002"))
NEUTRAL_COLOR = 0x2B2D31
PANEL_IMAGE_URL = "https://cdn.discordapp.com/attachments/1489434130683789523/1496424212720648352/Untitled-2.png?ex=69ef1b26&is=69edc9a6&hm=f7a4c011da0432aeff95e8bc25c131a3b46f01d8f7d1913e553ff0591c9a60be&"
TICKET_IMAGE_URL = "https://cdn.discordapp.com/attachments/1444544689092038666/1485578853756829809/IMG_20260323_104525.png?ex=69c3b21f&is=69c2609f&hm=d599a4cde606a75739cb450d3fc17209430399cdbabada81fa062ff594b03472&"

ORDER_OPENING_TEXT = """**Welcome ** <a:aesthetic:1497939159891968223> 
Please clearly explain your request in general, and one of our team members will contact you.

Important Notice:<:14532857869539779861:1496401136045789194> 

*- Contact outside the ticket is strictly prohibited for any reason.
- Do not share any sensitive information such as tokens, passwords, or email addresses.*
**For your safety, please make sure to follow the instructions.** <:14257006539379835191:1496377302496444496>"""

PANEL_CONFIGS = {
    "normal": {
        "title": "505 Ticket System",
        "description": "Welcome to 505 Services!\n\nPlease select a ticket type below to create a support ticket.",
        "buttons": ["Inquiry", "Suggestion", "Complaint", "Staff Apply", "Verification", "Help"],
    },
    "order": {
        "title": "505 Order System",
        "description": "Welcome to 505 Services!\n\nClick the button below to create an order ticket.",
        "buttons": ["Create Order"],
    },
    "help": {
        "title": "505 Help System",
        "description": "Welcome to 505 Services!\n\nClick the button below to create a help ticket.",
        "buttons": ["Create Help"],
    },
}

NORMAL_TYPES = ["inquiry", "suggestion", "complaint", "staff_apply", "verification"]
TICKET_KIND_TYPES = {
    "normal": NORMAL_TYPES,
    "order": ["order"],
    "help": ["help"],
}
TICKET_TYPE_NAMES = {
    "inquiry": "inquiry",
    "suggestion": "suggestion",
    "complaint": "complaint",
    "staff_apply": "staff-apply",
    "verification": "verification",
    "help": "help",
    "order": "order",
}
PURCHASE_KEYWORDS = (
    "price", "prices", "pricing", "buy", "purchase", "payment", "payments", "cost", "order",
    "nitro", "token", "tokens", "subscription", "subscribe", "plan", "plans", "invoice",
    "سعر", "اسعار", "أسعار", "بكام", "اشتري", "شراء", "عايز", "طلب",
    "اوردر", "أوردر", "نيترو", "بوت", "ادفع", "دفع", "حجز",
)

SYSTEM_PROMPT = (
    "You are a temporary AI support helper inside one Discord ticket. "
    "Answer only using the current ticket context. Do not mix users or tickets. "
    "Keep replies short: 1 to 4 short lines, no long essays. "
    "Reply in the same language as the customer when possible. "
    "Ask at most one question at a time. "
    "Never ask for passwords, tokens, emails, or sensitive information. "
    "If the customer asks about prices, buying, payments, Nitro, bot orders, tokens, or subscriptions, "
    "be helpful but do not invent prices. Tell them their request is understood and staff/owner will confirm details."
)


class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_tasks = {}
        self.ai_busy_channels = set()
        self.resume_task = None

    async def cog_load(self):
        self.resume_task = asyncio.create_task(self._resume_ai_timers())

    def cog_unload(self):
        if self.resume_task:
            self.resume_task.cancel()
        for task in self.ai_tasks.values():
            task.cancel()

    def _is_claim_staff(self, member: discord.Member) -> bool:
        return member.guild_permissions.administrator or any(role.id == CLAIM_ROLE_ID for role in getattr(member, "roles", []))

    def _is_admin_command_staff(self, member: discord.Member) -> bool:
        return member.guild_permissions.administrator or any(role.id == ADMIN_COMMAND_ROLE_ID for role in getattr(member, "roles", []))

    async def _require_ticket_config_permission(self, ctx) -> bool:
        if isinstance(ctx.author, discord.Member) and self._is_admin_command_staff(ctx.author):
            return True
        await ctx.send("Only Administrators or the admin-commands role can use this command.", delete_after=8)
        return False

    def _ticket_kind(self, ticket_type: str) -> str:
        if ticket_type == "order":
            return "order"
        if ticket_type == "help":
            return "help"
        return "normal"

    def _ticket_types_for_kind(self, kind: str):
        return TICKET_KIND_TYPES.get(kind, NORMAL_TYPES)

    def _parse_duration(self, value: str):
        if not value:
            return None
        value = value.strip().lower()
        match = re.fullmatch(r"(\d+)(s|m|h|d)?", value)
        if not match:
            return None
        amount = int(match.group(1))
        unit = match.group(2) or "s"
        multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
        seconds = amount * multiplier
        return max(1, min(seconds, 7 * 86400))

    def _human_duration(self, seconds: int) -> str:
        seconds = int(seconds)
        if seconds % 86400 == 0:
            return f"{seconds // 86400}d"
        if seconds % 3600 == 0:
            return f"{seconds // 3600}h"
        if seconds % 60 == 0:
            return f"{seconds // 60}m"
        return f"{seconds}s"

    def _clean_channel_name(self, text: str) -> str:
        text = (text or "user").lower()
        text = re.sub(r"[^a-z0-9_-]+", "-", text)
        text = re.sub(r"-+", "-", text).strip("-")
        return text[:40] or "user"

    def _build_ticket_view(self, ticket_id: int, mode: str = "unclaimed"):
        if mode == "closed":
            return self._build_closed_view(ticket_id)
        view = discord.ui.View(timeout=None)
        if mode == "claimed":
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label="Claimed", custom_id=f"claimed_{ticket_id}", disabled=True))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label="Change Staff", custom_id=f"change_staff_{ticket_id}"))
        elif mode == "ai":
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label="AI Active", custom_id=f"ai_active_{ticket_id}", disabled=True))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label="Change Staff", custom_id=f"change_staff_{ticket_id}"))
        else:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label="Claim", custom_id=f"claim_{ticket_id}"))
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label="Close", custom_id=f"close_{ticket_id}"))
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label="Invite", custom_id=f"invite_{ticket_id}"))
        return view

    def _build_closed_view(self, ticket_id: int):
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.success, label="Open", custom_id=f"reopen_{ticket_id}"))
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.danger, label="Delete", custom_id=f"delete_{ticket_id}"))
        return view

    def _apply_status_to_embed(self, embed: discord.Embed, status: str, responsible: str, color: int = NEUTRAL_COLOR):
        new_embed = embed.copy()
        new_embed.clear_fields()
        new_embed.add_field(name="Status", value=status, inline=True)
        new_embed.add_field(name="Responsible", value=responsible, inline=True)
        try:
            new_embed.color = discord.Color(color)
        except Exception:
            pass
        return new_embed


    async def _send_ephemeral(self, interaction: discord.Interaction, content: str):
        try:
            if interaction.response.is_done():
                await interaction.followup.send(content, ephemeral=True)
            else:
                await interaction.response.send_message(content, ephemeral=True)
        except (discord.NotFound, discord.HTTPException):
            pass

    async def _defer_ephemeral(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True, thinking=True)
        except (discord.NotFound, discord.HTTPException):
            pass

    async def _get_ticket_record(self, ticket_id: int):
        return await db.get_active_ticket(ticket_id)

    async def _safe_get_ticket_channel(self, guild: discord.Guild, ticket_id: int):
        data = await self._get_ticket_record(ticket_id)
        if not data:
            return None, None
        channel = guild.get_channel(int(data[2]))
        if not channel:
            await db.delete_active_ticket(ticket_id)
            self._cancel_ai_timer(ticket_id)
            return data, None
        return data, channel

    async def _fetch_ticket_message(self, channel: discord.TextChannel, data):
        message_id = data[7] if len(data) > 7 else None
        if message_id:
            try:
                return await channel.fetch_message(int(message_id))
            except (discord.NotFound, discord.Forbidden, discord.HTTPException, ValueError):
                pass
        async for message in channel.history(limit=60, oldest_first=True):
            if message.author == self.bot.user and message.embeds:
                footer = message.embeds[0].footer.text or ""
                if footer.endswith(str(data[0])) or f"Ticket ID: {data[0]}" in footer:
                    await db.set_active_ticket_message(data[0], message.id)
                    return message
        return None

    async def _edit_ticket_message(self, guild: discord.Guild, ticket_id: int, status: str, responsible: str, mode: str, color: int = NEUTRAL_COLOR):
        data, channel = await self._safe_get_ticket_channel(guild, ticket_id)
        if not data or not channel:
            return
        message = await self._fetch_ticket_message(channel, data)
        if not message or not message.embeds:
            return
        embed = self._apply_status_to_embed(message.embeds[0], status, responsible, color)
        await message.edit(embed=embed, view=self._build_ticket_view(ticket_id, mode))

    async def _log(self, guild: discord.Guild, title: str, description: str, color: int = NEUTRAL_COLOR, file: discord.File = None):
        logs_id = await db.get_ticket_logs(guild.id)
        if not logs_id:
            return
        logs = guild.get_channel(int(logs_id))
        if not logs:
            return
        embed = discord.Embed(title=title, description=description, color=color)
        await logs.send(embed=embed, file=file, allowed_mentions=discord.AllowedMentions.none())

    @commands.group(name="ticket", aliases=["t"], invoke_without_command=True)
    async def ticket(self, ctx):
        if not await self._require_ticket_config_permission(ctx):
            return
        embed = discord.Embed(
            title="Ticket System",
            description=(
                "Commands:\n"
                "`!ticket setup normal/order/help [category]` - Set ticket category\n"
                "`!ticket panel normal/order/help [#channel]` - Send ticket panel\n"
                "`!ticket category normal/order/help CATEGORY_ID` - Set category by ID\n"
                "`!ticket archive CATEGORY_ID` - Set closed tickets category\n"
                "`!ticket logs #channel` - Set ticket logs channel\n"
                "`!ticket ratings #channel` - Set rating channel\n"
                "`!ticket staff @role` - Set ticket staff role\n"
                "`!ticket airoles @admin @owner` - Set AI escalation roles\n"
                "`!set-ai order 1m` / `!set-ai normal 2m` / `!set-ai help 1m` - Auto AI per type\n"
                "Inside a ticket: `Ai start` or `Ai stop`"
            ),
            color=NEUTRAL_COLOR,
        )
        await ctx.send(embed=embed, delete_after=35)

    @ticket.command(name="setup")
    async def ticket_setup(self, ctx, ticket_kind: str = "normal", category: discord.CategoryChannel = None):
        if not await self._require_ticket_config_permission(ctx):
            return
        ticket_kind = ticket_kind.lower()
        if ticket_kind not in PANEL_CONFIGS:
            await ctx.send("Type must be one of: `normal`, `order`, `help`", delete_after=8)
            return
        if category is None:
            default_name = "TICKETS" if ticket_kind == "normal" else f"{ticket_kind.upper()} TICKETS"
            category = discord.utils.get(ctx.guild.categories, name=default_name)
            if not category:
                category = await ctx.guild.create_category(default_name)
        await db.set_ticket_type_category(ctx.guild.id, ticket_kind, category.id)
        if ticket_kind == "normal":
            await db.set_ticket_category(ctx.guild.id, category.id)
        await ctx.send(f"`{ticket_kind}` tickets category set to {category.mention}", delete_after=10)

    @ticket.command(name="panel")
    async def ticket_panel(self, ctx, ticket_kind: str = "normal", channel: discord.TextChannel = None):
        if not await self._require_ticket_config_permission(ctx):
            return
        ticket_kind = ticket_kind.lower()
        if ticket_kind not in PANEL_CONFIGS:
            await ctx.send("Type must be one of: `normal`, `order`, `help`", delete_after=8)
            return
        channel = channel or ctx.channel
        cfg = PANEL_CONFIGS[ticket_kind]
        embed = discord.Embed(title=cfg["title"], description=cfg["description"], color=NEUTRAL_COLOR)
        embed.set_image(url=PANEL_IMAGE_URL)
        embed.set_footer(text="Drive 505 | Made by Saivy")
        view = discord.ui.View(timeout=None)
        for label in cfg["buttons"]:
            if ticket_kind == "order":
                custom_id = "ticket_order"
            elif ticket_kind == "help":
                custom_id = "ticket_help"
            else:
                custom_id = f"ticket_{label.lower().replace(' ', '_')}"
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label=label, custom_id=custom_id))
        await channel.send(embed=embed, view=view)
        await ctx.send(f"`{ticket_kind}` ticket panel sent to {channel.mention}", delete_after=5)

    @ticket.command(name="logs")
    async def ticket_logs(self, ctx, channel: discord.TextChannel):
        if not await self._require_ticket_config_permission(ctx):
            return
        await db.set_ticket_logs(ctx.guild.id, channel.id)
        await ctx.send(f"Ticket logs set to {channel.mention}", delete_after=5)

    @ticket.command(name="ratings", aliases=["rating", "ratechannel"])
    async def ticket_ratings(self, ctx, channel: discord.TextChannel):
        if not await self._require_ticket_config_permission(ctx):
            return
        await db.set_ticket_rating_channel(ctx.guild.id, channel.id)
        await ctx.send(f"Ticket ratings channel set to {channel.mention}", delete_after=5)

    @ticket.command(name="archive", aliases=["closedcategory", "closecategory"])
    async def ticket_archive(self, ctx, category_id: str = None):
        if not await self._require_ticket_config_permission(ctx):
            return
        if not category_id:
            await ctx.send("Usage: `!ticket archive CATEGORY_ID`", delete_after=8)
            return
        category_id = re.sub(r"[^0-9]", "", category_id)
        category = ctx.guild.get_channel(int(category_id)) if category_id else None
        if not isinstance(category, discord.CategoryChannel):
            await ctx.send("Invalid archive category ID.", delete_after=8)
            return
        await db.set_ticket_archive_category(ctx.guild.id, category.id)
        await ctx.send(f"Closed tickets archive category set to **{category.name}** (`{category.id}`)", delete_after=8)

    @ticket.command(name="staff")
    async def ticket_staff(self, ctx, role: discord.Role):
        if not await self._require_ticket_config_permission(ctx):
            return
        await db.set_ticket_staff_role(ctx.guild.id, role.id)
        await ctx.send(f"Staff role set to {role.mention}", delete_after=5)

    @ticket.command(name="airoles")
    async def ticket_airoles(self, ctx, admin_role: discord.Role, owner_role: discord.Role):
        if not await self._require_ticket_config_permission(ctx):
            return
        await db.set_ticket_ai_roles(ctx.guild.id, admin_role.id, owner_role.id)
        await ctx.send(f"AI escalation roles set to {admin_role.mention} and {owner_role.mention}", delete_after=8)

    @ticket.command(name="adminrole")
    async def ticket_adminrole(self, ctx, role: discord.Role):
        if not await self._require_ticket_config_permission(ctx):
            return
        await db.set_ticket_ai_roles(ctx.guild.id, admin_role_id=role.id)
        await ctx.send(f"AI admin role set to {role.mention}", delete_after=5)

    @ticket.command(name="ownerrole")
    async def ticket_ownerrole(self, ctx, role: discord.Role):
        if not await self._require_ticket_config_permission(ctx):
            return
        await db.set_ticket_ai_roles(ctx.guild.id, owner_role_id=role.id)
        await ctx.send(f"AI owner role set to {role.mention}", delete_after=5)

    @ticket.command(name="category")
    async def ticket_category(self, ctx, ticket_kind: str, category_id: str):
        if not await self._require_ticket_config_permission(ctx):
            return
        ticket_kind = ticket_kind.lower()
        if ticket_kind not in PANEL_CONFIGS:
            await ctx.send("Type must be one of: `normal`, `order`, `help`", delete_after=8)
            return
        category_id = re.sub(r"[^0-9]", "", str(category_id))
        category = ctx.guild.get_channel(int(category_id)) if category_id else None
        if not isinstance(category, discord.CategoryChannel):
            await ctx.send("Invalid category ID.", delete_after=5)
            return
        await db.set_ticket_type_category(ctx.guild.id, ticket_kind, category.id)
        if ticket_kind == "normal":
            await db.set_ticket_category(ctx.guild.id, category.id)
        await ctx.send(f"`{ticket_kind}` ticket category set to {category.name} (`{category.id}`)", delete_after=5)

    @commands.command(name="set-ai", aliases=["setai", "set_ai"])
    async def set_ai(self, ctx, ticket_kind: str = None, duration: str = None):
        if not isinstance(ctx.author, discord.Member) or not self._is_admin_command_staff(ctx.author):
            await ctx.send("Only Administrators or the admin-commands role can use `set-ai`.", delete_after=8)
            return
        if not ticket_kind or ticket_kind.lower() not in PANEL_CONFIGS:
            await ctx.send("Usage: `!set-ai order 1m`, `!set-ai normal 2m`, `!set-ai help 1m`, or `!set-ai order off`.", delete_after=12)
            return
        ticket_kind = ticket_kind.lower()
        if duration is None:
            current = await db.get_ticket_type_ai_delay(ctx.guild.id, ticket_kind)
            if current:
                await ctx.send(f"Auto AI for `{ticket_kind}` is `{self._human_duration(current)}`.", delete_after=10)
            else:
                await ctx.send(f"Auto AI for `{ticket_kind}` is disabled.", delete_after=10)
            return
        if duration.lower() in ("off", "stop", "disable", "0"):
            await db.set_ticket_type_ai_delay(ctx.guild.id, ticket_kind, None)
            await ctx.send(f"Auto AI disabled for `{ticket_kind}` tickets.", delete_after=10)
            await self._log(ctx.guild, "Auto AI Disabled", f"Type: `{ticket_kind}`\nBy: {ctx.author.mention}")
            return
        seconds = self._parse_duration(duration)
        if seconds is None:
            await ctx.send("Invalid duration. Examples: `30s`, `1m`, `2h`, `1d`.", delete_after=10)
            return
        await db.set_ticket_type_ai_delay(ctx.guild.id, ticket_kind, seconds)
        await ctx.send(f"Auto AI for `{ticket_kind}` tickets set to `{self._human_duration(seconds)}`.", delete_after=10)
        await self._log(ctx.guild, "Auto AI Updated", f"Type: `{ticket_kind}`\nDelay: `{self._human_duration(seconds)}`\nBy: {ctx.author.mention}")

    @commands.command(name="ai-time", aliases=["aitime", "ai_time"])
    async def ai_time(self, ctx, duration: str = None, channel: discord.TextChannel = None):
        if not isinstance(ctx.author, discord.Member) or not self._is_claim_staff(ctx.author):
            await ctx.send("Only the claim role or Administrators can use AI time.", delete_after=8)
            return
        if not duration:
            await ctx.send("Usage: `!ai-time 1m [#ticket]` or `!ai-time off [#ticket]`", delete_after=10)
            return
        channel = channel or ctx.channel
        record = await db.get_active_ticket_by_channel(ctx.guild.id, channel.id)
        if not record:
            await ctx.send("This channel is not a ticket.", delete_after=8)
            return
        if len(record) > 13 and record[13]:
            await ctx.send("This ticket is closed. Reopen it first.", delete_after=8)
            return
        ticket_id = int(record[0])
        if duration.lower() in ("off", "stop", "disable", "0"):
            self._cancel_ai_timer(ticket_id)
            await db.disable_ticket_ai(ticket_id)
            await self._edit_ticket_message(ctx.guild, ticket_id, "Unclaimed", "Waiting for staff", "unclaimed")
            await ctx.send(f"AI timer disabled for {channel.mention}.", delete_after=8)
            await self._log(ctx.guild, "AI Timer Disabled", f"Ticket #{ticket_id}\nBy: {ctx.author.mention}")
            return
        seconds = self._parse_duration(duration)
        if seconds is None:
            await ctx.send("Invalid duration. Examples: `30s`, `1m`, `2h`, `1d`.", delete_after=10)
            return
        await db.set_ticket_ai_delay(ticket_id, seconds)
        self._schedule_ai_timer(ticket_id, seconds)
        await ctx.send(f"AI will take ticket #{ticket_id} after `{self._human_duration(seconds)}` if nobody claims it.", delete_after=10)
        await self._log(ctx.guild, "AI Timer Set", f"Ticket #{ticket_id}\nDelay: {self._human_duration(seconds)}\nBy: {ctx.author.mention}")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if not isinstance(channel, discord.TextChannel):
            return
        record = await db.get_active_ticket_by_channel(channel.guild.id, channel.id)
        if record:
            self._cancel_ai_timer(int(record[0]))
            self.ai_busy_channels.discard(int(channel.id))
        await db.delete_active_ticket_by_channel(channel.guild.id, channel.id)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")
        try:
            if custom_id.startswith("rate_"):
                parts = custom_id.split("_")
                if len(parts) == 4:
                    await self.save_rating(interaction, int(parts[1]), int(parts[2]), int(parts[3]))
                return
            if not interaction.guild:
                return
            if custom_id.startswith("ticket_"):
                ticket_type = custom_id.replace("ticket_", "", 1)
                ticket_kind = self._ticket_kind(ticket_type)
                existing = await db.get_active_ticket_by_user_kind(
                    interaction.guild.id,
                    interaction.user.id,
                    self._ticket_types_for_kind(ticket_kind),
                )
                if existing:
                    old_channel = interaction.guild.get_channel(int(existing[1]))
                    if old_channel:
                        await interaction.response.send_message(
                            f"You already have an open `{ticket_kind}` ticket: {old_channel.mention}",
                            ephemeral=True,
                        )
                        return
                    await db.delete_active_ticket(existing[0])
                await self.create_ticket(interaction, ticket_type)
            elif custom_id.startswith("claim_ai_"):
                await self.claim_from_ai_prompt(interaction, int(custom_id.split("_")[2]))
            elif custom_id.startswith("claim_") or custom_id.startswith("accept_"):
                await self.accept_ticket(interaction, int(custom_id.split("_")[1]))
            elif custom_id.startswith("change_staff_"):
                await self.show_staff_select(interaction, int(custom_id.split("_")[2]))
            elif custom_id.startswith("select_staff_"):
                await self.select_staff(interaction, int(custom_id.split("_")[2]))
            elif custom_id.startswith("close_"):
                await self.close_ticket(interaction, int(custom_id.split("_")[1]))
            elif custom_id.startswith("reopen_"):
                await self.reopen_ticket(interaction, int(custom_id.split("_")[1]))
            elif custom_id.startswith("delete_"):
                await self.delete_ticket(interaction, int(custom_id.split("_")[1]))
            elif custom_id.startswith("invite_"):
                await self.invite_user(interaction, int(custom_id.split("_")[1]))
        except Exception as e:
            await self._send_ephemeral(interaction, f"Error: `{e}`")
            print(f"Ticket interaction error: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or not isinstance(message.channel, discord.TextChannel):
            return
        if message.content.startswith(config.PREFIX):
            return
        record = await db.get_active_ticket_by_channel(message.guild.id, message.channel.id)
        if not record:
            return
        if len(record) > 13 and record[13]:
            return
        content = message.content.strip()
        lower = content.lower()
        if isinstance(message.author, discord.Member) and self._is_claim_staff(message.author):
            if lower in ("ai stop", "aistop", "ai-stop"):
                await self._manual_ai_stop(message, record)
                return
            if lower in ("ai start", "aistart", "ai-start"):
                await self._manual_ai_start(message, record)
                return
            if record[9]:
                await self._send_ai_takeover_prompt(message, record)
                return
        if not record[9]:
            return
        await self._handle_ai_customer_message(message, record)

    async def create_ticket(self, interaction, ticket_type):
        category_kind = self._ticket_kind(ticket_type)
        category_id = await db.get_ticket_type_category(interaction.guild.id, category_kind)
        staff_role_id = await db.get_ticket_staff_role(interaction.guild.id) or str(CLAIM_ROLE_ID)
        if not category_id:
            await interaction.response.send_message("Ticket system is not set up. Contact an admin.", ephemeral=True)
            return
        category = interaction.guild.get_channel(int(category_id))
        if not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message("Ticket category was deleted or invalid. Please setup again.", ephemeral=True)
            return
        staff_role = interaction.guild.get_role(int(staff_role_id)) if staff_role_id else interaction.guild.get_role(CLAIM_ROLE_ID)
        ticket_name = f"{TICKET_TYPE_NAMES.get(ticket_type, 'ticket')}-{self._clean_channel_name(interaction.user.name)}"[:90]
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, read_message_history=True),
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        channel = await interaction.guild.create_text_channel(
            name=ticket_name,
            category=category,
            overwrites=overwrites,
            reason=f"Ticket created by {interaction.user}",
        )
        ticket_id = await db.create_active_ticket(interaction.guild.id, channel.id, interaction.user.id, ticket_type)
        message = await self.send_ticket_message(channel, interaction.user, ticket_type, ticket_id, staff_role)
        await db.set_active_ticket_message(ticket_id, message.id)
        auto_ai_delay = await db.get_ticket_type_ai_delay(interaction.guild.id, category_kind)
        if auto_ai_delay:
            await db.set_ticket_ai_delay(ticket_id, int(auto_ai_delay))
            self._schedule_ai_timer(ticket_id, int(auto_ai_delay))
            await self._log(interaction.guild, "Auto AI Timer Started", f"Ticket #{ticket_id}\nType: `{category_kind}`\nDelay: `{self._human_duration(auto_ai_delay)}`")
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)
        await self.log_ticket_created(interaction.guild, interaction.user, ticket_type, ticket_id)

    async def send_ticket_message(self, channel, user, ticket_type, ticket_id, staff_role):
        description = (
            f"**Created by:** {user.mention}\n"
            f"**Type:** {ticket_type.replace('_', ' ').title()}\n\n"
            "Please describe your issue and staff will assist you shortly."
        )
        embed = discord.Embed(
            title=f"Ticket #{ticket_id} - {ticket_type.replace('_', ' ').title()}",
            description=description,
            color=NEUTRAL_COLOR,
        )
        embed.set_image(url=TICKET_IMAGE_URL)
        embed.set_footer(text=f"Ticket ID: {ticket_id}")
        embed.add_field(name="Status", value="Unclaimed", inline=True)
        embed.add_field(name="Responsible", value="Waiting for staff", inline=True)
        staff_mention = staff_role.mention if staff_role else f"<@&{CLAIM_ROLE_ID}>"
        message = await channel.send(
            f"{staff_mention} {user.mention}",
            embed=embed,
            view=self._build_ticket_view(ticket_id, "unclaimed"),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True, everyone=False),
        )
        if ticket_type == "order":
            await channel.send(ORDER_OPENING_TEXT, allowed_mentions=discord.AllowedMentions.none())
        return message

    async def accept_ticket(self, interaction, ticket_id: int):
        if not self._is_claim_staff(interaction.user):
            await interaction.response.send_message("Only the claim role or Administrators can claim tickets.", ephemeral=True)
            return
        await self._assign_ticket_staff(interaction, ticket_id, interaction.user, changed=False, edit_component_message=True)

    async def claim_from_ai_prompt(self, interaction, ticket_id: int):
        if not self._is_claim_staff(interaction.user):
            await self._send_ephemeral(interaction, "Only ticket staff or Administrators can claim tickets.")
            return
        await self._defer_ephemeral(interaction)
        data = await self._get_ticket_record(ticket_id)
        if not data:
            await self._send_ephemeral(interaction, "Ticket not found.")
            return
        if len(data) > 13 and data[13]:
            await self._send_ephemeral(interaction, "This ticket is closed. Reopen it first.")
            return
        channel = interaction.guild.get_channel(int(data[2]))
        if not channel:
            await db.delete_active_ticket(ticket_id)
            self._cancel_ai_timer(ticket_id)
            await self._send_ephemeral(interaction, "Ticket channel not found. Record cleaned.")
            return
        await db.set_active_ticket_staff(ticket_id, interaction.user.id)
        self._cancel_ai_timer(ticket_id)
        await db.disable_ticket_ai(ticket_id)
        await self._edit_ticket_message(interaction.guild, ticket_id, "Claimed", interaction.user.mention, "claimed", NEUTRAL_COLOR)
        try:
            if interaction.message:
                disabled_view = discord.ui.View(timeout=None)
                disabled_view.add_item(
                    discord.ui.Button(
                        style=discord.ButtonStyle.secondary,
                        label=f"Claimed by {interaction.user.display_name}"[:80],
                        disabled=True,
                    )
                )
                await interaction.message.edit(view=disabled_view)
        except discord.HTTPException:
            pass
        embed = discord.Embed(
            title="Ticket Claimed",
            description=f"{interaction.user.mention} took this ticket from AI.",
            color=NEUTRAL_COLOR,
        )
        await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
        await self.log_ticket_accepted(interaction.guild, interaction.user, ticket_id, change=True)
        await self._send_ephemeral(interaction, "You claimed this ticket from AI.")

    async def _send_ai_takeover_prompt(self, message: discord.Message, record):
        ticket_id = int(record[0])
        embed = discord.Embed(
            title="AI is currently handling this ticket",
            description=(
                f"{message.author.mention}, AI is still assisting the customer.\n"
                "Press **Claim** if you want to take this ticket from AI.\n"
                "If you do nothing, AI will continue helping the customer."
            ),
            color=NEUTRAL_COLOR,
        )
        embed.add_field(name="Current Responsible", value="AI Assistant", inline=True)
        embed.add_field(name="Ticket ID", value=str(ticket_id), inline=True)
        view = discord.ui.View(timeout=120)
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label="Claim", custom_id=f"claim_ai_{ticket_id}"))
        try:
            await message.channel.send(
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
            )
        except discord.HTTPException:
            pass

    async def _assign_ticket_staff(self, interaction, ticket_id: int, staff_member: discord.Member, changed: bool, edit_component_message: bool = False):
        data = await self._get_ticket_record(ticket_id)
        if not data:
            await interaction.response.send_message("Ticket not found.", ephemeral=True)
            return
        if len(data) > 13 and data[13]:
            await interaction.response.send_message("This ticket is closed. Reopen it first.", ephemeral=True)
            return
        channel = interaction.guild.get_channel(int(data[2]))
        if not channel:
            await db.delete_active_ticket(ticket_id)
            self._cancel_ai_timer(ticket_id)
            await interaction.response.send_message("Ticket channel not found. Record cleaned.", ephemeral=True)
            return
        if not self._is_claim_staff(staff_member):
            await interaction.response.send_message("Selected member is not ticket staff or Administrator.", ephemeral=True)
            return
        await db.set_active_ticket_staff(ticket_id, staff_member.id)
        self._cancel_ai_timer(ticket_id)
        await db.disable_ticket_ai(ticket_id)
        mode = "claimed"
        if edit_component_message and interaction.message and interaction.message.embeds:
            embed = self._apply_status_to_embed(interaction.message.embeds[0], "Claimed", staff_member.mention, NEUTRAL_COLOR)
            await interaction.response.edit_message(embed=embed, view=self._build_ticket_view(ticket_id, mode))
        else:
            await self._edit_ticket_message(interaction.guild, ticket_id, "Claimed", staff_member.mention, mode, NEUTRAL_COLOR)
            if not interaction.response.is_done():
                await interaction.response.edit_message(content=f"Staff changed to {staff_member.mention}.", embed=None, view=None)
        title = "Ticket Staff Changed" if changed else "Ticket Claimed"
        desc = f"{staff_member.mention} is now responsible for this ticket."
        embed = discord.Embed(title=title, description=desc, color=NEUTRAL_COLOR)
        await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
        if edit_component_message:
            await interaction.followup.send(f"Ticket claimed by {staff_member.mention}.", ephemeral=True)
        await self.log_ticket_accepted(interaction.guild, staff_member, ticket_id, change=changed)

    async def show_staff_select(self, interaction, ticket_id: int):
        if not self._is_claim_staff(interaction.user):
            await interaction.response.send_message("Only ticket staff or Administrators can change staff.", ephemeral=True)
            return
        data = await self._get_ticket_record(ticket_id)
        if not data:
            await interaction.response.send_message("Ticket not found.", ephemeral=True)
            return
        members = []
        seen = set()
        role = interaction.guild.get_role(CLAIM_ROLE_ID)
        if role:
            for member in role.members:
                if not member.bot and member.id not in seen:
                    members.append(member)
                    seen.add(member.id)
        for member in interaction.guild.members:
            if member.guild_permissions.administrator and not member.bot and member.id not in seen:
                members.append(member)
                seen.add(member.id)
        members = sorted(members, key=lambda m: m.display_name.lower())[:25]
        if not members:
            await interaction.response.send_message("No staff members found in cache.", ephemeral=True)
            return
        options = [
            discord.SelectOption(label=m.display_name[:100], value=str(m.id), description=f"@{m.name}"[:100])
            for m in members
        ]
        select = discord.ui.Select(placeholder="Choose the new ticket staff", custom_id=f"select_staff_{ticket_id}", options=options)
        view = discord.ui.View(timeout=60)
        view.add_item(select)
        embed = discord.Embed(
            title="Change Ticket Staff",
            description="Select the staff member who will take this ticket.",
            color=NEUTRAL_COLOR,
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def select_staff(self, interaction, ticket_id: int):
        if not self._is_claim_staff(interaction.user):
            await interaction.response.send_message("Only ticket staff or Administrators can change staff.", ephemeral=True)
            return
        values = interaction.data.get("values") or []
        if not values:
            await interaction.response.send_message("No staff selected.", ephemeral=True)
            return
        try:
            member = interaction.guild.get_member(int(values[0])) or await interaction.guild.fetch_member(int(values[0]))
        except Exception:
            member = None
        if not member:
            await interaction.response.send_message("Selected member not found.", ephemeral=True)
            return
        await self._assign_ticket_staff(interaction, ticket_id, member, changed=True, edit_component_message=False)

    def _can_close_ticket(self, member: discord.Member, data) -> bool:
        return self._is_claim_staff(member) or str(member.id) == str(data[3])

    async def close_ticket(self, interaction, ticket_id):
        await self._defer_ephemeral(interaction)
        data = await self._get_ticket_record(ticket_id)
        if not data:
            await self._send_ephemeral(interaction, "Ticket not found.")
            return
        if len(data) > 13 and data[13]:
            await self._send_ephemeral(interaction, "Ticket is already closed.")
            return
        if not self._can_close_ticket(interaction.user, data):
            await self._send_ephemeral(interaction, "Only the ticket owner, ticket staff, or Administrators can close this ticket.")
            return
        channel = interaction.guild.get_channel(int(data[2]))
        user = interaction.guild.get_member(int(data[3]))
        if not channel:
            await db.delete_active_ticket(ticket_id)
            self._cancel_ai_timer(ticket_id)
            await self._send_ephemeral(interaction, "Missing ticket record cleaned.")
            return
        if user:
            try:
                await self.send_rating(user, interaction.guild.id, ticket_id)
            except discord.Forbidden:
                pass
        await self._send_ephemeral(interaction, "Closing ticket in 5 seconds...")
        await asyncio.sleep(5)
        transcript_file, msg_count = await self.build_transcript_file(channel, ticket_id, data)
        await self.log_ticket_closed(interaction.guild, interaction.user, ticket_id, data, msg_count, transcript_file)
        await db.set_active_ticket_closed(ticket_id, True)
        await db.disable_ticket_ai(ticket_id)
        self._cancel_ai_timer(ticket_id)
        self.ai_busy_channels.discard(int(channel.id))
        await self._edit_ticket_message(interaction.guild, ticket_id, "Closed", "Archived", "closed", NEUTRAL_COLOR)
        await self._archive_channel(channel, data, interaction.user)
        embed = discord.Embed(
            title="Ticket Closed",
            description="This ticket has been archived. Use **Open** to reopen it or **Delete** to remove it permanently.",
            color=NEUTRAL_COLOR,
        )
        await channel.send(embed=embed, view=self._build_closed_view(ticket_id), allowed_mentions=discord.AllowedMentions.none())

    async def _archive_channel(self, channel: discord.TextChannel, data, closer: discord.Member):
        ticket_type = data[4]
        user = channel.guild.get_member(int(data[3]))
        username = self._clean_channel_name(user.name if user else str(data[3]))
        new_name = f"closed-{TICKET_TYPE_NAMES.get(ticket_type, 'ticket')}-{username}"[:90]
        archive_id = await db.get_ticket_archive_category(channel.guild.id)
        archive_category = channel.guild.get_channel(int(archive_id)) if archive_id else None

        overwrites = dict(channel.overwrites)
        for target in list(overwrites.keys()):
            if isinstance(target, discord.Member) and self.bot.user and target.id == self.bot.user.id:
                continue
            overwrites[target] = discord.PermissionOverwrite(view_channel=False, send_messages=False, read_message_history=False)
        overwrites[channel.guild.default_role] = discord.PermissionOverwrite(view_channel=False, send_messages=False, read_message_history=False)
        overwrites[channel.guild.me] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, read_message_history=True)

        try:
            kwargs = {"name": new_name, "overwrites": overwrites, "reason": f"Ticket closed by {closer}"}
            if isinstance(archive_category, discord.CategoryChannel):
                kwargs["category"] = archive_category
            await channel.edit(**kwargs)
        except discord.HTTPException:
            pass

    async def reopen_ticket(self, interaction, ticket_id: int):
        await self._defer_ephemeral(interaction)
        if not self._is_claim_staff(interaction.user):
            await self._send_ephemeral(interaction, "Only ticket staff or Administrators can reopen tickets.")
            return
        data = await self._get_ticket_record(ticket_id)
        if not data:
            await self._send_ephemeral(interaction, "Ticket not found.")
            return
        channel = interaction.guild.get_channel(int(data[2]))
        if not channel:
            await db.delete_active_ticket(ticket_id)
            await self._send_ephemeral(interaction, "Ticket channel not found. Record cleaned.")
            return
        ticket_type = data[4]
        ticket_kind = self._ticket_kind(ticket_type)
        category_id = await db.get_ticket_type_category(interaction.guild.id, ticket_kind)
        category = interaction.guild.get_channel(int(category_id)) if category_id else None
        user = interaction.guild.get_member(int(data[3]))
        if not user:
            try:
                user = await interaction.guild.fetch_member(int(data[3]))
            except Exception:
                user = None
        staff_role_id = await db.get_ticket_staff_role(interaction.guild.id) or str(CLAIM_ROLE_ID)
        staff_role = interaction.guild.get_role(int(staff_role_id)) if staff_role_id else None
        username = self._clean_channel_name(user.name if user else str(data[3]))
        new_name = f"{TICKET_TYPE_NAMES.get(ticket_type, 'ticket')}-{username}"[:90]

        overwrites = dict(channel.overwrites)
        overwrites[interaction.guild.default_role] = discord.PermissionOverwrite(view_channel=False)
        overwrites[interaction.guild.me] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, read_message_history=True)
        if user:
            overwrites[user] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        try:
            kwargs = {"name": new_name, "overwrites": overwrites, "reason": f"Ticket reopened by {interaction.user}"}
            if isinstance(category, discord.CategoryChannel):
                kwargs["category"] = category
            await channel.edit(**kwargs)
        except discord.HTTPException:
            pass

        await db.set_active_ticket_closed(ticket_id, False)
        await db.set_active_ticket_staff(ticket_id, None)
        await self._edit_ticket_message(interaction.guild, ticket_id, "Unclaimed", "Waiting for staff", "unclaimed", NEUTRAL_COLOR)
        await self._send_ephemeral(interaction, "Ticket reopened.")
        await channel.send(f"Ticket reopened by {interaction.user.mention}.", allowed_mentions=discord.AllowedMentions(users=True))
        await self._log(interaction.guild, "Ticket Reopened", f"Ticket #{ticket_id}\nBy: {interaction.user.mention}")

    async def delete_ticket(self, interaction, ticket_id: int):
        await self._defer_ephemeral(interaction)
        if not self._is_claim_staff(interaction.user):
            await self._send_ephemeral(interaction, "Only ticket staff or Administrators can delete tickets.")
            return
        data = await self._get_ticket_record(ticket_id)
        if not data:
            await self._send_ephemeral(interaction, "Ticket not found.")
            return
        channel = interaction.guild.get_channel(int(data[2]))
        await self._send_ephemeral(interaction, "Deleting ticket...")
        await self._log(interaction.guild, "Ticket Deleted", f"Ticket #{ticket_id}\nBy: {interaction.user.mention}")
        await db.delete_active_ticket(ticket_id)
        self._cancel_ai_timer(ticket_id)
        if channel:
            await channel.delete(reason=f"Ticket deleted by {interaction.user}")

    async def invite_user(self, interaction, ticket_id):
        data = await self._get_ticket_record(ticket_id)
        if not data:
            await interaction.response.send_message("Ticket not found.", ephemeral=True)
            return
        if len(data) > 13 and data[13]:
            await interaction.response.send_message("This ticket is closed. Reopen it first.", ephemeral=True)
            return
        channel = interaction.guild.get_channel(int(data[2]))
        if not channel:
            await db.delete_active_ticket(ticket_id)
            self._cancel_ai_timer(ticket_id)
            await interaction.response.send_message("Ticket channel not found. Record cleaned.", ephemeral=True)
            return
        modal = discord.ui.Modal(title="Invite User")
        user_input = discord.ui.TextInput(label="User ID or Mention", placeholder="Enter user ID or mention...", required=True)
        modal.add_item(user_input)

        async def on_submit(i):
            user_id = re.sub(r"[<@!>]", "", user_input.value)
            if not user_id.isdigit():
                await i.response.send_message("Invalid user ID.", ephemeral=True)
                return
            try:
                user = await interaction.guild.fetch_member(int(user_id))
            except discord.NotFound:
                user = None
            if not user:
                await i.response.send_message("User not found.", ephemeral=True)
                return
            await channel.set_permissions(user, view_channel=True, send_messages=True, read_message_history=True)
            await i.response.send_message(f"{user.mention} has been added.", ephemeral=True)
            await channel.send(f"{user.mention} has been added by {interaction.user.mention}", allowed_mentions=discord.AllowedMentions(users=True))

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)

    async def send_rating(self, user, guild_id: int, ticket_id: int):
        embed = discord.Embed(
            title="🌟 تقييم التكت",
            description=f"شكراً لاستخدامك نظام التكت.\n\nقيّم تجربتك في التكت **#{ticket_id}** من 1 إلى 5.",
            color=NEUTRAL_COLOR,
        )
        view = discord.ui.View(timeout=300)
        for label, value in [("🌟 1", "1"), ("🌟 2", "2"), ("🌟 3", "3"), ("🌟 4", "4"), ("🌟 5", "5")]:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label=label, custom_id=f"rate_{guild_id}_{ticket_id}_{value}"))
        await user.send(embed=embed, view=view)

    async def save_rating(self, interaction, guild_id: int, ticket_id: int, rating: int):
        embed = discord.Embed(
            title="🌟 تم حفظ التقييم",
            description=f"شكراً لتقييمك التكت **#{ticket_id}** بـ **{rating}/5** 🌟.",
            color=NEUTRAL_COLOR,
        )
        await interaction.response.send_message(embed=embed)
        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            return
        channel_id = await db.get_ticket_rating_channel(guild.id) or await db.get_ticket_logs(guild.id)
        if channel_id:
            channel = guild.get_channel(int(channel_id))
            if channel:
                rating_embed = discord.Embed(
                    title="🌟 Ticket Rating",
                    description=f"**Ticket ID:** #{ticket_id}\n**Rating:** {'🌟' * rating} ({rating}/5)\n**User:** {interaction.user.mention} (`{interaction.user.id}`)",
                    color=NEUTRAL_COLOR,
                )
                await channel.send(embed=rating_embed, allowed_mentions=discord.AllowedMentions.none())

    async def build_transcript_file(self, channel: discord.TextChannel, ticket_id: int, data):
        rows = []
        msg_count = 0
        async for message in channel.history(limit=None, oldest_first=True):
            msg_count += 1
            author = html.escape(str(message.author))
            display = html.escape(getattr(message.author, "display_name", str(message.author)))
            bot_tag = " BOT" if message.author.bot else ""
            timestamp = message.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            content = html.escape(message.content or "").replace("\n", "<br>")
            if not content:
                content = "<em>No text content</em>"
            attachments_html = []
            for attachment in message.attachments:
                url = html.escape(attachment.url)
                name = html.escape(attachment.filename)
                is_image = False
                if getattr(attachment, "content_type", None):
                    is_image = str(attachment.content_type).startswith("image/")
                if not is_image:
                    is_image = attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
                if is_image:
                    attachments_html.append(f'<div class="attachment"><a href="{url}">{name}</a><br><img src="{url}" alt="{name}"></div>')
                else:
                    attachments_html.append(f'<div class="attachment"><a href="{url}">{name}</a></div>')
            embeds_html = []
            for emb in message.embeds:
                parts = []
                if emb.title:
                    parts.append(f"<strong>{html.escape(emb.title)}</strong>")
                if emb.description:
                    parts.append(html.escape(emb.description).replace("\n", "<br>"))
                for field in emb.fields:
                    parts.append(f"<strong>{html.escape(field.name)}</strong>: {html.escape(field.value).replace(chr(10), '<br>')}")
                image_url = None
                if emb.image and emb.image.url:
                    image_url = emb.image.url
                elif emb.thumbnail and emb.thumbnail.url:
                    image_url = emb.thumbnail.url
                if image_url:
                    safe_url = html.escape(image_url)
                    parts.append(f'<a href="{safe_url}">Embed image</a><br><img src="{safe_url}" alt="embed image">')
                if parts:
                    embeds_html.append('<div class="embed">' + '<br>'.join(parts) + '</div>')
            rows.append(f'''
            <div class="message">
                <div class="meta"><span class="author">{display}</span><span class="bot">{bot_tag}</span> <span class="tag">{author}</span> <span class="time">{timestamp}</span></div>
                <div class="content">{content}</div>
                {''.join(attachments_html)}
                {''.join(embeds_html)}
            </div>
            ''')
        ticket_type = html.escape(str(data[4]))
        user_id = html.escape(str(data[3]))
        created = html.escape(str(data[6]))
        generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        body = "".join(rows) or "<p>No messages found.</p>"
        doc = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Ticket #{ticket_id} Transcript</title>
<style>
body {{ font-family: Arial, sans-serif; background: #313338; color: #f2f3f5; margin: 0; padding: 24px; }}
.header {{ background: #2b2d31; border-radius: 10px; padding: 16px; margin-bottom: 18px; }}
.message {{ background: #2b2d31; border-radius: 10px; padding: 12px 14px; margin: 10px 0; }}
.meta {{ color: #b5bac1; font-size: 13px; margin-bottom: 6px; }}
.author {{ color: #ffffff; font-weight: bold; }}
.bot {{ color: #57f287; font-weight: bold; }}
.tag {{ color: #949ba4; margin-left: 6px; }}
.time {{ float: right; color: #949ba4; }}
.content {{ line-height: 1.45; word-wrap: break-word; }}
.attachment, .embed {{ margin-top: 8px; padding: 8px; border-left: 3px solid #5865f2; background: #232428; border-radius: 6px; }}
a {{ color: #00a8fc; }}
img {{ max-width: 420px; max-height: 420px; border-radius: 8px; margin-top: 6px; display: block; }}
</style>
</head>
<body>
<div class="header">
<h1>Ticket #{ticket_id} Transcript</h1>
<p><strong>Channel:</strong> #{html.escape(channel.name)}<br>
<strong>Type:</strong> {ticket_type}<br>
<strong>User ID:</strong> {user_id}<br>
<strong>Created:</strong> {created}<br>
<strong>Generated:</strong> {generated}<br>
<strong>Messages:</strong> {msg_count}</p>
</div>
{body}
</body>
</html>'''
        file_data = io.BytesIO(doc.encode("utf-8"))
        return discord.File(file_data, filename=f"ticket_{ticket_id}_transcript.html"), msg_count

    async def log_ticket_created(self, guild, user, ticket_type, ticket_id):
        await self._log(guild, "Ticket Created", f"User: {user.mention}\nType: {ticket_type.title()}\nID: #{ticket_id}")

    async def log_ticket_accepted(self, guild, staff, ticket_id, change=False):
        title = "Ticket Staff Changed" if change else "Ticket Claimed"
        await self._log(guild, title, f"Staff: {staff.mention}\nID: #{ticket_id}")

    async def log_ticket_closed(self, guild, closer, ticket_id, data, msg_count, transcript_file):
        description = (
            f"Closed by: {closer.mention}\n"
            f"ID: #{ticket_id}\n"
            f"Type: `{data[4]}`\n"
            f"User: <@{data[3]}> (`{data[3]}`)\n"
            f"Transcript messages: `{msg_count}`"
        )
        await self._log(guild, "Ticket Closed + Transcript", description, NEUTRAL_COLOR, transcript_file)

    def _cancel_ai_timer(self, ticket_id: int):
        task = self.ai_tasks.pop(int(ticket_id), None)
        if task and not task.done():
            task.cancel()

    def _schedule_ai_timer(self, ticket_id: int, seconds: int):
        self._cancel_ai_timer(ticket_id)
        task = asyncio.create_task(self._ai_timer(int(ticket_id), int(seconds)))
        self.ai_tasks[int(ticket_id)] = task

    async def _resume_ai_timers(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(2)
        try:
            pending = await db.get_ai_pending_tickets()
        except Exception as e:
            print(f"AI timer resume error: {e}")
            return
        for record in pending:
            delay = int(record[11] or 0)
            if delay <= 0:
                continue
            start_time = self._parse_db_datetime(record[12] if len(record) > 12 else None) or self._parse_db_datetime(record[6])
            elapsed = 0
            if start_time:
                elapsed = max(0, int((datetime.now(timezone.utc) - start_time).total_seconds()))
            remaining = max(1, delay - elapsed)
            self._schedule_ai_timer(int(record[0]), remaining)

    def _parse_db_datetime(self, value):
        if not value:
            return None
        if isinstance(value, datetime):
            dt = value
        else:
            try:
                dt = datetime.fromisoformat(str(value))
            except ValueError:
                return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    async def _ai_timer(self, ticket_id: int, seconds: int):
        try:
            await asyncio.sleep(seconds)
            data = await self._get_ticket_record(ticket_id)
            if not data:
                return
            if (len(data) > 13 and data[13]) or data[5] or not data[8] or data[9]:
                return
            guild = self.bot.get_guild(int(data[1]))
            if not guild:
                return
            await self._activate_ai(guild, data, reason="timeout")
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"AI timer error for ticket {ticket_id}: {e}")

    async def _manual_ai_start(self, message: discord.Message, record):
        await self._activate_ai(message.guild, record, reason="manual", actor=message.author)
        await message.channel.send("AI started for this ticket.")

    async def _manual_ai_stop(self, message: discord.Message, record):
        ticket_id = int(record[0])
        await db.disable_ticket_ai(ticket_id)
        self._cancel_ai_timer(ticket_id)
        await self._edit_ticket_message(message.guild, ticket_id, "Unclaimed", "Waiting for staff", "unclaimed", NEUTRAL_COLOR)
        embed = discord.Embed(
            title="AI Stopped",
            description="AI has been stopped. Staff should claim this ticket using the Claim button.",
            color=NEUTRAL_COLOR,
        )
        await message.channel.send(embed=embed)
        await self._log(message.guild, "AI Stopped", f"Ticket #{ticket_id}\nBy: {message.author.mention}")

    async def _activate_ai(self, guild: discord.Guild, record, reason: str = "manual", actor=None):
        ticket_id = int(record[0])
        channel = guild.get_channel(int(record[2]))
        if not channel:
            await db.delete_active_ticket(ticket_id)
            self._cancel_ai_timer(ticket_id)
            return
        if len(record) > 13 and record[13]:
            return
        await db.set_active_ticket_staff(ticket_id, None)
        await db.set_ticket_ai_active(ticket_id, True)
        await self._edit_ticket_message(guild, ticket_id, "Claimed", "AI Assistant", "ai", NEUTRAL_COLOR)
        user = guild.get_member(int(record[3]))
        greeting_target = user.mention if user else f"<@{record[3]}>"
        await channel.send(
            f"{greeting_target} AI is helping temporarily until staff takes over. Send your request clearly in one message.",
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
        )
        by_text = f"\nBy: {actor.mention}" if actor else ""
        await self._log(guild, "AI Started", f"Ticket #{ticket_id}\nReason: {reason}{by_text}")

    async def _handle_ai_customer_message(self, message: discord.Message, record):
        ticket_id = int(record[0])
        channel_id = int(message.channel.id)
        if channel_id in self.ai_busy_channels or record[10]:
            try:
                await message.reply("Please wait for the current AI reply first.", delete_after=6)
            except discord.HTTPException:
                pass
            return
        self.ai_busy_channels.add(channel_id)
        await db.set_ticket_ai_busy(ticket_id, True)
        permission_changed = False
        try:
            await message.channel.set_permissions(message.author, send_messages=False, view_channel=True, read_message_history=True)
            permission_changed = True
        except discord.HTTPException:
            permission_changed = False
        try:
            async with message.channel.typing():
                response = await self._generate_ai_reply(message, record)
            await message.channel.send(response, allowed_mentions=discord.AllowedMentions(users=True, roles=True, everyone=False))
        except Exception as e:
            print(f"AI response error: {e}")
            await message.channel.send("AI could not reply right now. Staff has been notified.")
            await self._log(message.guild, "AI Error", f"Ticket #{ticket_id}\nError: `{e}`")
        finally:
            if permission_changed:
                try:
                    await message.channel.set_permissions(message.author, send_messages=True, view_channel=True, read_message_history=True)
                except discord.HTTPException:
                    pass
            self.ai_busy_channels.discard(channel_id)
            await db.set_ticket_ai_busy(ticket_id, False)

    async def _generate_ai_reply(self, message: discord.Message, record):
        if self._needs_staff_for_purchase(message.content):
            mentions = await self._get_ai_role_mentions(message.guild)
            mention_text = " ".join(mentions).strip()
            await self._log(message.guild, "AI Purchase Request", f"Ticket #{record[0]}\nUser: {message.author.mention}\nMessage: {message.content[:500]}")
            prefix = f"{mention_text}\n" if mention_text else ""
            return prefix + f"{message.author.mention} تمام، فهمت طلبك. تفاصيل الشراء أو السعر لازم الإدارة تأكدها لك هنا، استنى ردهم ومتشاركش أي بيانات حساسة."
        if not config.OPENROUTER_API_KEY:
            mentions = await self._get_ai_role_mentions(message.guild)
            mention_text = " ".join(mentions).strip()
            prefix = f"{mention_text}\n" if mention_text else ""
            return prefix + "AI API key is not configured yet. Staff will help you soon."
        history = await self._build_ai_history(message.channel)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)
        payload = {
            "model": config.OPENROUTER_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 220,
        }
        headers = {
            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": config.OPENROUTER_SITE_URL,
            "X-OpenRouter-Title": config.OPENROUTER_SITE_NAME,
        }
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(config.OPENROUTER_BASE_URL, headers=headers, json=payload) as resp:
                data = await resp.json(content_type=None)
                if resp.status >= 400:
                    raise RuntimeError(data.get("error", data))
        content = data.get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            content = "I could not understand that. Please explain your request in one short message."
        content = str(content).strip()
        max_chars = getattr(config, "AI_RESPONSE_MAX_CHARS", 700)
        if len(content) > max_chars:
            content = content[:max_chars].rstrip() + "..."
        return content

    async def _build_ai_history(self, channel: discord.TextChannel):
        messages = []
        limit = getattr(config, "AI_HISTORY_LIMIT", 18)
        async for msg in channel.history(limit=limit, oldest_first=True):
            if not msg.content:
                continue
            clean = msg.content.strip()
            if not clean or clean.startswith(config.PREFIX):
                continue
            if clean.lower() in ("ai start", "ai stop", "aistart", "aistop", "ai-start", "ai-stop"):
                continue
            role = "assistant" if msg.author.bot else "user"
            messages.append({"role": role, "content": clean[:1200]})
        return messages[-limit:]

    def _needs_staff_for_purchase(self, text: str) -> bool:
        lowered = (text or "").lower()
        return any(keyword in lowered for keyword in PURCHASE_KEYWORDS)

    async def _get_ai_role_mentions(self, guild: discord.Guild):
        admin_role_id, owner_role_id = await db.get_ticket_ai_roles(guild.id)
        mentions = []
        for role_id in (admin_role_id, owner_role_id):
            if role_id:
                role = guild.get_role(int(role_id))
                if role:
                    mentions.append(role.mention)
        return mentions


async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
