# cogs/fun/setgif.py
import discord
from discord.ext import commands
from utils.helpers import delete_command, send_and_delete
from utils.embeds import success_embed, error_embed
from utils.checks import check_permission

class SetGif(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="setgif", aliases=["تعيين_جيف"])
    @commands.has_permissions(administrator=True)
    @check_permission("setgif")
    async def setgif(self, ctx, command_name=None, *, gif_url=None):
        """تخصيص GIF لأمر - !setgif marry https://gif.link"""
        
        await delete_command(ctx.message)
        
        if not command_name or not gif_url:
            await send_and_delete(ctx, error_embed("Missing Arguments", "Usage: `!setgif <command> <gif_url>`\nCommands: marry, goodnight, ez"))
            return
        
        valid_commands = ["marry", "goodnight", "ez"]
        if command_name.lower() not in valid_commands:
            await send_and_delete(ctx, error_embed("Invalid Command", f"Command must be one of: {', '.join(valid_commands)}"))
            return
        
        # تحديث الـ GIF في الـ Cog المناسب
        cog_name = command_name.capitalize()
        cog = self.bot.get_cog(cog_name)
        
        if cog and hasattr(cog, "gifs"):
            cog.gifs[command_name.lower()] = gif_url
            embed = success_embed(
                "GIF Updated",
                f"GIF for `{command_name}` has been updated successfully.\n**New URL:** {gif_url}"
            )
        else:
            embed = success_embed(
                "GIF Updated (Temporary)",
                f"GIF for `{command_name}` has been set to:\n{gif_url}\n\n*Note: This will reset when the bot restarts.*"
            )
            # تخزين مؤقت
            if not hasattr(self.bot, "custom_gifs"):
                self.bot.custom_gifs = {}
            self.bot.custom_gifs[command_name.lower()] = gif_url
        
        await send_and_delete(ctx, embed)

async def setup(bot):
    await bot.add_cog(SetGif(bot))