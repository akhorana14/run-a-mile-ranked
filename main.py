import aiocron
import asyncio
import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
from helper import admin_guard
import helper
import db
import rr
import os
import pytz

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

EMBED_COLOR = 0x00ff00

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!mile ', intents=intents, help_command=None)

client = discord.Client(intents=intents)

loop = asyncio.get_event_loop()

timezone = pytz.timezone('America/Los_Angeles')

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    await bot.process_commands(message)

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.mention}!")

@bot.command()
async def help(ctx):
    description = "Welcome to Run A Mile Ranked! Here are the commands you can use:"
    commands = [
        "**!mile help**: Displays this help message.",
        "**!mile ranks**: Learn about the different ranks and their RR ranges.",
        "**!mile profile [@user]**: View your profile or another user's profile.",
        "**!mile leaderboard**: See the leaderboard!",
        "**!mile signup**: Signs you up for Run A Mile Ranked.",
        "**!mile log <distance>**: Logs a run, in miles.",
    ]
    help_embed = discord.Embed(title="Run A Mile Ranked Help", description=description, color=EMBED_COLOR)
    help_embed.add_field(name="Commands", value="\n".join(commands), inline=False)
    await ctx.send(embed=help_embed)

@bot.command()
async def ranks(ctx):
    description = "These are the ranks you can achieve based on your Run Rating (RR):"
    footnote = "Note: To achieve the Usain Bolt rank, you must be the top runner in the server with at least 750 RR."
    ranks = [f"**{rr.get_rank_icon(rank)} {rr.get_rank_name(rank)}**: {rr.get_rank_range(rank)}" for rank in rr.Rank]
    ranks_embed = discord.Embed(title="Run Ranks", description=description, color=EMBED_COLOR)
    ranks_embed.add_field(name="Run Ranks", value="\n".join(ranks), inline=False)
    ranks_embed.set_footer(text=footnote)
    await ctx.send(embed=ranks_embed)

@bot.command()
async def leaderboard(ctx):
    # TODO (akhorana): Implement a web-hosted leaderboard
    # For now, returns the leaderboard from the database in embed format
    leaderboard_embed = discord.Embed(title="Run A Mile Ranked Leaderboard", description="Top runners based on their Run Rating (RR).", color=EMBED_COLOR)
    leaderboard = db.get_leaderboard()
    if not leaderboard:
        leaderboard_embed.add_field(name="No runners yet!", value="Be the first to sign up and log a run!", inline=False)
        await ctx.send(embed=leaderboard_embed)
        return
    for user in leaderboard:
        discord_id = user[1]
        username = user[2]
        rr_value = user[5]
        rank = rr.get_rank(rr_value, user[6])
        rank_name = rr.get_rank_name(rank)
        rank_icon = rr.get_rank_icon(rank)
        leaderboard_embed.add_field(name=f"{rank_icon} {username}", value=f"RR: {rr_value} ({rank_name})", inline=False)
    await ctx.send(embed=leaderboard_embed)
    

@bot.command()
async def signup(ctx):
    db.setup()
    last_position = int(db.get_last_position()) + 1
    if (db.get_user(str(ctx.author.id)) is not None):
        await ctx.send(f"{ctx.author.mention}, you are already signed up for Run A Mile Ranked!")
        return
    db.add_new_user(str(ctx.author.id), str(ctx.author), last_position)
    await ctx.send(f"{ctx.author.mention}, you are now signed up for Run A Mile Ranked, Happy Running! :athletic_shoe:")

