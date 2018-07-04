#!/usr/bin/env python3
# coding=utf-8

# Weather Module for Drastikbot
#
# Provides weather information from http://wttr.in
#
# Depends:
#   - requests      :: $ pip3 install requests

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
import requests


class Module:
    def __init__(self):
        self.commands = ['weather']
        self.helpmsg = [
            "Usage: .weather <Location / Airport code / @domain / IP address"
            " / Area code / GPS coordinates>",
            " ",
            "Show weather information from http://wttr.in"]


def url2str(query):
    return urllib.parse.unquote_plus(query)


# Temperature string formatting functions
def temp_color(temp, unit):
    tempcol_d = {
        -12: '02', -9: '12', -6: '11', 2: '10',
        10: '03', 19: '09', 28: '08', 37: '07'
    }

    if unit == '°C':
        t = int(temp)
    else:
        t = (int(temp) - 32) / 1.8  # Convert Fahrenheit to Celsius.

    for k, v in tempcol_d.items():
        if t < k:
            return f'\x03{v} {temp}\x0F'


def temp_format(txt):
    def range_hdl(t, tempstr):
        for idx, i in enumerate(t):
            coltemp = temp_color(i, u)
            tempstr += f'{coltemp}'
            if idx == 0:
                tempstr += ' -'
        return tempstr

    temp_ls = txt.split()
    t = temp_ls[0]
    u = temp_ls[1]
    d = t.count('-')
    tempstr = 'Temp:'

    if d == 1:
        if not t[0] == '-':
            t = t.split('-')
            tempstr = range_hdl(t, tempstr)
        else:
            coltemp = temp_color(t, u)
            tempstr += f'{coltemp}'
    elif d == 2:
        t = t.split('-', 2)
        t = [f'-{t[1]}', t[2]]
        tempstr = range_hdl(t, tempstr)
    elif d == 3:
        t = t.split('-', 2)
        t = [f'-{t[1]}', t[2]]
        tempstr = range_hdl(t, tempstr)
    else:
        coltemp = temp_color(t, u)
        tempstr += f'{coltemp}'
    return f'{tempstr} {u}'


# Wind string formatting functions
def wind_color(wind, unit):
    windcol_d = {
        4: '03', 10: '09', 20: '08', 32: '07'
    }
    if unit == 'km/h':
        w = int(wind)
    elif unit == 'mph':
        w = int(wind) * 1.609344  # Convert mph to km/h.
    elif unit == 'm/s':
        w = int(wind) * 3.6  # Convert m/s to km/h.

    for k, v in windcol_d.items():
        if w < k:
            return f'\x03{v} {wind}\x0F'
    # If the wind speed is higher than the values in the dict use red.
    return f'\x0304 {wind}\x0F'


def wind_format(txt):
    def range_hdl(t, tempstr):
        for idx, i in enumerate(t):
            coltemp = wind_color(i, u)
            tempstr += f'{coltemp}'
            if idx == 0:
                tempstr += ' -'
        return tempstr

    w_ls = txt.split()
    i = w_ls[0]
    w = w_ls[1]
    u = w_ls[2]
    d = w.count('-')
    windstr = f'Wind: {i}'

    if d == 1:
        if not w[0] == '-':
            t = w.split('-')
            windstr = range_hdl(w, windstr)
        else:
            coltemp = wind_color(w, u)
            windstr += f'{coltemp}'
    else:
        coltemp = wind_color(w, u)
        windstr += f'{coltemp}'
    return f'{windstr} {u}'


def colorize(txt):
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
    '  ,\_(   ).  ',
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
    '   \  /      ',
    ' _ /"".-.    ',
    '   \_(   ).  ',
    '    \   /    ',
    '  ‒ (   ) ‒  ',
    '    /   \    ',
    '  ‚ʻ⚡ʻ‚⚡‚ʻ   ',
    '  ‚ʻ‚ʻ⚡ʻ‚ʻ   ',
    '    ⚡ʻ ʻ⚡ʻ ʻ ',
    '     *⚡ *⚡ * ',
    '  ― (   ) ―  ',
    '     `-’     '
)


def wttr(irc, channel, location, unit=False, lang=False):
    if unit:
        u = unit
    else:
        u = ''
    if lang:
        lg = f'&lang={lang}'
    else:
        lg = ''

    url = f'http://wttr.in/{location}?0T{u}{lg}'
    r = requests.get(url, timeout=10).text.splitlines()
    text = ''
    for line in r:
        for i in art:
            line = line.replace(i, '')
        if line:
            line = colorize(line)
            text += f'{line} | '
    text = " ".join(text.split())  # Remove additional spaces.
    text = text.lstrip("Rainfall: ")  # Remove 'Rainfall: ' from the front.
    if "ERROR: Unknown location:" in text:
        text = f'\x0304wttr.in: Location "{location}" could not be found.'
    elif "API key has reached calls per day allowed limit." in text\
         or ("Sorry, we are running out of queries to the weather service at "
             "the moment.") in text:
        text = "\x0304wttr.in: API call limit reached. Try again tomorrow."
    irc.privmsg(channel, text)


def main(i, irc):
    if not i.msg_nocmd:
        msg = (f'Usage: {i.cmd_prefix}{i.cmd} <Location / Airport code /'
               ' @domain / IP address / Area code / GPS coordinates>')
        return irc.privmsg(i.channel, msg)

    q = urllib.parse.quote_plus(i.msg_nocmd)
    if i.msg_nocmd == 'moon' or 'moon@' in i.msg_nocmd:
        return irc.privmsg(i.channel, 'This is not supported yet '
                           '(add ,+US or ,+France for these cities)')

    wttr(irc, i.channel, q)
