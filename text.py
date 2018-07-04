#!/usr/bin/env python3
# coding=utf-8

# Text Module for Drastikbot
#
# Translate text to other unicode maps like widemap.

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


class Module:
    def __init__(self):
        self.commands = ['ae']
        self.helpmsg = [
            "Usage: .ae <Text>",
            " ",
            "Translate text to other unicode maps like widemap.",
            "Example: <Alice> : .ae Hello, World!",
            "         Bot     : Ｈｅｌｌｏ，　Ｗｏｒｌｄ！"]


WIDE_MAP = dict((i, i + 0xFEE0) for i in range(0x21, 0x7F))
WIDE_MAP[0x20] = 0x3000


def main(i, irc):
    if not i.msg_nocmd:
        return
    s = i.msg_nocmd
    t = s.translate(WIDE_MAP)
    if t == s:
        t = s.replace("", " ")[1: -1]
    irc.privmsg(i.channel, t)
