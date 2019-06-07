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

import urllib.parse
import json
import requests
import bs4
import url  # drastikbot_modules: url.py


class Module:
    def __init__(self):
        self.commands = ['g', 'bing', 'ddg', 'searx', 'sp']
        self.helpmsg = [
            "Usage: .g <query>",
            " ",
            "Get results from Google, Bing, Duckduckgo, Searx and Startpage.",
            ".g     : https://www.google.com/",
            ".bing  : https://www.bing.com",
            ".ddg   : https://duckduckgo.com/ (Also supports !bangs)",
            ".searx : https://searx.me/",
            ".sp    : https://www.startpage.com/"]


# ----- Constants ----- #
opt_title_tag = True
parser = 'html.parser'
lang = "en-US"
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


# --- Search engine functions --- #
def google(query):
    logo = '\x0302G\x0304o\x0308o\x0302g\x0309l\x0304e\x0F'
    search = f'https://www.google.com/search?q={query}'
    r = requests.get(search, headers={"Accept-Language": lang}, timeout=10)
    soup = bs4.BeautifulSoup(r.text, parser)
    err_str = (f'{logo}: \x0308Sorry, i could not find any results for:\x0F'
               f' {url2str(query)}')
    for s in soup.find_all('h3', {'class': ['r']}):
        u = s.find('a').get('href')
        u = urllib.parse.urlparse(u).query
        try:
            u = ''.join(urllib.parse.parse_qs(u)['q'][0].split())
        except KeyError:
            continue
        u = urlfix(u)
        if opt_title_tag:
            title = url.get_title(u)
            break
        else:
            title = ''
            try:
                requests.get(u, timeout=10)
                break
            except Exception:
                pass
    else:
        return err_str

    return f"{logo}: {u} | {title}"


def bing(query):
    logo = '\x0315Bing\x0F'
    search = f'https://www.bing.com/search?q={query}'
    err_str = (f'{logo}: \x0308Sorry, i could not find any results for:\x0F'
               f' {url2str(query)}')
    r = requests.get(search, headers={"Accept-Language": lang}, timeout=10)
    soup = bs4.BeautifulSoup(r.text, parser)
    for s in soup.find_all('h2'):
        u = urlfix(s.find('a').get('href'))
        if opt_title_tag:
            title = url.get_title(u)
            break
        else:
            title = ''
            try:
                requests.get(u, timeout=10)
                break
            except Exception:
                pass
    else:
        return err_str
    return f"{logo}: {u} | {title}"


def ddg(query, query_p):
    logo = "\x0315DuckDuckGo\x0F"
    if query_p[0] == '!':
        search = (f'http://api.duckduckgo.com/?q={query}'
                  '&format=json&no_redirect=1')
        r = requests.get(search, headers={"Accept-Language": lang}, timeout=10)
        data = json.loads(r.text)
        u = urlfix(data["Redirect"])
        return f"{logo}: {u}"
    # If no bang is given, search and find a result
    search = f'https://duckduckgo.com/html/?q={query}'
    r = requests.get(search, headers={"user-agent": "w3m/0.52",
                                      "Accept-Language": lang},
                     timeout=10)
    soup = bs4.BeautifulSoup(r.text, parser)
    err_str = (f'{logo}: \x0308Sorry, i could not find any results for:\x0F'
               f' {url2str(query)}')
    for s in soup.find_all('a', {'class': ['result__url']}):
        u = urllib.request.unquote(s.get('href'))[15:]
        if u:
            u = urlfix(u)
        else:
            return err_str
        if opt_title_tag:
            title = url.get_title(u)
            break
        else:
            title = ''
            try:
                requests.get(u, timeout=10)
                break
            except Exception:
                pass
    else:
        return err_str

    return f"{logo}: {u} | {title}"


def searx(query):
    logo = "\x0315sear\x0311X\x0F"
    err_str = (f'{logo}: \x0308Sorry, i could not find any results for:\x0F'
               f' {url2str(query)}')
    search = f'https://searx.me/?q={query}'
    r = requests.get(search, headers={"Accept-Language": lang}, timeout=10)
    soup = bs4.BeautifulSoup(r.text, parser)
    for a in soup.find_all('h4', {'class': ['result_header']}):
        for s in a('a'):
            u = urlfix(s.get('href'))
            if opt_title_tag:
                title = f"| {url.get_title(u)}"
            else:
                title = ''
            if title:
                br = True  # Break flag for the outer loop
                break
            else:
                try:
                    requests.get(u, timeout=10)
                    br = True  # Break flag for the outer loop
                    break
                except Exception:
                    pass
        if br:
            break
    else:
        return err_str

    return f"{logo}: {u} {title}"


def startpage(query):
    logo = "\x0304start\x0302page\x0F"
    err_str = (f'{logo}: \x0308Sorry, i could not find any results for:\x0F'
               f' {url2str(query)}')
    search = f'https://www.startpage.com/do/asearch?q={query}'
    r = requests.get(search, headers={"Accept-Language": lang}, timeout=10)
    soup = bs4.BeautifulSoup(r.text, parser)
    for s in soup.find_all('a', {'id': ['title_1']}):
        u = urlfix(s.get('href'))
        if opt_title_tag:
            title = f"| {url.get_title(u)}"
            break
        else:
            title = ''
            try:
                requests.get(u, timeout=10)
                break
            except Exception:
                pass
    else:
        return err_str

    return f"{logo}: {u} {title}"


def main(i, irc):
    query = urllib.parse.quote_plus(i.msg_nocmd)
    if i.cmd == 'g':
        irc.privmsg(i.channel, google(query))
    elif i.cmd == 'bing':
        irc.privmsg(i.channel, bing(query))
    elif i.cmd == 'ddg':
        irc.privmsg(i.channel, ddg(query, i.msg_nocmd))
    elif i.cmd == 'searx':
        irc.privmsg(i.channel, searx(query))
    elif i.cmd == 'sp':
        irc.privmsg(i.channel, startpage(query))
