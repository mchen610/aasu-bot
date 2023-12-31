from discord import Embed, Color
from discord.ext.commands import Context
from datetime import datetime

def get_error_msg(msg: str):
    return Embed(description=f"Error: **{msg}**", color=Color.red(), timestamp=datetime.now())

def get_pending_msg(msg: str):
    return Embed(description=f"Pending: **{msg}**", color=Color.yellow(), timestamp=datetime.now())

def get_success_msg(msg: str):
    return Embed(description=f"Success: **{msg}**", color=Color.brand_green(), timestamp=datetime.now())

async def send_error_msg(ctx: Context, msg: str):
    await ctx.respond(embed=get_error_msg(msg))

async def send_pending_msg(ctx, msg: str):
    await ctx.respond(embed=get_pending_msg(msg))

async def send_success_msg(ctx, msg: str):
    await ctx.respond(embed=get_success_msg(msg))
