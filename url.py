# coding=utf-8

# URL Module for Drastikbot
#
# Depends:
#   - requests      :: $ pip3 install requests
#   - beautifulsoup :: $ pip3 install beautifulsoup4

'''
Copyright (C) 2017-2021 drastik.org

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, version 3 only.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

import re
import math
import json
import urllib.parse
import requests
import bs4

from irc.message import remove_formatting


class Module:
    irc_commands = ["PRIVMSG"]


# ----- Constants ----- #
parser = 'html.parser'
user_agent = "w3m/0.52"
accept_lang = "en-US"
nsfw_tag = "\x0304[NSFW]\x0F"
data_limit = 204800  # bytes
# --------------------- #


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


def default_parser(u):
    '''
    Visit each url and check if there is html content
    served. If there is try to get the <title></title>
    tag. If there is not try to read the http headers
    to find 'content-type' and 'content-length'.
    '''

    h = {
        "user-agent": user_agent,
        "Accept-Language": accept_lang
    }

    try:
        r = requests.get(u, stream=True, headers=h, timeout=5)
    except Exception:
        return "", False

    data = b""
    for i in r.iter_content(chunk_size=2048, decode_unicode=False):
        data += i
        if len(data) > data_limit:
            break

    r.close()

    data = data.decode('utf-8', errors='ignore')
    soup = bs4.BeautifulSoup(data, parser)
    output = ""

    try:
        output += soup.head.title.text.strip()
    except Exception:
        try:
            output += r.headers['content-type']
            output += ", "
        except KeyError:
            pass
        try:
            h_length = convert_size(float(r.headers['content-length']))
            output += f"Size: {h_length}"
        except KeyError:
            pass

    try:
        if "RTA-5042-1996-1400-1577-RTA" in data:
            output = f"{nsfw_tag} {output}"
        elif r.headers["Rating"] == "RTA-5042-1996-1400-1577-RTA":
            output = f"{nsfw_tag} {output}"
    except KeyError:
        pass

    return output, data


#                                            #
# BEGIN: Website Handling Functions (by url) #
#                                            #
def youtube(url):
    '''Visit a video and get it's information.'''
    logo = "\x0300,04 ► \x0F"
    u = f"https://www.youtube.com/oembed?url={url}"
    r = requests.get(u, timeout=10)
    if r:
        j = r.json()
        return (f"{logo}: {j['title']}"
                f" | \x02Channel:\x0F {j['author_name']}")
    else:
        out = default_parser(url)[0]
        return f"{logo}: {out}"


def lainchan(url):
    logo = "\x0309lainchan\x0F"
    if "/res/" in url:
        board = url.split("lainchan.org/")[1].split("/", 1)[0]
        board = urllib.parse.unquote(board)
        u = url.replace(".html", ".json")
        post_no = False
        if ".html#" in url:
            post_no = url.split("#")[1][1:]
        r = requests.get(u, timeout=10).json()
        try:
            title = r["posts"][0]["sub"]
        except KeyError:
            title = f'{r["posts"][0]["com"][:80]}...'
        replies = len(r["posts"]) - 1
        files = 0
        for i in r["posts"]:
            if "filename" in i:
                files += 1
            if "extra_files" in i:
                files += len(i["extra_files"])
        if post_no:
            for i in r["posts"]:
                if int(post_no) != i["no"]:
                    continue
                post_text = bs4.BeautifulSoup(i["com"], parser).get_text()[:50]
                return (f"{logo} \x0306/{board}/\x0F {title} "
                        f"\x02->\x0F \x0302{post_text}...\x0F | "
                        f"\x02Replies:\x0F {replies} - \x02Files:\x0F {files}")

        return (f"{logo} \x0306/{board}/\x0F {title} | "
                f"\x02Replies:\x0F {replies} - \x02Files:\x0F {files}")
    else:
        out = default_parser(url)[0]
        return f"{logo}: {out}"


