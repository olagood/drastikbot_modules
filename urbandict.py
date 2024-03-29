#!/usr/bin/env python3
# coding=utf-8

# Urban Dictionary Module for Drastikbot.
#
# It uses api.urbandictionary.com/v0/.
#
# Depends:
#   - requests      :: $ pip3 install requests

'''
Copyright (C) 2018 drastik.org

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
from dbot_tools import p_truncate


class Module:
    bot_commands = ['ud']
    manual = {
        "desc": "Search https://www.urbandictionary.com/ for definitions.",
        "bot_commands": {
            "ud": {"usage": lambda x: f"{x}ud <query> [--def <num>]",
                   "info": ("The --def option allows you to select other"
                            " definitions. Example: .ud irc --def 2")}
        }
    }


logo = '\x0300,01Urban\x0F\x0308,01Dictionary\x0F'


def ud(query, res):
    u = f'http://api.urbandictionary.com/v0/define?term={query}'
    r = requests.get(u, timeout=30)
    j = r.json()['list'][res]
    word = j['word']
    definition = p_truncate(j['definition'], msg_len, 71, True)
    example = p_truncate(j['example'], msg_len, 15, True)
    author = j['author']
    t_up = j['thumbs_up']
    t_down = j['thumbs_down']
    pl = j['permalink'].rsplit('/', 1)[0]
    return (word, definition, example, author, t_up, t_down, pl)


def query(args):
    # Get the args list and the commands
    # Join the list to a string and return
    _args = args[:]
    try:
        idx = _args.index('--def')
        del _args[idx]
        del _args[idx]
    except ValueError:
        pass
    return ' '.join(_args)


def main(i, irc):
    msgtarget = i.msg.get_msgtarget()
    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    argv = args.split()

    if not args:
        m = f"Usage: {prefix}{botcmd} <query> [--def <num>]"
        irc.out.notice(msgtarget, m)
        return

    if '--def' in argv:
        idx = argv.index('--def')
        res = int(argv[idx + 1]) - 1
    else:
        res = 0

    q = query(argv)

    try:
        global msg_len
        # msg_len = msg_len - "PRIVMSG :" - chars - \r\n
        msg_len = irc.msg_len - 9 - 101 - 2
        u = ud(q, res)
        rpl = (f"{logo}: \x02{u[0]}\x0F"
               f" | {u[1]}"
               f" | \x02E.g:\x0F {u[2]}"
               f" | \x02Author:\x0F {u[3]}"
               f" | \x0303+{u[4]}\x0F"
               f" | \x0304-{u[5]}\x0F"
               f" | \x02Link:\x0F {u[6]}")
    except IndexError:
        rpl = f"{logo}: No definition was found for \x02{q}\x0F"
    except requests.exceptions.ReadTimeout:
        rpl = f"{logo}: Read timeout error. Please try again later."

    irc.out.notice(msgtarget, rpl)
