#!/usr/bin/env python3
# coding=utf-8

# Tell Module for Drastikbot
#
# It works "like" memoserv.
# A user tells the bot to tell a message to a nick when that nick is seen.
# .tell drastik drastikbot is down | .tell <NICKNAME> <MESSAGE>

'''
Copyright (C) 2017, 2021 drastik.org

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
from ignore import is_ignored


class Module:
    irc_commands = ["PRIVMSG"]
    manual = {
        "desc": (
            "Send a message to a user through the bot. This is used to"
            " send messages to users that are AFK or not connected to "
            "the server. The bot will message the receiver as soon as "
            "they post to a channel that the bot has joined."
        ),
        "bot_commands": {
            "tell": {"usage": lambda x: f"{x}tell <receiver> <message>"}
        }
    }


def add(receiver, msg, sender, dbc):
    timestamp = datetime.datetime.utcnow().replace(microsecond=0)
    dbc.execute("CREATE TABLE IF NOT EXISTS tell "
                "(receiver TEXT COLLATE NOCASE, msg TEXT, sender TEXT, "
                "timestamp TEXT, date INTEGER);")
    dbc.execute("INSERT INTO tell VALUES (?, ?, ?, ?, strftime('%s', 'now'));",
                # These are wrong but handled correctly. Fix it someday.
                (receiver, msg, str(timestamp), sender))


def find(nick, irc, dbc):
    try:
        dbc.execute('SELECT sender, msg, timestamp FROM tell '
                    'WHERE receiver=?;', (nick,))
        fetch = dbc.fetchall()
        for i in fetch:
            irc.out.privmsg(nick, f'\x0302{i[2]} [{i[0]} UTC]:\x0F')
            irc.out.privmsg(nick, i[1])
        dbc.execute('''DELETE FROM tell WHERE receiver=?;''', (nick,))
        # Delete messages older than 3600 * 24 * 30 * 3 seconds.
        dbc.execute('''DELETE FROM tell WHERE
                    (strftime('%s', 'now') - date) > (3600 * 24 * 30 * 3);''')
    except Exception:
        # Nothing in the db yet, ignore errors.
        pass


def main(i, irc):
    db = i.db_disk
    dbc = db.cursor()

    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()

    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    if "tell" == botcmd:
        argv = args.split(" ", 1)

        try:
            receiver = argv[0]
            message = argv[1]
        except IndexError:
            m = f"Usage: {prefix}{botcmd} <receiver> <message>"
            irc.out.notice(msgtarget, m)
            return

        if is_ascii_cl(irc.curr_nickname, receiver):
            m = f"{nickname}: I am here now, tell me."
            irc.out.notice(msgtarget, m)
            return

        if is_ignored(i, irc, receiver, nickname):
            return  # say nothing

        add(receiver, message, nickname, dbc)

        if i.msg.is_nickname(receiver):
            m = f'{nickname}: When you return, I will notify'
            irc.out.notice(msgtarget, m)
            return

        m = f'{nickname}: When {receiver} returns, I will notify.'
        irc.out.notice(msgtarget, m)

    find(nickname, irc, dbc)
    db.commit()