def imgur(url):
    try:
        up = urllib.parse.urlparse(url)
        host = up.hostname
        path = up.path
        if host[:2] == "i.":
            host = host[2:]
            path = path.rsplit(".", 1)[0]
            u = f"https://{host}{path}"
        else:
            u = url

        r = requests.get(u, timeout=10)
        s = "widgetFactory.mergeConfig('gallery', "
        b = r.text.index(s) + len(s)
        e = r.text.index(");", b)
        t = r.text[b:e]

        s = "image               :"
        b = t.index(s) + len(s)
        e = t.index("},", b)
        t = t[b:e] + "}"

        j = json.loads(t)
        title = j["title"]
        mimetype = j["mimetype"]
        size = j["size"]
        width = j["width"]
        height = j["height"]
        nsfw = j["nsfw"]

        output = ""
        if nsfw:
            output += f"{nsfw_tag} "
        output += f"{title} - Imgur"
        output += f" | {mimetype}, Size: {convert_size(size)}"
        output += f", {width}x{height}"
        return output
    except Exception:
        return default_parser(url)[0]


def nitter(url):
    logo = "\x02Nitter\x0f"
    output, data = default_parser(url)
    try:
        soup = bs4.BeautifulSoup(data, parser)
        user = soup.find(attrs={"property": "og:title"})['content']
        post = soup.find(attrs={"property": "og:description"})['content']
        if post:
            return f"{logo}: \x0305{user}\x0f {post}"
        return output
    except Exception:
        return output


def twitter(url):
    logo = "\x0311twitter\x0F"
    u = f"https://publish.twitter.com/oembed?url={url}"
    r = requests.get(u, timeout=10,
                     headers={"user-agent": user_agent,
                              "Accept-Language": accept_lang})
    if r:
        j = r.json()
        html = j["html"]
        soup = bs4.BeautifulSoup(html, parser)
        tweet = soup.get_text(separator=" ")
        return f"{logo}: {tweet}"
    else:
        out = default_parser(url)[0]
        return f"{logo}: {out}"
#                                          #
# END: Website Handling Functions (by url) #
#                                          #


hosts_d = {
    "youtube.com": youtube,
    "youtu.be": youtube,
    "lainchan.org": lainchan,
    "i.imgur.com": imgur,
    "imgur.com": imgur,
    "nitter.net": nitter,
    "twitter.com": twitter
}


def _get_title_from_host(u):
    host = urllib.parse.urlparse(u).hostname
    if host.startswith("www."):
        host = host[4:]
    if host not in hosts_d:
        return default_parser(u)  # Return tuple
    else:
        return hosts_d[host](u), False


#                                              #
# BEGIN: Website Handling Functions (by title) #
#                                              #
def pleroma(data):
    logo = "\x0308Pleroma\x0F"
    soup = bs4.BeautifulSoup(data, parser)
    t = soup.find(attrs={"property": "og:description"})['content']
    t = t.split(": ", 1)
    poster = t[0]
    post = t[1]
    return f"{logo}: \x0305{poster}\x0F {post}"
#                                            #
# END: Website Handling Functions (by title) #
#                                            #


titles_d = {
    "Pleroma": pleroma
}


def _get_title_from_title(title, data):
    '''
    Used to get data from the <head> when the <title> isn't very helpful
    '''
    if title in titles_d:
        try:
            return titles_d[title](data)
        except Exception:
            return title
    else:
        return title


def get_title(u):
    try:
        title, data = _get_title_from_host(u)
    except AttributeError:  # `u' is not a URL and the host is None.
        return ""

    if data:
        title = _get_title_from_title(title, data)
    return title


def get_urls_from_text(text):
    return filter((lambda x: x.startswith("http")), text.split())


def get_titles_from_text(text, limit=0):
    prev_u = set()  # Already visited URLs, used to avoid spamming.
    count = 0

    for u in get_urls_from_text(text):
        if u in prev_u:
            continue

        if limit > 0 and count >= limit:
            yield ("limit", None)
            return
        else:
            count += 1

        title = get_title(u)
        if not title:
            continue
        else:
            yield ("title", title)


def main(i, irc):
    msgtarget = i.msg.get_msgtarget()
    text = i.msg.get_message().strip()
    text = str(text).split(' :', 1)[1][:-1]
    text = remove_formatting(text)

    for (status, title) in get_titles_from_text(text, limit=5):
        if status == "limit":
            nickname = i.msg.get_nickname()
            m = "[url] {nickname}: Max number of URLs per post (5) reached."
            irc.out.notice(msgtarget, m)
            return

        irc.out.notice(msgtarget, title)
