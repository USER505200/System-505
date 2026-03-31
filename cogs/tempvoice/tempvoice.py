# cogs/tempvoice/tempvoice.py
import discord
from discord.ext import commands
import asyncio
import re
from config import COLORS, EMOJIS
import database as db

class TempVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_channels = {}
        self.delete_tasks = {}
        self.panel_channel_id = None
        self.panel_message_id = None
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.guild:
            return
        
        temp_channel_id = await db.get_temp_voice_channel(member.guild.id)
        if not temp_channel_id:
            return
        
        temp_channel = member.guild.get_channel(int(temp_channel_id))
        if not temp_channel:
            return
        
        if after.channel and after.channel.id == temp_channel.id:
            for v_id, data in list(self.active_channels.items()):
                if data["owner_id"] == member.id and v_id in self.delete_tasks:
                    self.delete_tasks[v_id].cancel()
                    del self.delete_tasks[v_id]
            
            await self.create_temp_voice(member, after.channel)
        
        if before.channel and before.channel.id in self.active_channels:
            if len(before.channel.members) == 0:
                await self.schedule_delete(before.channel)
    
    async def schedule_delete(self, voice_channel):
        voice_id = voice_channel.id
        
        if voice_id in self.delete_tasks:
            self.delete_tasks[voice_id].cancel()
        
        async def delayed_delete():
            await asyncio.sleep(2)
            await self.delete_temp_voice(voice_channel)
        
        task = asyncio.create_task(delayed_delete())
        self.delete_tasks[voice_id] = task
    
    async def create_temp_voice(self, member, source_channel):
        """إنشاء روم صوتي فقط (بدون روم نصي)"""
        
        category = source_channel.category
        voice_name = f"{member.display_name}"
        
        # إنشاء الروم الصوتي فقط
        voice_channel = await member.guild.create_voice_channel(
            name=voice_name,
            category=category,
            user_limit=0,
            reason=f"Temp voice for {member.display_name}"
        )
        
        # صلاحيات الروم الصوتي
        await voice_channel.set_permissions(member, connect=True, manage_channels=True)
        await voice_channel.set_permissions(member.guild.default_role, connect=False)
        
        # حفظ البيانات
        self.active_channels[voice_channel.id] = {
            "owner_id": member.id,
            "voice_name": voice_name
        }
        
        # نقل العضو للروم الصوتي الجديد
        try:
            await member.move_to(voice_channel)
        except:
            pass
        
        # تحديث اللوحة الثابتة
        await self.update_main_panel(member.guild)
    
    async def update_main_panel(self, guild):
        if not self.panel_channel_id:
            return
        
        panel_channel = guild.get_channel(self.panel_channel_id)
        if not panel_channel:
            return
        
        active_list = []
        for v_id, data in self.active_channels.items():
            voice = guild.get_channel(v_id)
            if voice:
                owner = guild.get_member(data["owner_id"])
                active_list.append(f"• {voice.mention} - **Owner:** {owner.mention if owner else 'Unknown'}")
        
        embed = discord.Embed(
            title="Drive 505 X Temp Vc",
            description="**Active Voice Channels:**\n" + ("\n".join(active_list) if active_list else "No active voice channels yet."),
            color=discord.Color.dark_gray()
        )
        
        embed.set_image(url="https://cdn.discordapp.com/attachments/1481632627558715565/1485515148478120116/file_000000002a44720aa8ea74a5d90c8596.png?ex=69c376ca&is=69c2254a&hm=8fbcf1cd775ca8c5b3a3b9b253d54778eb2d2409184cdd51cde57081713e68e8&")
        
        embed.add_field(name=" How to Use", value="Join the temp voice channel to create your private !", inline=False)
        embed.set_footer(text=f"Total Active : {len(self.active_channels)}")
        
        view = discord.ui.View(timeout=None)
        
        buttons = ["Name", "Limit", "Privacy", "Trust", "Untrust", "Invite", "Kick", "Region", "Block", "Unblock", "Transfer", "Delete"]
        for btn in buttons:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label=btn, custom_id=f"control_{btn.lower()}"))
        
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label="Create", emoji="🎉", custom_id="create"))
        
        try:
            if self.panel_message_id:
                msg = await panel_channel.fetch_message(self.panel_message_id)
                await msg.edit(embed=embed, view=view)
            else:
                msg = await panel_channel.send(embed=embed, view=view)
                self.panel_message_id = msg.id
        except:
            msg = await panel_channel.send(embed=embed, view=view)
            self.panel_message_id = msg.id
    
    async def delete_temp_voice(self, voice_channel):
        if voice_channel.id not in self.active_channels:
            return
        
        if voice_channel.id in self.delete_tasks:
            del self.delete_tasks[voice_channel.id]
        
        try:
            await voice_channel.delete(reason="Temp voice deleted")
            del self.active_channels[voice_channel.id]
            await self.update_main_panel(voice_channel.guild)
        except Exception as e:
            print(f"Error deleting temp voice: {e}")
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if not interaction.type == discord.InteractionType.component:
            return
        
        custom_id = interaction.data["custom_id"]
        
        if custom_id == "create":
            temp_channel_id = await db.get_temp_voice_channel(interaction.guild.id)
            if not temp_channel_id:
                await interaction.response.send_message("❌ Temp voice channel not set! Use `!temp set #channel`", ephemeral=True)
                return
            
            temp_channel = interaction.guild.get_channel(int(temp_channel_id))
            if not temp_channel:
                await interaction.response.send_message("❌ Temp voice channel not found!", ephemeral=True)
                return
            
            await interaction.response.send_message(f"🎙️ Join {temp_channel.mention} to create your private !", ephemeral=True)
            return
        
        if custom_id.startswith("control_"):
            action = custom_id.split("_")[1]
            
            if not interaction.user.voice or not interaction.user.voice.channel:
                await interaction.response.send_message("❌ You must be in a voice channel to use these controls!", ephemeral=True)
                return
            
            voice_channel = interaction.user.voice.channel
            
            if voice_channel.id not in self.active_channels:
                await interaction.response.send_message("❌ This is not a temp voice channel!", ephemeral=True)
                return
            
            owner_id = self.active_channels[voice_channel.id]["owner_id"]
            is_owner = interaction.user.id == owner_id
            
            if action == "name":
                if not is_owner:
                    await interaction.response.send_message("❌ Only the channel owner can rename!", ephemeral=True)
                    return
                modal = discord.ui.Modal(title="Rename Voice Channel")
                name_input = discord.ui.TextInput(label="New Channel Name", placeholder="Enter new name...", required=True, max_length=100)
                modal.add_item(name_input)
                async def on_submit(i):
                    await voice_channel.edit(name=name_input.value)
                    await i.response.send_message(f"✅ Renamed to: **{name_input.value}**", ephemeral=True)
                modal.on_submit = on_submit
                await interaction.response.send_modal(modal)
            
            elif action == "limit":
                if not is_owner:
                    await interaction.response.send_message("❌ Only the channel owner can set limit!", ephemeral=True)
                    return
                modal = discord.ui.Modal(title="Set User Limit")
                limit_input = discord.ui.TextInput(label="User Limit (0-99)", placeholder="0 = unlimited", required=True, max_length=2)
                modal.add_item(limit_input)
                async def on_submit(i):
                    try:
                        limit = int(limit_input.value)
                        if 0 <= limit <= 99:
                            await voice_channel.edit(user_limit=limit)
                            await i.response.send_message(f"✅ Limit set to: **{limit if limit > 0 else 'Unlimited'}**", ephemeral=True)
                        else:
                            await i.response.send_message("❌ Limit must be 0-99!", ephemeral=True)
                    except:
                        await i.response.send_message("❌ Enter a valid number!", ephemeral=True)
                modal.on_submit = on_submit
                await interaction.response.send_modal(modal)
            
            elif action == "privacy":
                if not is_owner:
                    await interaction.response.send_message("❌ Only the channel owner can change privacy!", ephemeral=True)
                    return
                perms = voice_channel.overwrites_for(interaction.guild.default_role)
                if perms.connect is False:
                    await voice_channel.set_permissions(interaction.guild.default_role, connect=None)
                    await interaction.response.send_message("🔓 Channel is now **public**!", ephemeral=True)
                else:
                    await voice_channel.set_permissions(interaction.guild.default_role, connect=False)
                    await interaction.response.send_message("🔒 Channel is now **private**!", ephemeral=True)
            
            elif action == "trust":
                if not is_owner:
                    await interaction.response.send_message("❌ Only the channel owner can trust users!", ephemeral=True)
                    return
                modal = discord.ui.Modal(title="Trust User")
                user_input = discord.ui.TextInput(label="User ID or Mention", placeholder="Enter user ID or mention...", required=True)
                modal.add_item(user_input)
                async def on_submit(i):
                    user_id = re.sub(r'[<@!>]', '', user_input.value)
                    if user_id.isdigit():
                        user = await interaction.guild.fetch_member(int(user_id))
                        if user:
                            await voice_channel.set_permissions(user, connect=True)
                            await i.response.send_message(f"✅ {user.mention} has been trusted!", ephemeral=True)
                        else:
                            await i.response.send_message("❌ User not found!", ephemeral=True)
                    else:
                        await i.response.send_message("❌ Invalid user ID!", ephemeral=True)
                modal.on_submit = on_submit
                await interaction.response.send_modal(modal)
            
            elif action == "untrust":
                if not is_owner:
                    await interaction.response.send_message("❌ Only the channel owner can untrust users!", ephemeral=True)
                    return
                modal = discord.ui.Modal(title="Untrust User")
                user_input = discord.ui.TextInput(label="User ID or Mention", placeholder="Enter user ID or mention...", required=True)
                modal.add_item(user_input)
                async def on_submit(i):
                    user_id = re.sub(r'[<@!>]', '', user_input.value)
                    if user_id.isdigit():
                        user = await interaction.guild.fetch_member(int(user_id))
                        if user:
                            await voice_channel.set_permissions(user, connect=None)
                            await i.response.send_message(f"✅ {user.mention} has been untrusted!", ephemeral=True)
                        else:
                            await i.response.send_message("❌ User not found!", ephemeral=True)
                    else:
                        await i.response.send_message("❌ Invalid user ID!", ephemeral=True)
                modal.on_submit = on_submit
                await interaction.response.send_modal(modal)
            
            elif action == "invite":
                modal = discord.ui.Modal(title="Invite User")
                user_input = discord.ui.TextInput(label="User ID or Mention", placeholder="Enter user ID or mention...", required=True)
                modal.add_item(user_input)
                async def on_submit(i):
                    user_id = re.sub(r'[<@!>]', '', user_input.value)
                    if user_id.isdigit():
                        user = await interaction.guild.fetch_member(int(user_id))
                        if user:
                            await voice_channel.set_permissions(user, connect=True)
                            await i.response.send_message(f"✅ {user.mention} has been invited!", ephemeral=True)
                        else:
                            await i.response.send_message("❌ User not found!", ephemeral=True)
                    else:
                        await i.response.send_message("❌ Invalid user ID!", ephemeral=True)
                modal.on_submit = on_submit
                await interaction.response.send_modal(modal)
            
            elif action == "kick":
                if not is_owner:
                    await interaction.response.send_message("❌ Only the channel owner can kick!", ephemeral=True)
                    return
                members = [m for m in voice_channel.members if m.id != owner_id]
                if not members:
                    await interaction.response.send_message("❌ No members to kick!", ephemeral=True)
                    return
                select = discord.ui.Select(
                    placeholder="Select a member to kick...",
                    options=[discord.SelectOption(label=m.display_name, value=str(m.id)) for m in members[:25]]
                )
                async def select_cb(i):
                    user = interaction.guild.get_member(int(select.values[0]))
                    if user and user in voice_channel.members:
                        await user.move_to(None)
                        await i.response.send_message(f"✅ {user.mention} has been kicked!", ephemeral=True)
                select.callback = select_cb
                view = discord.ui.View(timeout=30)
                view.add_item(select)
                await interaction.response.send_message("👢 Select a member to kick:", view=view, ephemeral=True)
            
            elif action == "region":
                if not is_owner:
                    await interaction.response.send_message("❌ Only the channel owner can change region!", ephemeral=True)
                    return
                regions = [
                    discord.SelectOption(label="Auto", value="auto"),
                    discord.SelectOption(label="Europe", value="europe"),
                    discord.SelectOption(label="US East", value="us-east"),
                    discord.SelectOption(label="US West", value="us-west"),
                ]
                select = discord.ui.Select(placeholder="Select a region...", options=regions)
                async def select_cb(i):
                    region = select.values[0]
                    if region == "auto":
                        await voice_channel.edit(rtc_region=None)
                        await i.response.send_message("✅ Region set to **Auto**!", ephemeral=True)
                    else:
                        await voice_channel.edit(rtc_region=region)
                        await i.response.send_message(f"✅ Region set to **{region.title()}**!", ephemeral=True)
                select.callback = select_cb
                view = discord.ui.View(timeout=30)
                view.add_item(select)
                await interaction.response.send_message("🌍 Select a region:", view=view, ephemeral=True)
            
            elif action == "block":
                if not is_owner:
                    await interaction.response.send_message("❌ Only the channel owner can block!", ephemeral=True)
                    return
                modal = discord.ui.Modal(title="Block User")
                user_input = discord.ui.TextInput(label="User ID or Mention", placeholder="Enter user ID or mention...", required=True)
                modal.add_item(user_input)
                async def on_submit(i):
                    user_id = re.sub(r'[<@!>]', '', user_input.value)
                    if user_id.isdigit():
                        user = await interaction.guild.fetch_member(int(user_id))
                        if user:
                            await voice_channel.set_permissions(user, connect=False)
                            await i.response.send_message(f"🚫 {user.mention} has been blocked!", ephemeral=True)
                        else:
                            await i.response.send_message("❌ User not found!", ephemeral=True)
                    else:
                        await i.response.send_message("❌ Invalid user ID!", ephemeral=True)
                modal.on_submit = on_submit
                await interaction.response.send_modal(modal)
            
            elif action == "unblock":
                if not is_owner:
                    await interaction.response.send_message("❌ Only the channel owner can unblock!", ephemeral=True)
                    return
                modal = discord.ui.Modal(title="Unblock User")
                user_input = discord.ui.TextInput(label="User ID or Mention", placeholder="Enter user ID or mention...", required=True)
                modal.add_item(user_input)
                async def on_submit(i):
                    user_id = re.sub(r'[<@!>]', '', user_input.value)
                    if user_id.isdigit():
                        user = await interaction.guild.fetch_member(int(user_id))
                        if user:
                            await voice_channel.set_permissions(user, connect=None)
                            await i.response.send_message(f"✅ {user.mention} has been unblocked!", ephemeral=True)
                        else:
                            await i.response.send_message("❌ User not found!", ephemeral=True)
                    else:
                        await i.response.send_message("❌ Invalid user ID!", ephemeral=True)
                modal.on_submit = on_submit
                await interaction.response.send_modal(modal)
            
            elif action == "transfer":
                if not is_owner:
                    await interaction.response.send_message("❌ Only the channel owner can transfer!", ephemeral=True)
                    return
                members = [m for m in voice_channel.members if m.id != owner_id]
                if not members:
                    await interaction.response.send_message("❌ No members to transfer to!", ephemeral=True)
                    return
                select = discord.ui.Select(
                    placeholder="Select a new owner...",
                    options=[discord.SelectOption(label=m.display_name, value=str(m.id)) for m in members[:25]]
                )
                async def select_cb(i):
                    new_owner_id = int(select.values[0])
                    new_owner = interaction.guild.get_member(new_owner_id)
                    if new_owner:
                        self.active_channels[voice_channel.id]["owner_id"] = new_owner_id
                        await i.response.send_message(f"👑 Channel transferred to {new_owner.mention}!", ephemeral=True)
                    else:
                        await i.response.send_message("❌ User not found!", ephemeral=True)
                select.callback = select_cb
                view = discord.ui.View(timeout=30)
                view.add_item(select)
                await interaction.response.send_message("👑 Select a new owner:", view=view, ephemeral=True)
            
            elif action == "delete":
                if not is_owner:
                    await interaction.response.send_message("❌ Only the channel owner can delete!", ephemeral=True)
                    return
                await interaction.response.send_message("🗑️ Deleting your voice channel in 5 seconds...", ephemeral=True)
                await asyncio.sleep(5)
                await self.delete_temp_voice(voice_channel)
    
    @commands.group(name="temp", aliases=["tvc"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def temp(self, ctx):
        embed = discord.Embed(
            title="🎙️ Temp Voice System",
            description="**Commands:**\n"
                       "`!temp set <channel>` - Set the temp voice channel\n"
                       "`!temp remove` - Remove temp voice channel\n"
                       "`!temp info` - Show current settings\n"
                       "`!panel #channel` - Send control panel",
            color=COLORS["info"]
        )
        await ctx.send(embed=embed, delete_after=15)
    
    @temp.command(name="set", aliases=["setup", "تعيين"])
    @commands.has_permissions(administrator=True)
    async def temp_set(self, ctx, channel: discord.VoiceChannel):
        await db.set_temp_voice_channel(ctx.guild.id, channel.id)
        embed = discord.Embed(
            title=f"✅ Temp Voice Channel Set",
            description=f"**Channel:** {channel.mention}\n**ID:** `{channel.id}`\n\nMembers who join this channel will automatically get a private voice channel.",
            color=COLORS["success"]
        )
        await ctx.send(embed=embed, delete_after=10)
    
    @temp.command(name="remove", aliases=["delete", "حذف"])
    @commands.has_permissions(administrator=True)
    async def temp_remove(self, ctx):
        await db.remove_temp_voice_channel(ctx.guild.id)
        embed = discord.Embed(title=f"✅ Temp Voice Channel Removed", description="The temp voice system has been disabled.", color=COLORS["success"])
        await ctx.send(embed=embed, delete_after=10)
    
    @temp.command(name="info", aliases=["settings", "معلومات"])
    @commands.has_permissions(administrator=True)
    async def temp_info(self, ctx):
        channel_id = await db.get_temp_voice_channel(ctx.guild.id)
        embed = discord.Embed(title="🎙️ Temp Voice System Info", color=COLORS["info"])
        if channel_id:
            channel = ctx.guild.get_channel(int(channel_id))
            if channel:
                embed.add_field(name="📌 Temp Voice Channel", value=f"{channel.mention} (`{channel.id}`)", inline=False)
                embed.add_field(name="📊 Status", value="✅ **Active**", inline=False)
                embed.add_field(name="📈 Active Channels", value=str(len(self.active_channels)), inline=False)
            else:
                embed.add_field(name="📌 Temp Voice Channel", value=f"`{channel_id}` (Not found)", inline=False)
        else:
            embed.add_field(name="📌 Temp Voice Channel", value="Not set", inline=False)
            embed.add_field(name="💡 How to set", value="Use `!temp set #channel`", inline=False)
        await ctx.send(embed=embed, delete_after=15)
    
    @commands.command(name="panel", aliases=["لوحه"])
    @commands.has_permissions(administrator=True)
    async def panel(self, ctx, channel: discord.TextChannel = None):
        if not channel:
            channel = ctx.channel
        
        self.panel_channel_id = channel.id
        
        embed = discord.Embed(
            title="Drive 505 X Temp V",
            description="**Active Voice Channels:**\nNo active voice channels yet.",
            color=discord.Color.dark_gray()
        )
        
        embed.set_image(url="https://cdn.discordapp.com/attachments/1481632627558715565/1485515148478120116/file_000000002a44720aa8ea74a5d90c8596.png?ex=69c376ca&is=69c2254a&hm=8fbcf1cd775ca8c5b3a3b9b253d54778eb2d2409184cdd51cde57081713e68e8&")
        
        embed.add_field(name=" How to Use", value="Join the temp voice channel to create your private channel!", inline=False)
        embed.set_footer(text=f"Total Active : {len(self.active_channels)}")
        
        view = discord.ui.View(timeout=None)
        
        buttons = ["Name", "Limit", "Privacy", "Trust", "Untrust", "Invite", "Kick", "Region", "Block", "Unblock", "Transfer", "Delete"]
        for btn in buttons:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.secondary, label=btn, custom_id=f"control_{btn.lower()}"))
        
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label="Create Channel", emoji="🎉", custom_id="create_channel"))
        
        msg = await channel.send(embed=embed, view=view)
        self.panel_message_id = msg.id
        
        await ctx.send(f"✅ Control panel sent to {channel.mention}", delete_after=5)

async def setup(bot):
    await bot.add_cog(TempVoice(bot))