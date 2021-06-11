# coding=utf-8

# Waether module for drastikbot2
#
# Provides weather information from http://wttr.in
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


import urllib.parse
import requests
from user_auth import user_auth


class Module:
    bot_commands = ["weather", "weather_set", "weather_auth"]
    manual = {
        "desc": "Show weather information from http://wttr.in",
        "bot_commands": {
            "weather": {
                "usage": lambda x: (
                    f"{x}weather <location / airport code / @domain"
                    " / IP address / area code / GPS coordinates>"
                ),
                "info": "Get weather information."
            },
            "weather_set": {
                "usage": lambda x: (
                    f"{x}weather_set <location / airport code / @domain"
                    " / IP address / area code / GPS coordinates>"
                ),
                "info": (
                    "Set your default location. If a location has been"
                    " set, calling the weather command without arguments"
                    " will return the weather for that location, otherwise"
                    " you will be asked to provide a location. To unset"
                    " your location use .weather_set without any"
                    " arguements."
                )
            },
            "weather_auth": {
                "usage": lambda x: f"{x}weather_auth",
                "info": "Toggle NickServ authentication for weather_set"
            }
        }
    }


# ====================================================================
# Database Initializer: Called during bot startup
# ====================================================================

def db_init(i, _irc):
    db = i.db_disk
    dbc = db.cursor()

    dbc.executescript("""
    CREATE TABLE IF NOT EXISTS weather (
        nickname TEXT COLLATE NOCASE PRIMARY KEY,
        location TEXT,
        auth INTEGER DEFAULT 0);
    """)

    db.commit()


# ====================================================================
# wttr.in
# ====================================================================

def wttr(location: str) -> str:
    if location.lower() == "moon" or "moon@" in location.lower():
        m = "This is not supported yet (add ,+US or ,+France for these cities)"
        return m

    location = urllib.parse.quote(location, safe="")
    url = f"http://wttr.in/{location}?0Tm"
    r = requests.get(url, timeout=10)

    text = ''
    for line in r.text.splitlines():
        line = remove_ascii_art(line)
        if line:
            line = handler(line)
            text += f'{line} | '

    text = " ".join(text.split())  # Remove additional spaces.
    text = text.lstrip("Rainfall: ")  # Remove 'Rainfall: ' from the front.

    err_msg_1 = "ERROR: Unknown location:"
    if err_msg_1 in text:
        return f'\x0304wttr.in: Location "{location}" could not be found.'

    err_msg_1 = "API key has reached calls per day allowed limit."
    err_msg_2 = ("Sorry, we are running out of queries to the weather service"
                 " at the moment.")
    if err_msg_1 in text or err_msg_2 in text:
        return "\x0304wttr.in: API call limit reached. Try again tomorrow."

    return text


# Helper functions:

def unit_swap(unit):
    """Change the unit string from °C to °F or from km/h to mph and opposite"""
    unit_d = {
        "°C": "°F",
        "°F": "°C",
        "km/h": "mph",
        "mph": "km/h"
        }
    return unit_d.get(unit)


# Temperature

def temperature_color(temperature, unit_in, unit_out):
    """Colorize and convert the temperature."""
    tempcolor_d = {  # celsius: color
        -12: "02", -9: "12", -6: "11", 2: "10",
        10: "03", 19: "09", 28: "08", 37: "07"
    }
    if "°C" == unit_in:
        celsius = int(temperature.split("(")[0])
        fahrenheit = celsius * 1.8 + 32
        fahrenheit = int(round(fahrenheit, 0))
    elif "°F" == unit_in:
        fahrenheit = int(temperature.split("(")[0])
        celsius = (fahrenheit - 32) / 1.8
        celsius = int(round(celsius, 0))
    else:
        return "invalid input unit"

    for temp, color in tempcolor_d.items():
        if celsius <= temp:
            if "°C" == unit_out:
                return f"\x03{color} {celsius}\x0F"
            elif "°F" == unit_out:
                return f"\x03{color} {fahrenheit}\x0F"

    # Fallback for when the temperature is too high.
    if "°C" == unit_out:
        return f"\x0304 {celsius}\x0F"
    elif "°F" == unit_out:
        return f"\x0304 {fahrenheit}\x0F"


def temp_format_range(temp_list, unit, unit_s):
    ret = "Temp:"
    ret += f"{temperature_color(temp_list[0], unit, unit)} -"
    ret += f"{temperature_color(temp_list[1], unit, unit)} {unit} /"
    ret += f"{temperature_color(temp_list[0], unit, unit_s)} -"
    ret += f"{temperature_color(temp_list[1], unit, unit_s)} {unit_s}"
    return ret


