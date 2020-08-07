#!/usr/bin/env python3
# coding=utf-8

# Virtual D&D style dice rolling

'''
Copyright (c) 2020 Tekdude <tekdude@gmail.com>
Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import random

class Module:
    def __init__(self):
        self.commands = ['roll']
        self.helpmsg = [
            "Usage: .roll <N>d<S>",
            " ",
            "Rolls <N> number of virtual dice, each with <S> number of sides, and returns the results.",
            "Examples: '.roll 1d20' Rolls a single 20 sided die",
            "          '.roll 2d6' Rolls two 6 sided dice"]


def main(i, irc):
    try:
        values = i.msg_nocmd.split('d')
        if len(values) != 2: raise ValueError()
        n_dice = int(values[0])
        n_sides = int(values[1])
        results = [ random.randint(1, n_sides) for i in range(n_dice) ]
        irc.privmsg(
            i.channel,
            f"{i.nickname} rolled {n_dice} {'die' if n_dice == 1 else 'dice'} with {n_sides} sides: {', '.join(map(str, results))}"
        )
    except:
        irc.notice(
            i.nickname,
            f"The dice notation '{i.msg_nocmd}' is invalid. Type '.roll help' to learn about rolling dice."
        )
