#!/usr/bin/env python3
# coding=utf-8

# Seen Module for Drastikbot
#
# It logs the last activity of every user posting and returns it upon request.
# It logs time, post, nickname, channel.
#
# user = The one used the bot (or posted a random line)
# nick = The nickname requested by the user

'''
Seen module for drastikbot.
Copyright (C) 2018, 2021-2022 drastik.org

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
from admin import is_bot_owner  # type: ignore


class Module:
    startup = True
    irc_commands = ["PRIVMSG"]
    manual = {
        "desc": ("See when a user was last seen posting in a channel the"
                 " bot has joined. If the user posted in channel other"
                 " than the one the command was given from, then the bot"
                 " will show that channel. Private messages with the bot"
                 " are NOT saved."),
        "bot_commands": {
            "seen": {"usage": lambda x: f"{x}seen <nickname>"},
            "info": ("Example: <Alice>: .seen Bob / <Bot>:"
                     " Bob was last seen 0:21:09 ago"
                     " [2018-06-25 13:36:42 UTC], saying .help seen")
        }
    }


def update(db, channel, nickname, message):
    timestamp = str(datetime.utcnow().replace(microsecond=0))

    with db:
        dbc = db.cursor()

        sql = """
            INSERT OR IGNORE INTO seen (nick, msg, time, channel)
            VALUES (?, ?, ?, ?);
        """
        dbc.execute(sql, (nickname, message, timestamp, channel))

        sql = """
            UPDATE seen SET msg=?, time=?, channel=?
            WHERE nick=?;
        """
        dbc.execute(sql, (message, timestamp, channel, nickname))


def fetch(db, nickname):
    dbc = db.cursor()
    sql = """
        SELECT nick, msg, time, channel
        FROM seen WHERE nick=?;
    """
    dbc.execute(sql, (nickname,))
    return dbc.fetchone()


# Output message preparation for .seen ###############################

def prep_message(i, fetchdata):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()

    requested_nick, msg, timestamp, channel = fetchdata
    ago, weekday, day, month, year, time, tz = prep_datetime(i, timestamp)
    is_ctcp_action, msg = prep_ctcp_action(msg)

    m = "\x0312"

    if is_ascii_cl(requested_nick, nickname):
        m += "You\x0F were"
    else:
        m += f"{requested_nick}\x0F was"

    m += (f" last seen \x0312{ago} ago\x0F"
          f" [{weekday} {day} {month} {year} {time} {tz}]")

    if is_ctcp_action:
        m += ", doing"
    else:
        m += ", saying"

    m += f" \x0312{msg}\x0F"

    if channel != msgtarget:
        m += f" in \x0312{channel}"

    return m


def prep_datetime(i, timestamp):
    conf = i.bot["conf"]

    d = datetime.fromisoformat(f"{timestamp}+00:00")

    ago = datetime.now(timezone.utc).replace(microsecond=0) - d

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

    return ago, weekday, d.day, month, d.year, d.time(), tz


def prep_ctcp_action(message):
    is_ctcp_action = False
    msg = message

    if "\x01ACTION " in msg[:8]:
        is_ctcp_action = True
        msg = msg[8:]
        if msg[-1] == "\x01":
            msg = msg[:-1]

    return is_ctcp_action, msg


# Commands ###########################################################

def seen(i, irc, db):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    argv = args.split()
    argc = len(argv)

    if not args:
        requested_nick = nickname
    elif (argc == 1 and len(args) <= 30):
        requested_nick = argv[0]
    else:
        m = f"Usage: {prefix}{botcmd} <nickname>"
        irc.out.notice(msgtarget, m)
        return

    # Check if the requested nickname is the bot's nickname
    if requested_nick == irc.curr_nickname:
        m = "\x0304Who?\x0F"
        irc.out.notice(msgtarget, m)
        return

    seen = fetch(db, requested_nick)

    if not seen:
        m = f"Sorry, I haven't seen \x0312{requested_nick}\x0F around"
        irc.out.notice(msgtarget, m)
    else:
        m = prep_message(i, seen)
        irc.out.notice(msgtarget, m)


# Main ###############################################################

def init(db):
    dbc = db.cursor()
    sql = """
        CREATE TABLE IF NOT EXISTS seen (
               nick TEXT COLLATE NOCASE PRIMARY KEY,
               msg TEXT,
               time TEXT,
               channel TEXT
        );
    """
    dbc.execute(sql)
    db.commit()


def main(i, irc):
    db = i.db_disk

    # Database initialization on startup
    if i.msg.is_command("__STARTUP"):
        init(db)
        return

    msgtarget = i.msg.get_msgtarget()
    ch_pfx = i.bot["conf"].get_channel_prefix(msgtarget)
    nickname = i.msg.get_nickname()
    is_pm = i.msg.is_pm()
    text = i.msg.get_text()

    # Database initialization by command
    if i.msg.is_botcmd("seen-initialize") and is_bot_owner(irc, nickname):
        irc.out.notice(nickname, "seen: database initialized")
        init(db)
        return

    # Handle the `seen' command, if any.
    if i.msg.is_botcmd("seen") and i.msg.is_botcmd_prefix(ch_pfx):
        seen(i, irc, db)

    # Save user messages.
    if not is_pm:  # PMs with the bot are not saved.
        update(db, msgtarget, nickname, text)
