# utils/helpers.py
import discord
from discord.ext import commands
import asyncio
import re
import config

async def get_member(ctx, user_input=None):
    """جلب العضو من منشن أو ريبلاي أو ID - محسنة"""
    
    # الحالة 1: ريبلاي
    if ctx.message.reference and not user_input:
        try:
            msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            return msg.author
        except:
            return None
    
    # الحالة 2: إدخال نص
    if user_input:
        # تنظيف المنشن
        clean_input = re.sub(r'[<@!>]', '', user_input.split()[0] if user_input.split() else user_input)
        
        try:
            if clean_input.isdigit():
                return await ctx.guild.fetch_member(int(clean_input))
            return await commands.MemberConverter().convert(ctx, user_input)
        except:
            return None
    
    return None

async def delete_command(message, delay=0):
    """لا تمسح رسالة المستخدم"""
    pass

async def delete_response(message, delay=config.DELETE_RESPONSE_DELAY):
    """حذف رسالة البوت بعد تأخير"""
    if not message:
        return
    try:
        await asyncio.sleep(delay)
        await message.delete()
    except:
        pass

async def send_and_delete(ctx, embed, delete_after=config.DELETE_RESPONSE_DELAY):
    """إرسال رسالة وحذفها تلقائياً"""
    msg = await ctx.send(embed=embed)
    await delete_response(msg, delete_after)
    return msg

async def send_permanent(ctx, embed):
    """إرسال رسالة دائمة"""
    return await ctx.send(embed=embed)