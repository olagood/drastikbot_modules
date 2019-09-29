#!/usr/bin/env python3
# coding=utf-8

# Lainstream for Drastikbot
#
# Update and get information about lainchan radio and video streams.
#
# Depends:
#   - requests      :: $ pip3 install requests
#   - beautifulsoup :: $ pip3 install beautifulsoup4

# © 2018 All Rights Reserved olagood (drastik) https://github.com/olagood/

import pickle
from bs4 import BeautifulSoup
import requests


class Module:
    def __init__(self):
        self.commands = ['radio', 'stream', 'streamset']
        self.helpmsg = [
            "Usage: .radio",
            "       .stream",
            "       .streamset [Stream title]  # Unset if no args are given.",
            "Show and set streaming information for lainchan.org's streaming",
            "service."]


def radio():
    ret = "\x0306Lainchan Radio\x0F: "
    urls = ("https://lainon.life/playlist/cyberia.json",
            "https://lainon.life/playlist/cafe.json",
            "https://lainon.life/playlist/everything.json",
            "https://lainon.life/playlist/swing.json")
    for url in urls:
        channel = url.rsplit("/")[-1][:-5]
        r = requests.get(url, timeout=10)
        j = r.json()
        # live = j['stream_data']['live']
        c_artist = j['current']['artist']
        c_title = j['current']['title']
        listeners = j['listeners']['current']
        ret += (f"\x0305{channel} {listeners}\x0F: "
                f"\x0302{c_artist} - {c_title}\x0F | ")
    return ret + "https://lainon.life/"


def _stream_viewers(mode="rtmp"):
    if mode == "rtmp":
        suffix = "/live/subs?app=live&name=stream"
    else:
        # Add code for OGV stream
        return "??"
    url = f"https://lainchan.org{suffix}"
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.content, "html.parser")
    if mode == "rtmp":
        return soup.text.strip()
    else:
        # Add code for OGV stream
        return "??"


def stream(args):
    title = ""
    mode = "rtmp"
    if len(args) == 1 and args[0] != "":
        mode = args[0]
    if mode in value:
        title = value[mode]["stream"]

    viewers = _stream_viewers()
    if int(viewers) == 0:
        viewers_text = ""
    else:
        viewers_text = f"Viewers: {viewers} | "
    streamer = value[mode]["streamer"]
    if title:
        result = (f"\x0304Lainstream\x0F: \x0311{title}\x0F by "
                  f"\x0302{streamer}\x0F | {viewers_text}"
                  "Watch at: https://lainchan.org/stream.html | "
                  "HLS: https://lainchan.org:8080/hls/stream.m3u8")
    else:
        result = ("\x0304Lainstream\x0F: Nothing is streaming right now."
                  " Learn how you can stream at: "
                  "https://lainchan.org/stream.html ")
    return result


def streamset(args, i, irc):
    mode = "rtmp"
    if not args:
        value[mode]["stream"] = ""
        value[mode]["streamer"] = ""
        return "\x0304Lainstream\x0F: Stream information was unset!"

    if args[0] == "--ogv":
        mode = "ogv"
        title = ' '.join(args[1:])
    elif args[0] == "--rtmp":
        mode = "rtmp"
        title = ' '.join(args[1:])
    else:
        title = ' '.join(args)

    if not title:
        value[mode]["stream"] = ""
        value[mode]["streamer"] = ""
        return "\x0304Lainstream\x0F: Stream information was unset!"
    else:
        value[mode]["stream"] = title
        value[mode]["streamer"] = i.nickname
        return "\x0304Lainstream\x0F: Stream information updated!"


def main(i, irc):
    args = i.msg_nocmd.split()
    db = i.db[1]
    dbc = db.cursor()

    global value
    value = {
        "ogv": {"stream": ""},
        "rtmp": {"stream": ""},
    }

    try:
        dbc.execute('''SELECT value FROM stream;''')
        fetch = dbc.fetchone()
        value = pickle.loads(fetch[0])
    except Exception:
        dbc.execute('''CREATE TABLE IF NOT EXISTS stream (value BLOB);''')

    if i.cmd == 'stream':
        irc.privmsg(i.channel, stream(args))
    elif i.cmd == 'radio':
        irc.privmsg(i.channel, radio())
    elif i.cmd == 'streamset':
        irc.privmsg(i.channel, streamset(args, i, irc))

    v = pickle.dumps(value)
    try:
        dbc.execute('''INSERT INTO stream (value) VALUES (?);''', (v,))
    except Exception:
        pass
    dbc.execute('''UPDATE stream SET value = ?''', (v,))
    db.commit()
