#!/usr/bin/env python3
# coding=utf-8

# Tell Module for Drastikbot
#
# It works "like" memoserv.
# A user tells the bot to tell a message to a nick when that nick is seen.
# .tell drastik drastikbot is down | .tell <NICKNAME> <MESSAGE>
#
# Depends
# -------
# drastikbot_modules: url.py

'''
Copyright (C) 2017, 2021-2022 drastik.org

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from dbothelper import is_ascii_cl, get_day_str, get_month_str  # type: ignore
from ignore import is_ignored  # type: ignore

# Try to import the url module from drastikbot_modules to provide url titles.
try:
    import url
    url_support = True
except ImportError:
    url_support = False


class Module:
    startup = True
    irc_commands = ["PRIVMSG"]
    manual = {
        "desc": (
            "Send a message to a user through the bot. This is used to"
            " send messages to users that are AFK or not connected to "
            "the server. The bot will message the receiver as soon as "
            "they post to a channel that the bot has joined."
        ),
        "bot_commands": {
            "tell": {"usage": lambda x: f"{x}tell <receiver> <message>"},
            "yell": {"usage": lambda x: f"{x}yell <receiver> <message>"}
        }
    }


# ====================================================================
# Insert messages in the db
# ====================================================================

def add(i, irc, upper=False):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()

    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()

    args = i.msg.get_args()
    argv = args.split(" ", 1)

    try:
        receiver = argv[0]
        message = argv[1]
    except IndexError:
        m = f"Usage: {prefix}{botcmd} <receiver> <message>"
        irc.out.notice(msgtarget, m)
        return

    if upper:
        message = message.upper()

    if is_ascii_cl(irc.curr_nickname, receiver):
        m = f"{nickname}: I am here now, tell me."
        irc.out.notice(msgtarget, m)
        return

    if is_ignored(i, irc, receiver, nickname):
        return  # do not say anything

    db_insert(i, receiver, message, nickname, msgtarget)

    if i.msg.is_nickname(receiver):
        m = f'{nickname}: When you return, I will notify'
        irc.out.notice(msgtarget, m)
    else:
        m = f'{nickname}: When {receiver} returns, I will notify.'
        irc.out.notice(msgtarget, m)


def db_insert(i, receiver, msg, sender, msgtarget):
    db = i.db_disk
    dbc = db.cursor()

    timestamp = datetime.utcnow().replace(microsecond=0)
    sql = """
        INSERT INTO tell VALUES (?, ?, ?, ?, strftime('%s', 'now'), ?);
    """
    dbc.execute(sql, (receiver, msg, sender, str(timestamp), msgtarget))

    db.commit()


# ====================================================================
# Pull messages from the db
# ====================================================================

def find(i, irc):
    db = i.db_disk
    dbc = db.cursor()
    nick = i.msg.get_nickname()

    sql = """
        SELECT sender, msg, timestamp, channel FROM tell WHERE receiver=?;
    """
    dbc.execute(sql, (nick,))

    fetch = dbc.fetchall()
    if not fetch:
        return

    for x in fetch:
        header, msg = prep_message(i, x)
        irc.out.privmsg(nick, header)
        irc.out.privmsg(nick, msg)
        # Also show the titles for any urls in the msg
        if not url_support:
            continue
        for (_status, title) in url.get_titles_from_text(msg, limit=3):
            irc.out.privmsg(nick, title)

    dbc.execute("DELETE FROM tell WHERE receiver=?;", (nick,))
    # Delete messages older than 3600 * 24 * 30 * 3 seconds.
    sql = """
        DELETE FROM tell
        WHERE (strftime('%s', 'now') - date) > (3600 * 24 * 30 * 3);
    """
    dbc.execute(sql)

    db.commit()


def prep_message(i, fetchdata):
    conf = i.bot["conf"]
    sender, msg, timestamp, channel = fetchdata

    d = datetime.fromisoformat(f"{timestamp}+00:00")

    # Get the timezone from the config file and convert the datetime object
    # or remain in UTC
    try:
        tz = conf.conf["ui"]["timezone"]
        # Add the timezone to get a timezone aware object
        d = d.astimezone(tz=ZoneInfo(tz))
    except KeyError:
        tz = "UTC"

    weekday = get_day_str(d.weekday())
    month = get_month_str(d.month)

    header = (f'\x02\x0312{sender}\x0F'
              f' \x0315[{weekday} {d.day} {month} {d.year}'
              f' {d.time()} {tz}]\x0F')
    if sender == channel:
        header += " \x0304[Private]\x0F:"
    else:
        header += f" \x0303[{channel}]\x0F:"
    return header, msg


# ====================================================================
# Intialization / Migrations
# ====================================================================

def db_init(i):
    db = i.db_disk
    dbc = db.cursor()

    dbc.executescript("""
    CREATE TABLE IF NOT EXISTS tell (
        receiver  TEXT COLLATE NOCASE,
        msg       TEXT,
        sender    TEXT,
        timestamp TEXT,
        date      INTEGER,
        channel   TEXT);
    """)

    # Migration code :: added 2022/20/4 :: delete after 2023/20/4
    dbc.execute("PRAGMA table_info(tell);")
    if not any([x[1] == "channel" for x in dbc.fetchall()]):
        dbc.execute("ALTER TABLE tell ADD COLUMN channel TEXT;")

    db.commit()


# ====================================================================
# Main
# ====================================================================

def main(i, irc):
    try:
        botcmd = i.msg.get_botcmd()
    except AttributeError:
        botcmd = i.msg.get_command()  # __STARTUP

    if "__STARTUP" == botcmd:
        db_init(i)
        return

    msgtarget = i.msg.get_msgtarget()
    ch_pfx = i.bot["conf"].get_channel_prefix(msgtarget)

    find(i, irc)

    if i.msg.is_botcmd_prefix(ch_pfx):
        if "tell-initialize" == botcmd:
            db_init(i)

        if "tell" == botcmd:
            add(i, irc)

        if "yell" == botcmd:
            add(i, irc, upper=True)
