# coding=utf-8

# Wiktionary module for drastikbot2
##
# Depends
# -------
# pip: requests, beautifulsoup4

# Copyright (C) 2018, 2021 drastik.org
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


import requests
import bs4
import re
from dbot_tools import p_truncate


class Module:
    bot_commands = ["wiktionary", "wt"]
    usage = lambda x, y: f"{x}{y} <word> [-e <num>]"
    info = ("The -e option allows you to choose other defintions."
            " The number of definitions is listed in parenthesis in the"
            " result. In a query, the bot will post the full definitions"
            " without truncating the text.")
    manual = {
        "desc": "Search https://en.wiktionary.org/ for word definitions.",
        "bot_commands": {
            "wiktionary": {"usage": lambda x: usage(x, "wiktionary"),
                           "info": info,
                           "alias": ["wt"]},
            "wt": {"usage": lambda x: usage(x, "wt"),
                   "info": info,
                   "alias": ["wiktionary"]}
        }
    }


# ----- Global Constants ----- #
r_timeout = 10
bs4_parser = "html.parser"
# ---------------------------- #


def get_text(html, etymology):
    soup = bs4.BeautifulSoup(html, bs4_parser)

    result = {}
    result[etymology] = {}

    s_et = soup.find('span', id=etymology)
    result[etymology]["Etymology"] = s_et.find_next('p').text

    ids = ("Noun", "Verb", "Adjective", "Adverb",
           "Interjection", "Particle", "Preposition")
    for i in ids:
        s = s_et.find_next('span', string=i)
        try:
            txt = s.find_next('ol').text
            result[etymology][i] = txt
        except Exception as e:
            pass

    return result


def extract_etymologies(html):
    result = {}
    count = 1
    while(True):
        if 'id="Etymology"' in html:
            result.update(get_text(html, "Etymology"))
            break
        elif f'id="Etymology_{count}"' in html:
            result.update(get_text(html, f"Etymology_{count}"))
            count += 1
        else:
            break

    return result


def wiktionary(url, res):
    r = requests.get(url, timeout=r_timeout)

    # Extract the html of a single language section.
    section_end = '<hr'
    html = ""
    for t in r.text.splitlines():
        html += t
        if section_end in t:
            break

    # Remove quotations so that beautifulsoup doesn't catch them.
    html = re.compile(r'(?ims)<ul>.*?</ul>').sub('', html)
    html = re.compile(r'(?ims)<dl>.*?</dl>').sub('', html)
    html = re.compile(r'(?ims)<span class="defdate">.*?</span>').sub('', html)
    return extract_etymologies(html)


def search_query(args):
    # Get the args list and the commands
    # Join the list to a string and return
    _args = args[:]
    try:
        idx = _args.index('-e')
        del _args[idx]
        del _args[idx]
    except ValueError:
        pass
    return ' '.join(_args)


def main(i, irc):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    if not args:
        m = (f'Usage: {prefix}{botcmd} <Word> [-e <NUM>]')
        irc.out.notice(msgtarget, m)
        return

    argv = args.split()

    if '-e' in argv:
        idx = argv.index('-e')
        res = int(argv[idx + 1])
    else:
        res = 1

    q = search_query(argv)
    q_web = q.replace(" ", "_")
    url = f"https://en.wiktionary.org/wiki/{q_web}"
    result = wiktionary(url, res)
    result_length = len(result)

    if res not in range(1, result_length + 1):
        m = f'Wiktionary: No definition was found for "{q}" | {url}'
        irc.out.notice(msgtarget, m)
        return

    try:
        result = result[f"Etymology_{res}"]
    except KeyError:
        result = result["Etymology"]

    msg_len = (irc.msg_len - 9 - 8 - len(str(result_length))
               - (len(result) * 5) - len(url))
    p_tr_percent = 100 / len(result)

    txt = ""
    for part, cont in result.items():
        rslt = f"{part}: {cont}"
        if nickname != msgtarget:
            rslt = p_truncate(rslt, msg_len, p_tr_percent, True)
        txt += f"{rslt} | "

    rpl = f"{q} | {txt}({result_length}) | {url}"
    irc.out.notice(msgtarget, rpl)
