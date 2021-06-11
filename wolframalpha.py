# coding=utf-8

# WolframAlpha module for drastikbot2
#
# It makes use of the Short Answers API to get answers for user queries.
#
# You need to use you own AppID to use this module. Find out more:
# http://products.wolframalpha.com/short-answers-api/documentation/
#
# Depends
# -------
# pip: requests

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


import urllib.parse
import requests


class Module:
    bot_commands = ["wa", "wolfram", "wolframalpha"]
    manual = {
        "desc": "Get results from the Wolfram|Alpha short answers API.",
        "bot_commands": {
            "wa": {"usage": lambda x: f"{x}wa <query>",
                   "alias": ["wolfram", "wolframalpha"]},
            "wolfram": {"usage": lambda x: f"{x}wolfram <query>",
                        "alias": ["w", "wolframalpha"]},
            "wolframalpha": {"usage": lambda x: f"{x}wolframalpha <query>",
                             "alias": ["wolfram", "w"]}
        }
    }


AppID = "Enter your AppID here"


def short_answers(query):
    url = f"http://api.wolframalpha.com/v1/result?appid={AppID}&i={query}"
    try:
        r = requests.get(url, timeout=10)
    except Exception:
        return False
    return r.text


def main(i, irc):
    msgtarget = i.msg.get_msgtarget()
    args = i.msg.get_args()

    query = urllib.parse.quote_plus(args)
    r = short_answers(query)
    r = f"Wolfram|Alpha: {r}"
    irc.out.notice(msgtarget, r)
