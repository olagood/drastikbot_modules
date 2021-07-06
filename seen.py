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
Copyright (C) 2018, 2021 drastik.org

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

import datetime

from dbothelper import is_ascii_cl
from admin import is_bot_owner


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
    dbc = db.cursor()
    timestamp = str(datetime.datetime.utcnow().replace(microsecond=0))

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
    db.commit()


def fetch(db, nickname):
    dbc = db.cursor()
    sql = """
        SELECT nick, msg, time, channel
        FROM seen WHERE nick=?;
    """
    dbc.execute(sql, (nickname,))
    return dbc.fetchone()


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


def seen(i, irc, db):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    argv = args.split()
    argc = len(argv)

    if not args:
        rq_nick = nickname
    elif (argc == 1 and len(args) <= 30):
        rq_nick = argv[0]
    else:
        m = f"Usage: {prefix}{botcmd} <nickname>"
        irc.out.notice(msgtarget, m)
        return

    # Check if the requested nickname is the bot's nickname
    if rq_nick == irc.curr_nickname:
        m = "\x0304Who?\x0F"
        irc.out.notice(msgtarget, m)
        return

    seen = fetch(db, rq_nick)

    if not seen:
        m = f"Sorry, I haven't seen \x0312{rq_nick}\x0F around"
        irc.out.notice(msgtarget, m)
        return

    # s_nickname = seen[0]
    s_message = seen[1]
    s_time = datetime.datetime.strptime(seen[2], "%Y-%m-%d %H:%M:%S")
    s_channel = seen[3]

    time_now = datetime.datetime.utcnow().replace(microsecond=0)
    s_ago = time_now - s_time

    ctcp_action = False
    if "\x01ACTION " in s_message[:8]:
        ctcp_action = True
        s_message = s_message[8:]
        if s_message[-1] == "\x01":
            s_message = s_message[:-1]

    m = "\x0312"

    if is_ascii_cl(rq_nick, nickname):
        m += "You\x0F were"
    else:
        m += f"{rq_nick}\x0F was"

    m += f" last seen \x0312{s_ago} ago\x0F [{s_time} UTC]"

    if ctcp_action:
        m += ", doing"
    else:
        m += ", saying"

    m += f" \x0312{s_message}\x0F"

    if s_channel != msgtarget:
        m += f" in \x0312{s_channel}"

    irc.out.notice(msgtarget, m)


def main(i, irc):
    db = i.db_disk

    # Database initialization on startup
    if i.msg.is_command("__STARTUP"):
        init(db)
        return

    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    is_pm = i.msg.is_pm()
    text = i.msg.get_text()

    # Database initialization by command
    if i.msg.is_botcmd("seen-initialize") and is_bot_owner(irc, nickname):
        irc.out.notice(nickname, "seen: database initialized")
        init(db)
        return

    # Handle the `seen' command, if any.
    if i.msg.is_botcmd("seen"):
        seen(i, irc, db)

    # Save user messages.
    if not is_pm:  # PMs with the bot are not saved.
        update(db, msgtarget, nickname, text)
