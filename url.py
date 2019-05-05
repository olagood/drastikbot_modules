#!/usr/bin/env python3
# coding=utf-8

# URL Module for Drastikbot
#
# Depends:
#   - requests      :: $ pip3 install requests
#   - beautifulsoup :: $ pip3 install beautifulsoup4

'''
Copyright (C) 2019 drastik.org

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import re
import math
import requests
import bs4


class Module:
    def __init__(self):
        self.auto = True
        self.helpmsg = ["Visit posted urls and post their HTML <title> tag."]


# ----- Constants ----- #
parser = 'html.parser'
user_agent = "w3m/0.52"
accept_lang = "en-US"
data_limit = 70000
blacklist = ['hooktube.com/', 'youtu.be/', 'youtube.com/watch']
# --------------------- #


def remove_formatting(msg):
    '''Remove IRC String formatting codes'''
    # - Regex -
    # Capture "x03N,M". Should be the first called:
    # (\\x03[0-9]{0,2},{1}[0-9]{1,2})
    # Capture "x03N". Catch all color codes.
    # (\\x03[0-9]{0,2})
    # Capture the other formatting codes
    line = re.sub(r'(\\x03[0-9]{0,2},{1}[0-9]{1,2})', '', msg)
    line = re.sub(r'(\\x03[0-9]{1,2})', '', line)
    line = line.replace("\\x03", "")
    line = line.replace("\\x02", "")
    line = line.replace("\\x1d", "")
    line = line.replace("\\x1D", "")
    line = line.replace("\\x1f", "")
    line = line.replace("\\x1F", "")
    line = line.replace("\\x16", "")
    line = line.replace("\\x0f", "")
    line = line.replace("\\x0F", "")
    return line


def short_url(url):
    if not len(url) > 80:
        return False
    p = {}
    p['url'] = url
    p['json'] = 1
    service = 'https://u.drastik.org/make'
    try:
        r = requests.get(service, params=p, timeout=5)
        return r.json()["short-url"]
    except Exception:
        return False


def convert_size(size_bytes):
    # https://stackoverflow.com/
    # questions/5194057/better-way-to-convert-file-sizes-in-python
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def get_url(msg):
    '''Search a string for urls and return a list of them.'''
    str_l = msg.split()
    req_l = ["http://", "https://"]  # add "." for parse urls without a scheme
    urls = [u for u in str_l if any(r in u for r in req_l)]
    # Avoid parsing IPv4s that are not complete (IPs like: 1.1):
    # Useful when a scheme is not required to parse a URL.
    # urls = [u for u in urls if u.count('.') == 3 or u.upper().isupper()]
    return urls


def get_title(u):
    '''
    Visit each url and check if there is html content
    served. If there is try to get the <title></title>
    tag. If there is not try to read the http headers
    to find 'content-type' and 'content-length'.
    '''
    data = ''
    title = False
    try:
        r = requests.get(u, stream=True,
                         headers={"user-agent": user_agent,
                                  "Accept-Language": accept_lang},
                         timeout=5)
    except Exception:
        return False
    for i in r.iter_content(chunk_size=512, decode_unicode=False):
        data += i.decode('utf-8', errors='ignore')
        if '</title>' in data.lower():
            html = bs4.BeautifulSoup(data, parser)
            try:
                title = html.head.title.text.strip()
            except Exception:
                pass
            break
        elif len(data) > data_limit or '</head>' in data.lower():
            break
    if not title:
        try:
            h_type = r.headers['content-type']
        except KeyError:
            h_type = False
        try:
            h_length = convert_size(float(r.headers['content-length']))
        except KeyError:
            h_length = False
        if h_type and h_length:
            headers = f"{h_type}, Size: {h_length}"
        elif h_type and not h_length:
            headers = f"{h_type}"
        elif not h_type and h_length:
            headers = f"Size: {h_length}"
        else:
            return False
        r.close()
        return headers
    else:
        r.close()
        return title


def main(i, irc):
    # - Raw undecoded message clean up.
    # Remove /r/n and whitespace
    msg = i.msg_raw.strip()
    # Convert the bytes to a string,
    # split the irc commands from the text message,
    # remove ' character from the end of the string.
    msg = str(msg).split(' :', 1)[1][:-1]
    # Remove all IRC formatting codes
    msg = remove_formatting(msg)
    print(msg)
    # msg = info[2]

    urls = get_url(msg)
    prev_u = set()  # Already visited URLs, used to avoid spamming.
    for u in urls:
        if not (u.startswith('http://') or u.startswith('https://')):
            u = f'http://{u}'
        if any(b in u for b in blacklist):
            return
        if u in prev_u:
            return
        title = get_title(u)
        short = short_url(u)
        if not title:
            continue
        if short:
            title = f'{title} - {short}'
        irc.privmsg(i.channel, title)
        prev_u.add(u)
