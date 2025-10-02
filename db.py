import sqlite3
import rr as rrsystem

# Database class to handle keeping track of user stats.

conn = sqlite3.connect('ranked_stats.db')
c = conn.cursor()

# Setup the database tables
def setup():
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            discord_id TEXT UNIQUE,
            username TEXT,
            longest_streak REAL DEFAULT 0,
            last_logged DATE,
            rr INTEGER DEFAULT 0,
            leaderboard_position INTEGER,
            runs_logged INTEGER DEFAULT 0,
            total_distance DOUBLE DEFAULT 0.0
        )
    ''')
    conn.commit()

# Accessors

def get_last_position() -> int:
    # Get the highest leaderboard position currently in use
    c.execute('SELECT MAX(leaderboard_position) FROM users')
    result = c.fetchone()
    return result[0] if result[0] is not None else 0

def get_user(discord_id):
    c.execute('SELECT * FROM users WHERE discord_id = ?', (discord_id,))
    return c.fetchone()

def get_leaderboard():
    c.execute('SELECT * FROM users ORDER BY leaderboard_position ASC')
    return c.fetchall()

def get_users_who_didnt_log_today(date):
    c.execute('SELECT * FROM users WHERE last_logged != ? OR last_logged IS NULL', (date,))
    return c.fetchall()

# Mutators

def add_new_user(discord_id, username, position: int):
    c.execute('INSERT OR IGNORE INTO users (discord_id, username, leaderboard_position) VALUES (?, ?, ?)', (discord_id, username, position))
    conn.commit()

def log_run(discord_id, distance, date):
    user = get_user(discord_id)
    if user:
        new_rr = rrsystem.calculate_rr_logged(user, distance)
        update_user(user[1], longest_streak=user[3] + 1, last_logged=date, rr=new_rr, runs_logged=user[7] + 1, total_distance=user[8] + distance)

def adjust_rr(discord_id, rr):
    c.execute('UPDATE users SET rr = ? WHERE discord_id = ?', (rr, discord_id))
    conn.commit()

def update_user(discord_id, longest_streak=None, last_logged=None, rr=None, leaderboard_position=None, runs_logged=None, total_distance=None):
    user = get_user(discord_id)
    if not user:
        return
    if longest_streak is None:
        longest_streak = user[3]
    if last_logged is None:
        last_logged = user[4]
    if rr is None:
        rr = user[5]
    if leaderboard_position is None:
        leaderboard_position = user[6]
    if runs_logged is None:
        runs_logged = user[7]
    if total_distance is None:
        total_distance = user[8]
    c.execute('''
        UPDATE users 
        SET longest_streak = ?, last_logged = ?, rr = ?, leaderboard_position = ?, runs_logged = ?, total_distance = ? 
        WHERE discord_id = ?
    ''', (longest_streak, last_logged, rr, leaderboard_position, runs_logged, total_distance, discord_id))
    conn.commit()

def update_leaderboard_positions():
    c.execute('SELECT discord_id, rr FROM users ORDER BY rr DESC')
    users = c.fetchall()
    for position, (discord_id, rr) in enumerate(users, start=1):
        c.execute('UPDATE users SET leaderboard_position = ? WHERE discord_id = ?', (position, discord_id))
    conn.commit()

# Admin Mutators (Guarded behind admin-only commands)

def ADMIN_ONLY_reset_rr():
    c.execute('UPDATE users SET rr = 0')
    conn.commit()

def ADMIN_ONLY_delete_user(discord_id):
    c.execute('DELETE FROM users WHERE discord_id = ?', (discord_id,))
    conn.commit()

def ADMIN_ONLY_delete_table():
    c.execute('DROP TABLE IF EXISTS users')
    conn.commit()

def __init__(self):
    setup()