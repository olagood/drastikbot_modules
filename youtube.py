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
import requests
import bs4

import url


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


def output(i):
    '''Format the output message to be returned.'''
    # logo_yt = "\x0301,00You\x0300,04Tube\x0F"
    logo_yt = "\x0300,04 ► \x0F"

    if i["date"]:
        date = f" | \x02Uploaded:\x0F {i['date']}"
    else:
        date = ""

    return (f"{logo_yt}: {i['short_url']} | "
            f"\x02{i['name']}\x0F ({i['duration']})"
            f" | \x02Views:\x0F {i['views']}"
            f" | \x02Channel\x0F: {i['channel']}"
            f"{date}")


#
# Old parser
#

def yt_search_legacy(query):
    '''
    Search YouTube for 'query' and get a video from the search results.
    It tries to visit the video found to ensure that it is valid.
    Returns:
        - 'yt_id' : The YouTube ID of the result video.
        - False   : If no video is found for 'query'.
    '''
    search = (f'https://m.youtube.com/results?search_query={query}')
    r = requests.get(search, headers={"Accept-Language": lang}, timeout=10)
    #print(r.text, file=open("output.html", "a"))
    soup = bs4.BeautifulSoup(r.text, parser)
    for s in soup.find_all('a', {'class': ['yt-uix-tile-link']}):
        yt_id = urllib.parse.urlparse(s.get('href')).query
        print(yt_id)
        yt_id = urllib.parse.parse_qs(yt_id)
        print(yt_id)
        try:
            yt_id = yt_id['v'][0]
        except KeyError:
            try:
                yt_id = yt_id['video_id'][0]
            except KeyError:
                continue
        yt_id = ''.join(yt_id.split())
        # Try to visit the url to make sure it's a valid one.
        try:
            u = f'https://m.youtube.com/watch?v={yt_id}'
            requests.get(u, timeout=10)
            break
        except Exception:
            pass
    else:
        return False
    return yt_id


def output_legacy(yt_id):
    '''Format the output message to be returned.'''
    logo_yt = "\x0300,04 ► \x0F (legacy)"
    short_url = f"https://youtu.be/{yt_id}"
    title = url.youtube(short_url)
    return f"{logo_yt}: {short_url} | {title}"


def main(i, irc):
    msgtarget = i.msg.get_msgtarget()
    args = i.msg.get_args()

    query = urllib.parse.quote(args, safe="")
    try:
        m = output(yt_search(query))
    except Exception:
        print(traceback.format_exc())
        m = output_legacy(yt_search_legacy(query))

    irc.out.notice(msgtarget, m)
