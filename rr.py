# Ranked calculation for the RR (Run Rank Points) system
# Each user has a rank that increases when they log runs of 1 mile or more
# and decreases when they log runs of less than 1 mile.
# The higher your RR, the lower RR gains you recieve for each run logged. This goes 
# This encourages consistent running and rewards longer runs.
# Also, the higher your streak, the more points you get for each run logged.

import db
from enum import Enum
import math

BRONZE_RR_START = 0
BRONZE_RR_END = 99

SILVER_RR_START = 100
SILVER_RR_END = 199

GOLD_RR_START = 200
GOLD_RR_END = 299

PLATINUM_RR_START = 300
PLATINUM_RR_END = 399

DIAMOND_RR_START = 400
DIAMOND_RR_END = 499

MASTER_RR_START = 500
MASTER_RR_END = 749

GRANDMASTER_RR_START = 750
GRANDMASTER_RR_END = float('inf')

USAIN_BOLT_RR_START = 750
USAIN_BOLT_RR_END = float('inf')


# Heuristic to calculate RR based on distance and longest streak
# you should start out getting a good amount of rr at lower ranks, and then there should be a slight reduction as you get to higher ranks
# If you have a long streak, you should get a small bonus corresponding to your streak
# If you log less than a mile or don't log a run, at higher ranks you will lose rr proportional to how high up you are
# If you log between 1-2 miles, you get a +1/+2 rr bonus, if you log 2-5 miles you get a +2/+3 rr bonus. just to reward more running, but also not promote running an ungodly amount
# You should always be rewarded and gain RR for running a mile.
# The RR system will look similar to the RR system in VALORANT, but with a few changes to promote consistent running and longer runs. 

# We will use the following metrics:
# 1. Rank (BRONZE, SILVER, GOLD, PLATINUM, DIAMOND, MASTER, GRANDMASTER) - determines the base rr gain/loss
# 2. Longest Streak - determines a small bonus to rr gain/loss in a logarithmic scale
# 3. Distance run - determines the rr gain/loss for the run

# A streak starts at 3 consecutive days of logging a run, and increases in a logarithmic scale
# A streak is broken if a user does not log a run for a day.
def get_longest_streak_bonus(longest_streak):
    if longest_streak == 0:
        return 0
    return math.floor(math.log(longest_streak, 3))

def get_base_rr_gain(rank):
    if rank == Rank.BRONZE:
        return 25
    elif rank == Rank.SILVER:
        return 24
    elif rank == Rank.GOLD:
        return 23
    elif rank == Rank.PLATINUM:
        return 22
    elif rank == Rank.DIAMOND:
        return 20
    elif rank == Rank.MASTER:
        return 18
    elif rank == Rank.GRANDMASTER or rank == Rank.USAIN_BOLT:
        return 17
    else:
        print("Error: Invalid rank in get_base_rr_gain")
        return 0

def get_base_rr_loss(rank):
    # For Bronze, Silver, Gold, there is no RR loss.
    if rank == Rank.BRONZE or rank == Rank.SILVER or rank == Rank.GOLD:
        return 0
    elif rank == Rank.PLATINUM:
        return 5
    elif rank == Rank.DIAMOND:
        return 7
    elif rank == Rank.MASTER:
        return 12
    elif rank == Rank.GRANDMASTER:
        return 17
    elif rank == Rank.USAIN_BOLT:
        return 22
    else:
        print("Error: Invalid rank in get_base_rr_loss")
        return 0
    
# Distance multiplier to multiply the base rr gain/loss to help promote submitting a run, even if it's less than a mile
def get_distance_multiplier(distance):
    if distance < 1.0:
        return -(1 - distance)
    else:
        return 1.0

# Distance bonus to add to the rr gain to reward longer runs
def get_distance_bonus(distance):
    if distance <= 1.0:
        return 0
    elif distance <= 2.0:
        return 1
    elif distance <= 5.0:
        return 2
    else:
        return 3

# Calculates rr gain for a user who logged a run today
def calculate_rr_logged(user, distance):
    rank = get_rank(user[5], user[6])
    longest_streak = user[3] + 1
    base_rr_gain = get_base_rr_gain(rank)
    streak_bonus = get_longest_streak_bonus(longest_streak)
    distance_multiplier = get_distance_multiplier(distance)
    distance_bonus = get_distance_bonus(distance)
    total_rr_gain = math.ceil((base_rr_gain + streak_bonus + distance_bonus) * distance_multiplier)
    new_rr = max(0, user[5] + total_rr_gain)  # RR cannot go below 0
    return new_rr