def temp_format(txt):
    temperature_list = txt.split()  # ['25..27', '°C']
    temperature = temperature_list[0]
    # dashes = temperature.count('-')
    unit = temperature_list[1]
    unit_s = unit_swap(unit)
    ret = "Temp:"

    if '..' in temperature:
        temp_list = temperature.split('..')
        ret = temp_format_range(temp_list, unit, unit_s)
    else:
        ret += f"{temperature_color(temperature, unit, unit)} {unit} /"
        ret += f"{temperature_color(temperature, unit, unit_s)} {unit_s}"

    return ret


# Wind

def wind_color(wind, unit_in, unit_out):
    windcolor_d = {  # km/h: color
        4: "03", 10: "09", 20: "08", 32: "07"
    }
    if "km/h" == unit_in:
        kmh = int(wind)
        mph = kmh * 0.6213711922
        mph = int(round(mph, 0))
    elif "mph" == unit_in:
        mph = int(wind)
        kmh = mph * 1.609344
        kmh = int(round(kmh, 0))
    # elif "m/s" == unit_in:
    #     ms = int(wind)
    #     kmh = ms * 3.6

    for k, color in windcolor_d.items():
        if kmh < k:
            if "km/h" == unit_out:
                return f"\x03{color} {kmh}\x0F"
            elif "mph" == unit_out:
                return f"\x03{color} {mph}\x0F"

    # Fallback for when the wind speed is too high.
    if "km/h" == unit_out:
        return f"\x0304 {kmh}\x0F"
    elif "mph" == unit_out:
        return f"\x0304 {mph}\x0F"


def wind_format(txt):
    def range_hdl(t, tempstr):
        for idx, i in enumerate(t):
            coltemp = wind_color(i, unit)
            tempstr += f'{coltemp}'
            if idx == 0:
                tempstr += ' -'
        return tempstr

    wind_list = txt.split()  # ['↑', '23', 'km/h']
    icon = wind_list[0]
    wind = wind_list[1]
    unit = wind_list[2]
    unit_s = unit_swap(unit)
    dashes = wind.count('-')
    ret = f'Wind: {icon}'

    if 1 == dashes:
        # NEEDLESS?
        wind_list = wind.split('-')
        ret += f"{wind_color(wind_list[0], unit, unit)} -"
        ret += f"{wind_color(wind_list[1], unit, unit)} {unit} /"
        ret += f"{wind_color(wind_list[0], unit, unit_s)} -"
        ret += f"{wind_color(wind_list[1], unit, unit_s)} {unit_s}"
    else:  # 17 km/h
        ret += f"{wind_color(wind, unit, unit)} {unit} /"
        ret += f"{wind_color(wind, unit, unit_s)} {unit_s}"

    return f'{ret}'


def handler(txt):
    if ('°C' in txt) or ('°F' in txt):
        return temp_format(txt)
    elif ('km/h' in txt) or ('mph' in txt) or ('m/s' in txt):
        return wind_format(txt)
    elif ('km' in txt) or ('mi' in txt):
        return f'Visibility: {txt}'
    elif ('mm' in txt) or ('in' in txt):
        return f'Rainfall: {txt}'
    elif '%' in txt:
        return f'Rain Prob: {txt}'
    else:
        return txt


# Ascii art set from:
# https://github.com/schachmat/wego/blob/master/frontends/ascii-art-table.go
art = (
    '             ',
    '    .-.      ',
    '     __)     ',
    '    (        ',
    '     `-᾿     ',
    '      •      ',
    '     .--.    ',
    '  .-(    ).  ',
    ' (___.__)__) ',
    '  _ - _ - _  ',
    ' _ - _ - _ - ',
    '    (   ).   ',
    '   (___(__)  ',
    '  ‚ʻ‚ʻ‚ʻ‚ʻ   ',
    ' _`/"".-.    ',
    '  ,\\_(   ).  ',
    '   /(___(__) ',
    '   ‚ʻ‚ʻ‚ʻ‚ʻ  ',
    '   ‚’‚’‚’‚’  ',
    '   ‚‘‚‘‚‘‚‘  ',
    '     .-.     ',
    '   * * * *   ',
    '  * * * *    ',
    '    * * * *  ',
    '    ʻ ʻ ʻ ʻ  ',
    '   ʻ ʻ ʻ ʻ   ',
    '     ʻ ʻ ʻ ʻ ',
    '    ‘ ‘ ‘ ‘  ',
    '    ʻ * ʻ *  ',
    '   * ʻ * ʻ   ',
    '     ʻ * ʻ * ',
    '    * ʻ * ʻ  ',
    '   *  *  *   ',
    '     *  *  * ',
    '    *  *  *  ',
    '   \\  /      ',
    ' _ /"".-.    ',
    '   \\_(   ).  ',
    '    \\   /    ',
    '  ‒ (   ) ‒  ',
    '    /   \\    ',
    '  ‚ʻ⚡ʻ‚⚡‚ʻ   ',
    '  ‚ʻ‚ʻ⚡ʻ‚ʻ   ',
    '    ⚡ʻ ʻ⚡ʻ ʻ ',
    '     *⚡ *⚡ * ',
    '  ― (   ) ―  ',
    '     `-’     ',
    '   ⚡‘‘⚡‘‘  '
)


