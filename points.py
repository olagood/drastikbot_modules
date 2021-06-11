# coding=utf-8

# Point (karma) counting module for drastikbot
#
# Give points/karma to users for performing certain actions


# Copyright (C) 2019, 2021 drastik.org
#
# This file is part of drastikbot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


class Module:
    irc_commands = ["PRIVMSG"]
    manual = {
        "desc": "Count a user's GNU/Linux points.",
        "bot_commands": {
            "points": lambda x: f"{x}points",
            "info": "Show your total amount of points."
        }
    }


def set_gnu_linux_points(dbc, nickname, points):
    dbc.execute("CREATE TABLE IF NOT EXISTS points_gnu_linux "
                "(nickname TEXT COLLATE NOCASE, points INTEGER);")
    dbc.execute("INSERT OR IGNORE INTO points_gnu_linux VALUES (?, ?);",
                (nickname, points))
    dbc.execute("UPDATE points_gnu_linux SET points=? WHERE nickname=?;",
                (points, nickname))


def get_gnu_linux_points(dbc, nickname):
    try:
        dbc.execute("SELECT points FROM points_gnu_linux WHERE nickname=?;",
                    (nickname,))
        return dbc.fetchone()[0]
    except Exception:
        return 0


def gnu_linux_points_handler(dbc, nickname, mode=""):
    try:
        p = get_gnu_linux_points(dbc, nickname)
    except Exception:
        p = 0
    if "gnu" == mode:
        p += 1
    elif "linux" == mode:
        p -= 1
    set_gnu_linux_points(dbc, nickname, p)


def main(i, irc):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    botcmd = i.msg.get_botcmd()
    text = i.msg.get_text()

    dbc = i.db_disk.cursor()

    if botcmd == "points":
        gl_p = get_gnu_linux_points(dbc, nickname)
        m = f"GNU/Linux Points for {nickname}: {gl_p}"
        irc.out.notice(msgtarget, m)
        return

    # Ignore PMs
    if msgtarget == nickname:
        return

    last_nick = i.varget("last_nick", defval=irc.curr_nickname)

    # Only one sequential line is counted
    if last_nick == nickname:
        return

    i.varset("last_nick", nickname)

    text = text.lower()

    if "gnu/linux" in text or "gnu+linux" in text or "gnu linux" in text:
        gnu_linux_points_handler(dbc, nickname, mode="gnu")
    elif "linux" in text and "kernel" not in text and "gnu" not in text:
        gnu_linux_points_handler(dbc, nickname, mode="linux")

    i.db_disk.commit()
