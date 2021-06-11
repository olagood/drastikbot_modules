#!/usr/bin/env python3
# coding=utf-8

# Search Module for Drastikbot
#
# Provides the results of various search engines like:
# Google, Bing, Duckduckgo, Searx, Startpage
#
# Depends:
#   - requests      :: $ pip3 install requests
#   - beautifulsoup :: $ pip3 install beautifulsoup4
#   - url           :: included with drastikbot_modules, should be loaded.

'''
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

import urllib.parse
import requests
import bs4
import url  # drastikbot_modules: url.py


class Module:
    bot_commands = ['g', 'bing', 'ddg', 'searx', 'sp']
    manual = {
        "desc": ("Get search results from Duckduckgo, Google, Bing"
                 ", Searx and Startpage."),
        "bot_commands": {
            "g": {"usage": lambda x: f"{x}g <query>"},
            "bing": {"usage": lambda x: f"{x}bing <query>"},
            "ddg": {"usage": lambda x: f"{x}ddg <query>"},
            "searx": {"usage": lambda x: f"{x}searx <query>"},
            "sp": {"usage": lambda x: f"{x}sp <query>"}
        }
    }


# ----- Constants ----- #
opt_title_tag = True
parser = 'html.parser'
lang = "en-US"

ua_chrome_90 = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36")


# --------------------- #


# --- Helper Functions --- #
def url2str(query):
    return urllib.parse.unquote_plus(query)


def url_extract(url):
    u = urllib.parse.urlparse(url)
    u = urllib.parse.parse_qs(u.query)
    try:
        u = u['v'][0]
    except Exception:
        u = u['video_id'][0]
    return ''.join(u.split())


def urlfix(url):
    url = url.replace(' ', '')
    if not (url.startswith('http://') or url.startswith('https://')):
        url = 'http://' + url
    return url


# ====================================================================
# Google
# ====================================================================

def google(args):
    query = urllib.parse.quote(args, safe="")
    u = f"https://www.google.com/search?q={query}"
    h = {
        "Accept-Language": lang,
        "user-agent": ua_chrome_90,
    }
    r = requests.get(u, headers=h, timeout=10)
    soup = bs4.BeautifulSoup(r.text, parser)

    results_l = soup.find("div", {"id": "search"}).find_all("a")
    result = results_l[0].get("href")

    return "google", result


# ====================================================================
# Bing
# ====================================================================

def bing(args):
    query = urllib.parse.quote(args, safe="")
    u = f"https://bing.com/search?q={query}"
    h = {
        "Accept-Language": lang,
        "user-agent": ua_chrome_90,
    }
    r = requests.get(u, headers=h, timeout=10)
    soup = bs4.BeautifulSoup(r.text, parser)

    results_l = soup.find_all("li", {"class": "b_algo"})
    result = results_l[0].find("a").get("href")

    return "bing", result


# ====================================================================
# Duckduckgo
# ====================================================================

def duckduckgo(args):
    query = urllib.parse.quote(args, safe="")

    if args[0] == '!':
        return "duckduckgo", duckduckgo_bang(query)

    return "duckduckgo", duckduckgo_search(query)


def duckduckgo_bang(query):
    u = f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1"
    h = {
        "Accept-Language": lang
    }
    r = requests.get(u, headers=h, timeout=10)
    return r.json()["Redirect"]


def duckduckgo_search(query):
    u = ("https://html.duckduckgo.com/html/"
         f"?q={query}&kl=wt-wt&kp=-2&kaf=1&kh=1&k1=-1&kd=-1")
    h = {
        "user-agent": ua_chrome_90,
        "Accept-Language": lang
    }
    r = requests.get(u, headers=h, timeout=10)
    soup = bs4.BeautifulSoup(r.text, parser)

    result = soup.find("a", {"class": ["result__url"]})
    return result.get("href")


# ====================================================================
# Searx
# ====================================================================

def searx(args):
    query = urllib.parse.quote(args, safe="")
    u = ("https://search.mdosch.de/search"
         f"?q={query}&format=json&category_general=1")
    h = {
        "user-agent": ua_chrome_90,
        "Accept-Language": lang
    }
    r = requests.get(u, headers=h, timeout=10)
    try:
        result = r.json()["results"][0]["url"]
    except IndexError:
        result = f"\x0308Sorry, i could not find any results for:\x0F {args}"

    return "searx", result


# ====================================================================
# Startpage
# ====================================================================

def startpage(args):
    query = urllib.parse.quote(args, safe="")
    u = ("https://www.startpage.com/sp/search"
         f"?query={query}&language=english")
    h = {
        "user-agent": ua_chrome_90,
        "Accept-Language": lang
    }
    r = requests.get(u, headers=h, timeout=10)
    soup = bs4.BeautifulSoup(r.text, parser)

    results_l = soup.find_all("a", {"class": ["result-link"]})
    result = results_l[0].get("href")

    return "startpage", result


# ====================================================================
# Main
# ====================================================================

dispatch = {
    "g": google,
    "bing": bing,
    "ddg": duckduckgo,
    "searx": searx,
    "sp": startpage
}

logo_d = {
    "google": "\x0302G\x0304o\x0308o\x0302g\x0309l\x0304e\x0F",
    "bing": "\x0315Bing\x0F",
    "duckduckgo": "\x0315DuckDuckGo\x0F",
    "searx": "\x0315sear\x0311X\x0F",
    "startpage": "\x0304start\x0302page\x0F"
}

# err = f'{logo}: \x0308Sorry, i could not find any results for:\x0F {query}'


def main(i, irc):
    msgtarget = i.msg.get_msgtarget()
    botcmd = i.msg.get_botcmd()
    args = i.msg.get_args()

    engine, result = dispatch[botcmd](args)

    title = None
    if opt_title_tag:
        title = url.get_title(result)

    logo = logo_d[engine]

    if title:
        m = f"{logo}: {result} | < title: {title}"
    else:
        m = f"{logo}: {result}"

    # Truncate the output just in case. We can't send 512 bytes anyway.
    m = m[:512]

    irc.out.notice(msgtarget, m)
