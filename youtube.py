# coding=utf-8

# YouTube module for drastikbot2
#
# Search YouTube and return a video url.
#
# Depends
# -------
# pip: requests, beautifulsoup4
# drastikbot_modules: url

# Copyright (C) 2018-2021 drastik.org
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


import traceback

import urllib.parse
import json
import requests  # type:ignore

from irc.modules import log  # type:ignore


class Module:
    bot_commands = ['yt']
    manual = {
        "desc": "Search YouTube and return the resulting video url.",
        "bot_commands": {"yt": {"usage": lambda x: f"{x}yt <video title>"}}
    }


# ----- Constants ----- #
parser = 'html.parser'
lang = "en-US"
user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
              " AppleWebKit/537.36 (KHTML, like Gecko)"
              " Chrome/83.0.4103.116 Safari/537.36")
# --------------------- #


#
# New Parser
#

def yt_vid_info(v):
    yt_id = v["videoId"]
    short_url = f"https://youtu.be/{yt_id}"
    name = v["title"]["runs"][0]["text"]
    # Usually youtube's automated music uploads dont have dates.
    try:
        date = v["publishedTimeText"]["simpleText"]
    except KeyError:
        date = False
    duration = v["lengthText"]["simpleText"]
    views = v["viewCountText"]["simpleText"]
    channel = v["ownerText"]["runs"][0]["text"]

    return {
        'short_url': short_url, 'name': name, 'date': date, 'views': views,
        'channel': channel, 'duration': duration, 'yt_id': yt_id
    }


def yt_search(query):
    search = (f'https://www.youtube.com/results?search_query={query}'
              '&app=desktop')
    r = requests.get(search, timeout=10,
                     headers={"Accept-Language": lang,
                              "user-agent": user_agent})

    try:
        st = 'var ytInitialData = '
        st_i = r.text.index(st) + len(st)
    except ValueError:
        st = 'window["ytInitialData"] = '
        st_i = r.text.index(st) + len(st)

    j_data = r.text[st_i:]

    st = '};'
    st_i = j_data.index(st)

    j_data = j_data[:st_i+1]
    j = json.loads(j_data)

    res = j["contents"]['twoColumnSearchResultsRenderer']['primaryContents'][
        'sectionListRenderer']['contents'][0]['itemSectionRenderer'][
        'contents']  # What in the world?

    for vid in res:
        if "videoRenderer" in vid:
            v = vid["videoRenderer"]  # Video information
            return yt_vid_info(v)
        elif 'searchPyvRenderer' in vid:
            continue  # Skip promoted videos


def output(i, o):
    conf = i.bot["conf"].conf

    '''Format the output message to be returned.'''
    # logo_yt = "\x0301,00You\x0300,04Tube\x0F"
    logo_yt = "\x0300,04 ► \x0F"

    if o["date"]:
        date = f" | \x02Uploaded:\x0F {o['date']}"
    else:
        date = ""

    try:
        alt = f" | \x02Alt:\x0F {conf['module:youtube']['alt']}{o['yt_id']}"
    except KeyError:
        alt = ""
    except Exception as e:
        log.debug(f"[module:youtube]: {e}\n{traceback.format_exc()}")
        alt = ""

    return (f"{logo_yt}: {o['short_url']} | "
            f"\x02{o['name']}\x0F ({o['duration']})"
            f" | \x02Views:\x0F {o['views']}"
            f" | \x02Channel\x0F: {o['channel']}"
            f"{date}"
            f"{alt}")


def output_error(err):
    '''Show an error message to the user'''
    logo_yt = "\x0300,04 ► \x0F"
    return f"{logo_yt}: Unable to find a video. Error {err}"


def main(i, irc):
    msgtarget = i.msg.get_msgtarget()
    args = i.msg.get_args()

    query = urllib.parse.quote(args, safe="")
    try:
        m = output(i, yt_search(query))
    except Exception as e:
        log.debug(f"[module:youtube]: {e}\n{traceback.format_exc()}")
        m = output_error(e)

    irc.out.notice(msgtarget, m)
