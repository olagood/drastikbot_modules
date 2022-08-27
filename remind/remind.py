#!/usr/bin/env python3
# coding=utf-8

# Reminder Module for Drastikbot
#
# It sends user requested messages after a period of time.

'''
Remind module for drastikbot.
Copyright (C) 2022 drastik.org

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

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from dbothelper import get_day_str, get_month_str  # type: ignore
from admin import is_bot_owner  # type: ignore


class Module:
    startup = True
    bot_commands = [
        "remind",
        "remindme", "remind_me", "remind-me",
        "remind-initialize",
        "remind-delete"
    ]
    manual = {
        "desc": ("Set reminders for yourself or for other users."),
        "bot_commands": {
            "remind": {
                "usage": lambda x: f"{x}remind <nick> in <interval> <text>",
                "info": ("<interval>: An expression such as ``7 mins''."
                         " Example: .remind drastik in 7 mins to cook dinner")
            },
            "remindme": {
                "usage": lambda x: f"{x}remindme in <interval> <text>",
                "info": ("Like remind but it will always send the reminders"
                         " to you"),
                "alias": ["remind_me", "remind-me"]
            },
            "remind-delete": {
                "usage": lambda x: f"{x}remind-delete <id>",
                "info": ("When you set a reminder an id is returned. You can"
                         " use this id to delete reminders with this command."
                         " Example: .remind-delete 5")
            }
        }
    }


# Database ###########################################################

def add_reminder(db, receiver, added_by, message, channel, timestamp):
    dbc = db.cursor()

    sql = """
        INSERT INTO remind (receiver, added_by, message, channel, timestamp)
        VALUES (?, ?, ?, ?, ?);
    """
    dbc.execute(sql, (receiver, added_by, message, channel, timestamp))
    db.commit()
    return dbc.lastrowid


def delete_reminder(db, id, receiver):
    dbc = db.cursor()
    sql = """
        DELETE FROM remind
        WHERE id = ? AND (receiver = ? OR added_by = ?);
    """
    dbc.execute(sql, (id, receiver, receiver))
    db.commit()


def is_deleted(db, id) -> bool:
    dbc = db.cursor()
    sql = """
        SELECT * FROM remind WHERE id = ?;
    """
    dbc.execute(sql, (id,))
    return dbc.fetchone() is None


def has_delete_rights(db, id, nickname) -> bool:
    dbc = db.cursor()
    sql = """
        SELECT * FROM remind
        WHERE id = ? AND (receiver = ? OR added_by = ?);
    """
    dbc.execute(sql, (id, nickname, nickname))
    return (not (dbc.fetchone() is None))


# Date expression parser #############################################

calendricals = {
    "seconds": 1,
    "second": 1,
    "secs": 1,
    "sec": 1,
    "s": 1,

    "minutes": 60,
    "minute": 60,
    "mins": 60,
    "min": 60,
    "m": 60,

    "hours": 3600,
    "hour": 3600,
    "hrs": 3600,
    "hr": 3600,
    "h": 3600,

    "days": 3600 * 24,
    "day": 3600 * 24,
    "d": 3600 * 24,

    "weeks": 3600 * 24 * 7,
    "week": 3600 * 24 * 7,
    "wks": 3600 * 24 * 7,
    "wk": 3600 * 24 * 7,
    "w": 3600 * 24 * 7,

    "months": 3600 * 24 * 30,
    "month": 3600 * 24 * 30,
    "mon": 3600 * 24 * 30,
    "M": 3600 * 24 * 30
}


def parse_interval(text):
    return _parse_interval(text, 0)


def _parse_interval(text, acc):
    digits, rest = parse_digits(text)
    if not digits:
        if acc == 0:
            return None
        else:
            return acc, text

    rest = rest.strip()

    tokens = rest.split(" ", 1)
    if not tokens:
        if acc == 0:
            return None
        else:
            return acc, text

    calendrical = tokens[0]
    if calendrical[-1] == ",":  # As in 1day, 2hours
        calendrical = calendrical[:-1]
        if len(tokens) == 2:  # put the "," in the `rest' part
            tokens[1] = "," + tokens[1]

    # Try to match capitalized shortcuts
    multiplier = calendricals.get(calendrical, False)

    # Try to match everything else
    if not multiplier:
        multiplier = calendricals.get(calendrical.lower(), False)

    if not multiplier:
        return None

    try:
        rest = tokens[1].strip()
    except IndexError:
        rest = ""

    interval = int(digits) * multiplier

    if rest[:3].lower() == "and":
        return _parse_interval(rest[3:].strip(), acc + interval)
    elif rest[:1] == ",":
        return _parse_interval(rest[1:].strip(), acc + interval)
    else:
        return acc + interval, rest


def parse_digits(text):
    acc = ""
    for i, c in enumerate(text):
        if c.isdigit():
            acc += c
            continue

        if acc == "":
            return False, text
        else:
            return int(acc), text[i:]


# ====================================================================
# Output preparation and formatting
# ====================================================================

def msg_added(i, id, receiver, dt):
    nickname = i.msg.get_nickname()
    date = format_datetime(i, dt)
    return f"{nickname}: You set a reminder for {date}. Id: {id}."


def msg_deleted(i, id):
    nickname = i.msg.get_nickname()
    return f"{nickname}: Reminder #{id} deleted."


def msg_remind_usage(i):
    msgtarget = i.msg.get_msgtarget()
    botcmd = i.msg.get_botcmd()
    ch_pfx = i.bot["conf"].get_channel_prefix(msgtarget)

    return f"Usage: {ch_pfx}{botcmd} <nick> in <interval> <text>"


def msg_remind_me_usage(i):
    msgtarget = i.msg.get_msgtarget()
    botcmd = i.msg.get_botcmd()
    ch_pfx = i.bot["conf"].get_channel_prefix(msgtarget)

    return f"Usage: {ch_pfx}{botcmd} in <interval> <text>"


def msg_remind_delete_usage(i):
    msgtarget = i.msg.get_msgtarget()
    botcmd = i.msg.get_botcmd()
    ch_pfx = i.bot["conf"].get_channel_prefix(msgtarget)

    return f"Usage: {ch_pfx}{botcmd} <id>"


def format_datetime(i, dt) -> str:
    conf = i.bot["conf"]

    # Get the timezone from the config file and convert the datetime object
    # or remain in UTC
    try:
        tz = conf.conf["ui"]["timezone"]
        dt = dt.astimezone(tz=ZoneInfo(tz))
    except KeyError:
        tz = "UTC"

    weekday = get_day_str(dt.weekday())
    month = get_month_str(dt.month)
    time = str(dt.time()).rsplit(":", 1)[0]
    return f"{weekday} {dt.day} {month} {dt.year} {time} {tz}"


# ====================================================================
# Commands
# ====================================================================

def remind(i, irc, db):
    msgtarget = i.msg.get_msgtarget()
    args = i.msg.get_args()

    argv = args.split(" ", 2)
    argc = len(argv)

    if argc < 3:
        irc.out.notice(msgtarget, msg_remind_usage(i))
        return

    receiver = argv[0]

    remind_common(i, irc, db, receiver, argv[2])


def remind_me(i, irc, db):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    args = i.msg.get_args()

    argv = args.split(" ", 1)
    argc = len(argv)

    if argc < 2:
        irc.out.notice(msgtarget, msg_remind_me_usage(i))
        return

    remind_common(i, irc, db, nickname, argv[1])


# Common remind implementation ======================================

def remind_common(i, irc, db, receiver: str, rest: str):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    botcmd = i.msg.get_botcmd()
    ch_pfx = i.bot["conf"].get_channel_prefix(msgtarget)

    interval = parse_interval(rest)
    if interval is None:
        m = f"{botcmd}: Invalid interval. Try {ch_pfx}help remind"
        irc.out.notice(msgtarget, m)
        return

    secs, message = interval

    if not message:
        m = f"{botcmd}: Looks like you forgot to enter the message."
        irc.out.notice(msgtarget, m)
        return

    dt = datetime.now(timezone.utc) + timedelta(seconds=secs)
    timestamp = dt.timestamp()

    # Add the reminder in the database
    id = add_reminder(db, receiver, nickname, message, msgtarget, timestamp)

    irc.out.notice(msgtarget, msg_added(i, id, receiver, dt))


# Deleting reminders =================================================

def remind_delete(i, irc, db):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    args = i.msg.get_args()

    argv = args.split()
    argc = len(argv)

    if argc > 1:
        irc.out.notice(msgtarget, msg_remind_delete_usage(i))
        return

    id = args

    if is_deleted(db, id):
        m = f"{nickname}: Reminder #{id} could not be found."
        irc.out.notice(msgtarget, m)
        return

    if not has_delete_rights(db, id, nickname):
        m = f"{nickname}: Looks like you cannot delete this reminder."
        irc.out.notice(msgtarget, m)
        return

    delete_reminder(db, id, nickname)

    irc.out.notice(msgtarget, msg_deleted(i, id))


# ====================================================================
# Intialization
# ====================================================================

def init(db):
    dbc = db.cursor()
    sql = """
        CREATE TABLE IF NOT EXISTS remind (
               id        INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
               receiver  TEXT COLLATE NOCASE,
               added_by  TEXT COLLATE NOCASE,
               message   TEXT,
               channel   TEXT COLLATE NOCASE,
               timestamp INTEGER
        );
    """
    dbc.execute(sql)
    db.commit()


# ====================================================================
# Main
# ====================================================================

def main(i, irc):
    db = i.db_disk

    # Startup procedures
    if i.msg.is_command("__STARTUP"):
        init(db)  # Database initialization
        return

    nickname = i.msg.get_nickname()

    if i.msg.is_botcmd("remind-initialize") and is_bot_owner(irc, nickname):
        irc.out.notice(nickname, "remind: database initialized")
        init(db)
    elif i.msg.is_botcmd("remind"):
        remind(i, irc, db)
    elif i.msg.is_botcmd("remind-delete"):
        remind_delete(i, irc, db)
    else:
        remind_me(i, irc, db)
