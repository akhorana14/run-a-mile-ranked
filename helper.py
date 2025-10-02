# Helper class for managing commands between admin and bot executed commands

import discord
import pytz
import timedelta

import db
import rr

EMBED_COLOR = 0x00ff00

def admin_guard(ctx):
    if str(ctx.author) != "konaxxx":
        return False
    return True

def daily_rr_message(timezone, bot, announcement_channel_id):
    now = pytz.datetime.datetime.now(tz=timezone)
    yesterday = now - timedelta(days=1)
    date_string = timezone.localize(yesterday).strftime("%Y-%m-%d")
    date_embed_string = timezone.localize(yesterday).strftime("%A, %B %d")
    users_who_didnt_log = db.get_users_who_didnt_log_today(date_string)
    description = "It's the end of the day, and you didn't log your run!"
    if users_who_didnt_log == []:
        description = "Congratulations! Everyone logged their runs today!"
    day_end_embed = discord.Embed(title="End of " + date_embed_string, description=description, color=EMBED_COLOR)
    rank_loss_embed = discord.Embed(title="Rank Changes", description="The following users deranked because they didn't run today:", color=EMBED_COLOR)
    # A mapping of user, previous rank, new rank
    rank_loss_mapping = {}
    for user in users_who_didnt_log:
        discord_id = user[1]
        username = user[2]
        rr_value = user[5]
        position = user[6]
        rank = rr.get_rank(rr_value, position)
        rank_name = rr.get_rank_name(rank)
        rank_icon = rr.get_rank_icon(rank)
        total_rr_loss = 10 # TODO (akhorana): Calculate RR loss based on rank, longest streak, etc.
        # TODO (akhorana): Update total_rr_loss logic. total_rr_loss should account that the user doesn't go below 0RR.
        new_rr_value = max(0, rr_value - total_rr_loss)  # RR cannot go below 0
        new_rank = rr.get_rank(new_rr_value, position)
        if (new_rank != rank):
            rank_loss_mapping[username] = (rank, new_rank)
        db.adjust_rr(discord_id, new_rr_value)
        day_end_embed.add_field(name=f"{rank_icon} {username}", value=f"RR: {rr_value} -> {new_rr_value} (Lost {total_rr_loss} RR)", inline=False)
    if rank_loss_mapping:
        for username, (old_rank, new_rank) in rank_loss_mapping.items():
            old_rank_name = rr.get_rank_name(old_rank)
            new_rank_name = rr.get_rank_name(new_rank)
            old_rank_icon = rr.get_rank_icon(old_rank)
            new_rank_icon = rr.get_rank_icon(new_rank)
            rank_loss_embed.add_field(name=f"{old_rank_icon} {username}", value=f"{old_rank_icon} {old_rank_name} -> {new_rank_icon} {new_rank_name}", inline=False)
    if rank_loss_mapping:
        return day_end_embed, rank_loss_embed
    return day_end_embed, None