# Calculates rr loss for a user who did not log a run today
def calculate_rr_no_log(user):
    rank = get_rank(user[5], user[6])
    base_rr_loss = get_base_rr_loss(rank)
    longest_streak = user[3]
    new_rr = max(0, user[5] - base_rr_loss)  # RR cannot go below 0
    return new_rr

class Rank(Enum):
    BRONZE = 0 # 0 - 99 RR
    SILVER = 1 # 100 - 199 RR
    GOLD = 2 # 200 - 299 RR
    PLATINUM = 3 # 300 - 399 RR
    DIAMOND = 4 # 400 - 499 RR
    MASTER = 5 # 500 - 749 RR
    GRANDMASTER = 6 # 750 RR +
    USAIN_BOLT = 7 # Rank 1. Must be Grandmaster, and top 1 in RR.

def get_rank(rr, position):
    if rr < get_rank_start(Rank.SILVER):
        return Rank.BRONZE
    elif rr < get_rank_start(Rank.GOLD):
        return Rank.SILVER
    elif rr < get_rank_start(Rank.PLATINUM):
        return Rank.GOLD
    elif rr < get_rank_start(Rank.DIAMOND):
        return Rank.PLATINUM
    elif rr < get_rank_start(Rank.MASTER):
        return Rank.DIAMOND
    elif rr < get_rank_start(Rank.GRANDMASTER):
        return Rank.MASTER
    elif rr >= get_rank_start(Rank.GRANDMASTER) and position > 1:
        return Rank.GRANDMASTER
    else:
        return Rank.USAIN_BOLT
    
def get_rank_name(rank):
    if rank == Rank.BRONZE:
        return "Bronze"
    elif rank == Rank.SILVER:
        return "Silver"
    elif rank == Rank.GOLD:
        return "Gold"
    elif rank == Rank.PLATINUM:
        return "Platinum"
    elif rank == Rank.DIAMOND:
        return "Diamond"
    elif rank == Rank.MASTER:
        return "Master"
    elif rank == Rank.GRANDMASTER:
        return "Grandmaster"
    elif rank == Rank.USAIN_BOLT:
        return "Usain Bolt"
    else:
        return "Unknown Rank"
    
def get_rank_icon(rank):
    if rank == Rank.BRONZE:
        return "🥉"
    elif rank == Rank.SILVER:
        return "🥈"
    elif rank == Rank.GOLD:
        return "🥇"
    elif rank == Rank.PLATINUM:
        return "💿"
    elif rank == Rank.DIAMOND:
        return "💎"
    elif rank == Rank.MASTER:
        return "👑"
    elif rank == Rank.GRANDMASTER:
        return "🏆"
    elif rank == Rank.USAIN_BOLT:
        return "⚡"
    else:
        return "❓"
    
def get_rank_start(rank):
    if rank == Rank.BRONZE:
        return BRONZE_RR_START
    elif rank == Rank.SILVER:
        return SILVER_RR_START
    elif rank == Rank.GOLD:
        return GOLD_RR_START
    elif rank == Rank.PLATINUM:
        return PLATINUM_RR_START
    elif rank == Rank.DIAMOND:
        return DIAMOND_RR_START
    elif rank == Rank.MASTER:
        return MASTER_RR_START
    elif rank == Rank.GRANDMASTER:
        return GRANDMASTER_RR_START
    elif rank == Rank.USAIN_BOLT:
        return USAIN_BOLT_RR_START
    else:
        return -1

def get_rank_end(rank):
    if rank == Rank.BRONZE:
        return BRONZE_RR_END
    elif rank == Rank.SILVER:
        return SILVER_RR_END
    elif rank == Rank.GOLD:
        return GOLD_RR_END
    elif rank == Rank.PLATINUM:
        return PLATINUM_RR_END
    elif rank == Rank.DIAMOND:
        return DIAMOND_RR_END
    elif rank == Rank.MASTER:
        return MASTER_RR_END
    elif rank == Rank.GRANDMASTER:
        return float('inf')
    elif rank == Rank.USAIN_BOLT:
        return float('inf')
    else:
        return -1
    
def get_rank_range(rank):
    if get_rank_end(rank) == float('inf'):
        return f"{get_rank_start(rank)}+"
    else:
        return f"{get_rank_start(rank)} - {get_rank_end(rank)}"
    