@bot.command()
async def profile(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    user = db.get_user(str(member.id))
    if user is None:
        await ctx.send(f"{ctx.author.mention}, {member.mention} is not signed up for Run A Mile Ranked. They can sign up using `!mile signup`.")
        return
    username = user[2]
    longest_streak = user[3]
    last_logged = user[4]
    rr_value = user[5]
    position = user[6]
    total_distance = user[8]
    runs_logged = user[7]
    average_distance = total_distance / runs_logged if runs_logged > 0 else 0
    rank = rr.get_rank(rr_value, position)
    rank_name = rr.get_rank_name(rank)
    rank_icon = rr.get_rank_icon(rank)
    profile_embed = discord.Embed(title=f"{rank_icon} {username}'s Profile", color=EMBED_COLOR)
    profile_embed.add_field(name="Rank", value=f"{rank_icon} {rank_name}", inline=False)
    profile_embed.add_field(name="Run Rating (RR)", value=str(rr_value), inline=False)
    profile_embed.add_field(name="Longest Streak (Days)", value=str(longest_streak), inline=False)
    profile_embed.add_field(name="Total Runs Logged", value=str(runs_logged), inline=False)
    profile_embed.add_field(name="Average Distance", value=str(average_distance), inline=False)
    profile_embed.add_field(name="Total Distance", value=str(total_distance), inline=False)
    profile_embed.add_field(name="Last Logged Run", value=str(last_logged) if last_logged else "No runs logged yet", inline=False)
    profile_embed.add_field(name="Leaderboard Position", value=str(position), inline=False)
    await ctx.send(embed=profile_embed)

# !mile log <distance> (assumes miles)
@bot.command()
async def log(ctx, *, entry: str):
    try:
        distance = float(entry)
        if distance <= 0:
            raise ValueError("Distance must be positive.")
    except ValueError:
        await ctx.send(f"{ctx.author.mention}, please provide a valid positive number for distance. Example: `!mile log 3.5`")
        return
    db.setup()
    user = db.get_user(str(ctx.author.id))
    if user is None:
        await ctx.send(f"{ctx.author.mention}, you are not signed up for Run A Mile Ranked. Please sign up using `!mile signup` before logging runs.")
        return
    now = pytz.datetime.datetime.now(tz=timezone)
    date_string = now.strftime("%Y-%m-%d")
    if user[4] == date_string:
        await ctx.send(f"{ctx.author.mention}, you have already logged a run today. You can only log one run per day.")
        return
    db.log_run(str(ctx.author.id), distance, date_string)
    db.update_leaderboard_positions()
    await ctx.send(f"{ctx.author.mention}, logged your run of {distance} miles! See your new RR on the leaderboard. Keep it up!")

# Static Admin Commands: Can only be used by konaxxx
# TODO (akhorana): Create an allowlist of admins that can use these commands
@bot.command()
async def adjust_rr(ctx, member: discord.Member, rr_value: int):
    if not admin_guard(ctx):
        return
    db.adjust_rr(str(member.id), rr_value)
    await ctx.send(f"{ctx.author.mention}, adjusted {member.mention}'s RR to {rr_value}.")

@bot.command()
async def reset_rr(ctx):
    if not admin_guard(ctx):
        return
    db.ADMIN_ONLY_reset_rr()
    await ctx.send(f"{ctx.author.mention}, reset all users' RR to 0.")

@bot.command()
async def delete_user(ctx, member: discord.Member):
    if not admin_guard(ctx):
        return
    db.ADMIN_ONLY_delete_user(str(member.id))
    await ctx.send(f"{ctx.author.mention}, deleted {member.mention} from the database.")

@bot.command()
async def delete_table(ctx):
    if not admin_guard(ctx):
        return
    db.ADMIN_ONLY_delete_table()
    await ctx.send(f"{ctx.author.mention}, deleted the users table from the database.")

@bot.command()
async def force_update_leaderboard(ctx):
    if not admin_guard(ctx):
        return
    db.update_leaderboard_positions()
    await ctx.send(f"{ctx.author.mention}, force updated the leaderboard positions.")

@bot.command()
async def force_log(ctx, member: discord.Member, distance: float):
    if not admin_guard(ctx):
        return
    db.setup()
    user = db.get_user(str(member.id))
    if user is None:
        await ctx.send(f"{ctx.author.mention}, {member.mention} is not signed up for Run A Mile Ranked.")
        return
    now = pytz.datetime.datetime.now(tz=timezone)
    date_string = now.strftime("%Y-%m-%d")
    if user[4] == date_string:
        await ctx.send(f"{ctx.author.mention}, {member.mention} has already logged a run today.")
        return
    db.log_run(str(member.id), distance, date_string)
    db.update_leaderboard_positions()
    await ctx.send(f"{ctx.author.mention}, force logged a run of {distance} miles for {member.mention}.")

@bot.command()
async def force_update_streak(ctx, member: discord.Member, streak: int):
    if not admin_guard(ctx):
        return
    user = db.get_user(str(member.id))
    if user is None:
        await ctx.send(f"{ctx.author.mention}, {member.mention} is not signed up for Run A Mile Ranked.")
        return
    db.update_user(str(member.id), longest_streak=streak)
    await ctx.send(f"{ctx.author.mention}, force updated {member.mention}'s longest streak to {streak} days.")

# Periodic Tasks, managing the RR lifecycle and season resets.

announcement_channel_id = 1422105352144425011 # Alex's Server - #run-a-mile-ranked channel

# Daily at midnight PST, announce the end of the day and the RR losses for the players who didn't log a run
@aiocron.crontab('0 0 * * *', tz=timezone, start=False, loop=loop) # Every day at midnight PST
async def daily_rr_management():
    print("Daily rr management task executed.")
    embeds = helper.daily_rr_message(timezone, bot, announcement_channel_id)
    channel = bot.get_channel(announcement_channel_id)
    if channel:
        if embeds:
            for embed in embeds:
                if embed:
                    await channel.send(embed=embed)
    else:
        print("Error: Announcement channel not found: could not send daily RR embeds")

@aiocron.crontab('0 0 1 * *', tz=timezone, start=False, loop=loop) # First day of every month at midnight PST
async def monthly_season_reset():
    # TODO (akhorana): Implement monthly season reset, resetting RR and announcing winners
    print("Monthly season reset task executed.")
    channel = bot.get_channel(announcement_channel_id)
    if channel:
        await channel.send("The monthly season has reset! Check out the new leaderboard and keep running!")

# Admin Commands for periodic tasks
@bot.command()
async def mock_daily_rr_change(ctx):
    if not admin_guard(ctx):
        return
    embeds = helper.daily_rr_message(timezone, bot, announcement_channel_id)
    if embeds:
        for embed in embeds:
            if embed:
                await ctx.send(embed=embed)
    await ctx.send(f"{ctx.author.mention}, mock daily RR change executed.")

async def main():
    async with bot:
        daily_rr_management.start()
        monthly_season_reset.start()
        await bot.start(DISCORD_TOKEN)

loop.run_until_complete(main())