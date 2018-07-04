import pickle
from bs4 import BeautifulSoup
import requests


class Module:
    def __init__(self):
        self.commands = ['stream', 'streamset', 'streamunset', 'streamer',
                         'streamerset', 'streamerunset', 'viewers']
        self.helpmsg = [
            "Usage: .stream",
            "       .streamset <...>",
            "       .streamunset",
            "       .streamer",
            "       .streamerset",
            "       .streamerunset",
            "       .viewers",
            "Show and set streaming information for lainchan.org's streaming",
            "service."]


def stream(args):
    """Get Stream name """
    name = "Nothing"
    streamtype = "rtmp"
    if len(args) == 1 and args[0] != "":
        streamtype = args[0]
    if streamtype in value:
        if "stream" in value[streamtype]:
            name = value[streamtype]["stream"]
    result = "%s is streaming right now." % name
    return result


def streamset(args):
    """Set Stream name """
    streamtype = "rtmp"
    name = None
    if len(args) == 1 and args[0] != "":
        name = args[0]
    elif len(args) >= 2:
        if args[0] == "radio" or args[0] == "ogv" or args[0] == "rtmp":
            streamtype = args[0]
            name = ' '.join(args[1:])
        else:
            name = ' '.join(args[0:])
    value[streamtype]["stream"] = name
    result = "Okay, stream name set to %s" % name
    return result


def streamunset(args):
    """Unset Stream name """
    result = "Stream name unset"
    streamtype = "rtmp"
    if len(args) == 1 and args[0] != "":
        streamtype = args[0]
    if streamtype in value:
        if "stream" in value[streamtype]:
            del value[streamtype]["stream"]
    return result


def streamer(args):
    """Get Streamer name """
    name = "Noone"
    streamtype = "rtmp"
    if len(args) == 1 and args[0] != "":
        streamtype = args[0]
    if streamtype in value:
        if "streamer" in value[streamtype]:
            name = value[streamtype]["streamer"]
    result = "%s is streaming right now." % name
    return result


def streamerset(args):
    """Set Streamer name """
    streamtype = "rtmp"
    name = None
    if len(args) == 1 and args[0] != "":
        name = args[0]
    elif len(args) >= 2:
        if args[0] == "radio" or args[0] == "ogv" or args[0] == "rtmp":
            streamtype = args[0]
            name = ' '.join(args[1:])
        else:
            name = ' '.join(args[0:])
    value[streamtype]["streamer"] = name
    result = "Okay, streamer name set to %s" % name
    return result


def streamerunset(args):
    """Unset Streamer name """
    result = "Streamer name unset"
    streamtype = "rtmp"
    if len(args) == 1 and args[0] != "":
        streamtype = args[0]
    if streamtype in value:
        if "streamer" in value[streamtype]:
            del value[streamtype]["streamer"]
    return result


def viewers(args):
    """Display viewers """
    streamtype = "rtmp"
    suffix = ""
    viewers = "no"
    if len(args) == 1 and args[0] != "":
        streamtype = args[0]
    if streamtype == "rtmp":
        suffix = "/live/subs?app=live&name=stream"
    else:
        suffix = "/radio_assets/status.xsl"
    url = "https://lainchan.org%s" % suffix
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    if streamtype == "rtmp":
        viewers = soup.find('p').text.strip()
    else:
        results = soup.find_all("td", class_="streamdata")
        offset = 0
        if streamtype == "ogv":
            offset = 22
        elif streamtype == "radio":
            offset = 13
        if len(results) >= offset:
            viewers = results[offset].text.strip()
    result = "Stream has %s viewers" % viewers
    return result


def main(i, irc):
    msg = i.msg_nocmd.split()
    dbc = i.db[0].cursor()
    global value
    value = {"ogv": {}, "rtmp": {}, "radio": {}}
    try:
        dbc.execute('''SELECT value FROM stream''')
        fetch = dbc.fetchone()
        value = pickle.loads(fetch[0])
    except Exception as e:
        print(f'Exception: stream.py loading db value {e}')

    if i.cmd == 'stream':
        irc.privmsg(i.channel, stream(msg))
    elif i.cmd == 'streamset':
        irc.privmsg(i.channel, streamset(msg))
    elif i.cmd == 'streamunset':
        irc.privmsg(i.channel, streamunset(msg))
    elif i.cmd == 'streamer':
        irc.privmsg(i.channel, streamer(msg))
    elif i.cmd == 'streamerset':
        irc.privmsg(i.channel, streamerset(msg))
    elif i.cmd == 'streamerunset':
        irc.privmsg(i.channel, streamerunset(msg))
    elif i.cmd == 'viewers':
        irc.privmsg(i.channel, viewers(msg))

    v = pickle.dumps(value)
    dbc.execute('''CREATE TABLE IF NOT EXISTS stream (value BLOB);''')
    try:
        dbc.execute('''INSERT INTO stream (value) VALUES (?);''', (v,))
    except Exception:
        print('Exception: stream.py couldnt wrote to db.')
    dbc.execute('''UPDATE stream SET value = ?''', (v,))