def remove_ascii_art(text):
    for i in art:
        text = text.replace(i, '')

    return text


# ====================================================================
# User settings
# ====================================================================

# Authentication

def toggle_auth(dbc, nickname):
    nickname = i.msg.get_nickname()


    dbc.execute("""
    SELECT auth FROM weather WHERE nickname=?;
    """, (nickname,))

    fetch = dbc.fetchone()

    try:
        auth = fetch[0]
    except TypeError:  # 'NoneType' object is not subscriptable
        auth = 0

    if auth == 0:
        auth = 1
    elif auth == 1:
        auth = 0

    dbc.execute("""
    INSERT OR IGNORE INTO weather (nickname, auth) VALUES (?, ?);
    """, (nickname, auth))

    dbc.execute("""
    UPDATE weather SET auth=? WHERE nickname=?;
    """, (auth, nickname))

    return auth


def get_auth(i, irc, dbc):
    nickname = i.msg.get_nickname()

    dbc.execute('SELECT auth FROM weather WHERE nickname=?;', (nickname,))
    fetch = dbc.fetchone()
    try:
        auth = fetch[0]
    except TypeError:  # 'NoneType' object is not subscriptable
        auth = 0

    if auth == 0:
        return True
    elif auth == 1 and user_auth(i, irc, nickname):
        return True
    else:
        return False


# Location

def set_location(dbc, nickname, location):
    dbc.execute("""
    INSERT OR IGNORE INTO weather (nickname, location) VALUES (?, ?);
    """, (nickname, location))

    dbc.execute("""
    UPDATE weather SET location=? WHERE nickname=?;
    """, (location, nickname))


def get_location(dbc, nickname):
    try:
        dbc.execute("""
        SELECT location FROM weather WHERE nickname=?;
        """, (nickname,))
        return dbc.fetchone()[0]
    except Exception:
        return False


# ====================================================================
# IRC Callbacks
# ====================================================================

def weather(i, irc):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    db = i.db_disk
    dbc = db.cursor()

    if args:
        m = wttr(args)
        irc.out.notice(msgtarget, m)
        return

    location = get_location(dbc, nickname)
    if location:
        m = wttr(location)
        irc.out.notice(msgtarget, m)
        return

    m = (f"Usage: {prefix}{botcmd} <Location / Airport code / @domain /"
         " IP address / Area code / GPS coordinates>")
    irc.out.notice(msgtarget, m)


def weather_set(i, irc):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    args = i.msg.get_args()

    db = i.db_disk
    dbc = db.cursor()

    if not get_auth(i, irc, dbc):
        m = f"{nickname}: weather: NickServ authentication is required."
        irc.out.notice(msgtarget, m)
        return

    set_location(dbc, nickname, args)
    db.commit()

    m = f'{nickname}: weather: Your location was set to "{location}"'
    irc.out.notice(msgtarget, m)


def weather_auth(i, irc):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    args = i.msg.get_args()

    db = i.db_disk
    dbc = db.cursor()

    if not user_auth(i, irc, nickname):
        m =  f"{nickname}: You are not logged in with NickServ."
        irc.out.notice(msgtarget, m)
        return

    new_auth = toggle_auth(dbc, nickname)
    db.commit()

    if new_auth == 1:
        m = f'{nickname}: weather: Enabled NickServ authentication.'
    elif new_auth == 2:
        m = f'{nickname}: weather: Disabled NickServ authentication.'

    irc.out.notice(msgtarget, m)


# ====================================================================
# Main
# ====================================================================

dispatch = {
    "__STARTUP": db_init,
    "weather": weather,
    "weather_set": weather_set,
    "weather_auth": weather_auth
}


def main(i, irc):
    try:
        botcmd = i.msg.get_botcmd()
    except AttributeError:
        botcmd = i.msg.get_command()  # __STARTUP

    dispatch[botcmd](i, irc)
