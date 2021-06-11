# coding=utf-8

# Last.fm now playing module for drastikbot2
#
# It uses the Last.fm API to get the user's currently playing song.
# You need to provide your own API key to use this.
#
# Depends
# -------
# pip: requests


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
from user_auth import user_auth


class Module:  # Request commands to be used by the module
    bot_commands = ["np", "npset", "npunset", "npauth"]
    manual = {
        "desc": "Display your currently playing song using last.fm.",
        "irc_commands": {
            "np": {"usage": lambda x: f"{x}np",
                   "info": "Show the song that is playing right now."},
            "npset": {"usage": lambda x: f"{x}npset <last.fm username>",
                      "info": "Set your last.fm username."},
            "npunset": {"usage": lambda x: f"{x}npunset",
                        "info": "Unset your last.fm username."},
            "npauth": {"usage": lambda x: f"{x}npauth",
                       "info": "Toggle NickServ authentication for npset"},
        }
    }


# ----- Constants ----- #
API_KEY = 'Add you lastfm API here'
# --------------------- #


# ====================================================================
# Last.fm API
# ====================================================================

def lastfm_now_playing(user):
    u = ("https://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks"
         f"&user={user}&api_key={API_KEY}&format=json&limit=1")
    r = requests.get(u, timeout=10)
    j = r.json()

    try:
        out = j["recenttracks"]["track"][0]
    except KeyError as e:
        # error 10: Invalid API key
        if "error" in j and j["error"] == 10:
            raise Exception(j["message"])
        else:
            raise e

    artist = out["artist"]["#text"]
    song = out["name"]
    album = out["album"]["#text"]

    try:
        np = out["@attr"]["nowplaying"]
    except KeyError:
        np = False

    return {"now_playing": np,
            "artist": artist,
            "song": song,
            "album": album}


# ====================================================================
# Database
# ====================================================================

# Last.fm user

def get_lastfm_user(dbc, nick):
    try:
        dbc.execute('SELECT lfm_user FROM lastfm WHERE irc_nick=?;', (nick,))
        fetch = dbc.fetchone()
        lfm_user = fetch[0]
        return lfm_user
    except Exception:
        return False


def set_lastfm_user(dbc, user, nickname):
    dbc.execute("""
INSERT OR IGNORE INTO lastfm (irc_nick, lfm_user) VALUES (?, ?);
""", (nickname, user))

    dbc.execute("""
UPDATE lastfm SET lfm_user=? WHERE irc_nick=?;
""", (user, nickname))


def unset_lastfm_user(dbc, nickname):
    try:
        dbc.execute("DELETE FROM lastfm WHERE irc_nick=?;", (nickname,))
    except Exception:
        return False  # This usually means that there is no user set.

    return True


# IRC authentication

def get_auth_mode(dbc, nickname):
    dbc.execute('SELECT auth FROM lastfm WHERE irc_nick=?;', (nickname,))
    fetch = dbc.fetchone()
    try:
        return fetch[0]
    except TypeError:  # fetch is None, no mode set yet
        return 0


def toggle_auth_mode(dbc, nickname):
    auth = get_auth_mode(dbc, nickname)

    if auth == 0:
        auth = 1
    elif auth == 1:
        auth = 0

    dbc.execute("""
INSERT OR IGNORE INTO lastfm (irc_nick, auth) VALUES (?, ?);
""", (nickname, auth))

    dbc.execute("""
UPDATE lastfm SET auth=? WHERE irc_nick=?;
""", (auth, nickname))

    return auth


# ====================================================================
# Now Playing
# ====================================================================

def now_playing(i, irc, dbc):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    if args:
        m = f'Usage: {prefix}np'
        irc.out.notice(msgtarget, m)
        return

    lastfm_user = get_lastfm_user(dbc, nickname)
    if not lastfm_user:
        m = ("First you need to set your last.fm user."
             f"Try `{prefix}npset <user>'")
        irc.out.notice(msgtarget, m)
        return

    np = lastfm_now_playing(lastfm_user)

    # TODO. Removed for privacy reasons. There must be an option for users
    # to disallow this command on their nickname.
    # if argc == 1:  # Now playing info for a requested nickname.

    if not np["now_playing"]:
        m = f"{nickname}: Seems like you are not playing anything right now."
        irc.out.notice(msgtarget, m)
        return

    song, artist, album = np["song"], np["artist"], np["album"]

    if album:
        m = (f"\x0304{nickname}\x0F is listening to \x0304{song}\x0F by "
             f"\x0304{artist}\x0F from the album \x0304{album}\x0F.")
    else:
        m = (f"\x0304{nickname}\x0F is listening to \x0304{song}\x0F by "
             f"\x0304{artist}\x0F.")

    irc.out.notice(msgtarget, m)


# ====================================================================
# User setup and authentication
# ====================================================================

# Authentication

def is_authed(i, irc, dbc, nickname):
    auth = get_auth_mode(dbc, nickname)
    if auth == 0:
        return True
    if auth == 1 and user_auth(i, irc, nickname):
        return True

    return False


# IRC callback functions

def npset(i, irc, dbc):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    argv = args.split()
    argc = len(argv)

    if not args or argc > 1:
        m = f'Usage: {prefix}npset <last.fm username>'
        irc.out.notice(msgtarget, m)
        return

    lastfm_user = argv[0]

    if not is_authed(i, irc, dbc, nickname):
        m = f'{nickname}: You are not logged in.'
        irc.out.notice(msgtarget, m)
        return

    set_lastfm_user(dbc, lastfm_user, nickname)
    i.db_disk.commit()

    m = f"{nickname}: Your last.fm username was set to `{lastfm_user}'"
    irc.out.notice(msgtarget, m)


def npunset(i, irc, dbc):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()

    if not is_authed(i, irc, dbc, nickname):
        m = f'{nickname}: You are not logged in.'
        irc.out.notice(msgtarget, m)
        return

    if not unset_lastfm_user(dbc, nickname):
        m = f"{nickname}: There is no last.fm username to unset."
        irc.out.notice(msgtarget, m)
        return

    i.db_disk.commit()

    m = f"{nickname}: Your last.fm username was unset."
    irc.out.notice(msgtarget, m)


def npauth(i, irc, dbc):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()

    if not user_auth(i, irc, nickname):
        m = f"{nickname}: You need to be logged in to use this command"
        irc.out.notice(msgtarget, m)
        return

    if not is_authed(i, irc, dbc, nickname):
        m = f'{nickname}: You are not logged in.'
        irc.out.notice(msgtarget, m)
        return

    auth = toggle_auth_mode(dbc, nickname)
    i.db_disk.commit()

    if auth == 0:
        m = f"{nickname}: lastfm: Disabled authentication."
    elif auth == 1:
        m = f"{nickname}: lastfm: Enabled authentication."

    irc.out.notice(msgtarget, m)


# ====================================================================
# Main
# ====================================================================

dispatch = {
    "np": now_playing,
    "npset": npset,
    "npunset": npunset,
    "npauth": npauth
}


def main(i, irc):
    botcmd = i.msg.get_botcmd()

    dbc = i.db_disk.cursor()

    dbc.execute("""
CREATE TABLE IF NOT EXISTS lastfm (
    irc_nick TEXT COLLATE NOCASE PRIMARY KEY,
    lfm_user TEXT,
    auth INTEGER DEFAULT 0);
""")

    dispatch[botcmd](i, irc, dbc)
