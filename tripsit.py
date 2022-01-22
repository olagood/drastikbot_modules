#!/usr/bin/env python3
# coding=utf-8

# tripsit.me module
#
# Depends:
#   - requests      :: $ pip3 install requests

'''
Copyright (C) 2021 drastik.org

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

import requests


class Module:
    bot_commands = ['drug']
    manual = {
        "desc": "Request drug info from tripsit.me",
        "bot_commands": {
            "drug": {"usage": lambda x: f"{x}drug <query>",
                     "info": ""}
        }
    }


logo = '\x02TRIPSIT\x0F'


def tripsit(query):
    q = query.replace(" ", "%20")
    u = f'http://tripbot.tripsit.me/api/tripsit/getDrug?name={q}'

    r = requests.get(u, timeout=30)
    j = r.json()

    if j["err"]:
        ret = False, j["err"], ""
    else:
        name = j["data"][0]["name"]
        desc = j["data"][0]["properties"]["summary"]
        ret = True, name, desc

    return ret


def main(i, irc):
    msgtarget = i.msg.get_msgtarget()
    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    if not args:
        m = f"Usage: {prefix}{botcmd} <query>"
        irc.out.notice(msgtarget, m)
        return

    status, name, desc = tripsit(args)
    if not status:
        rpl = f"{logo}: No drug information for: {args}"
    else:
        rpl = f"{logo}: {name} - {desc}"

    irc.out.notice(msgtarget, rpl)
