#!/usr/bin/env python3
# coding=utf-8

# Text Module for Drastikbot
#
# Transform textual input to various other styles.

'''
Copyright (C) 2019 drastik.org

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


class Module:
    def __init__(self):
        self.commands = ['ae', 'circled_text', 'negative_circled_text',
                         'squared_text', 'negative_squared_text']
        self.helpmsg = [
            "Usage: .ae <Text>",
            "       .circled_text <Text>",
            " ",
            "Transform textual input to various other styles.",
            " ",
            "Example: <Alice> : .ae Hello, World!",
            "         Bot     : Ｈｅｌｌｏ，　Ｗｏｒｌｄ！"]


# https://en.wikipedia.org/wiki/Halfwidth_and_fullwidth_forms_(Unicode_block)
FULLWIDTH_MAP = dict((i, i + 0xFEE0) for i in range(0x21, 0x7F))
FULLWIDTH_MAP[0x20] = 0x3000

# https://en.wikipedia.org/wiki/Enclosed_Alphanumerics
_CIRCLED_NUM_MAP = dict((i, (i - 0x31) + 0x2460) for i in range(0x30, 0x3A))
_CIRCLED_NUM_MAP[0x30] = 0x24EA  # Set the actual Circled digit zero character
_CIRCLED_ALP_U_MAP = dict((i, (i - 0x41) + 0x24B6) for i in range(0x41, 0x5B))
_CIRCLED_ALP_L_MAP = dict((i, (i - 0x61) + 0x24B6) for i in range(0x61, 0x7B))
CIRCLED_MAP = {**_CIRCLED_NUM_MAP, **_CIRCLED_ALP_U_MAP, **_CIRCLED_ALP_L_MAP}

# https://en.wikipedia.org/wiki/Enclosed_Alphanumeric_Supplement
_NEGATIVE_CIRCLED_ALP_U_MAP = dict(
    (i, (i - 0x41) + 0x1F150) for i in range(0x41, 0x5B))
_NEGATIVE_CIRCLED_ALP_L_MAP = dict(
    (i, (i - 0x61) + 0x1F150) for i in range(0x61, 0x7B))
NEGATIVE_CIRCLED_MAP = {
    **_NEGATIVE_CIRCLED_ALP_U_MAP,
    **_NEGATIVE_CIRCLED_ALP_L_MAP
}

_SQUARED_ALP_U_MAP = dict((i, (i - 0x41) + 0x1F130) for i in range(0x41, 0x5B))
_SQUARED_ALP_L_MAP = dict((i, (i - 0x61) + 0x1F130) for i in range(0x61, 0x7B))
SQUARED_MAP = {**_SQUARED_ALP_U_MAP, **_SQUARED_ALP_L_MAP}

_NEGATIVE_SQUARED_ALP_U_MAP = dict(
    (i, (i - 0x41) + 0x1F170) for i in range(0x41, 0x5B))
_NEGATIVE_SQUARED_ALP_L_MAP = dict(
    (i, (i - 0x61) + 0x1F170) for i in range(0x61, 0x7B))
NEGATIVE_SQUARED_MAP = {
    **_NEGATIVE_SQUARED_ALP_U_MAP,
    **_NEGATIVE_SQUARED_ALP_L_MAP
}


def main(i, irc):
    if not i.msg_nocmd:
        return
    s = i.msg_nocmd

    if i.cmd == "ae":
        t = s.translate(FULLWIDTH_MAP)
        if t == s:
            t = s.replace("", " ")[1: -1]
    elif i.cmd == "circled_text":
        t = s.translate(CIRCLED_MAP)
    elif i.cmd == "negative_circled_text":
        t = s.translate(NEGATIVE_CIRCLED_MAP)
    elif i.cmd == "squared_text":
        t = s.translate(SQUARED_MAP)
    elif i.cmd == "negative_squared_text":
        t = s.translate(NEGATIVE_SQUARED_MAP)

    irc.privmsg(i.channel, t)
