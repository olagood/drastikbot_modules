# coding=utf-8

# Virtual D&D style dice rolling

'''
Copyright (c) 2020 Tekdude <tekdude@gmail.com>
Copyright (c) 2021 drastik <drastik.org> <derezzed@protonmail.com>

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
    bot_commands = ['roll']
    manual = {
        "desc": "Virtual D&D style dice rolling.",
        "bot_commands": {
            "roll": {
                "usage": lambda x: f"{x}roll <n>d<s>",
                "info": ("Rolls <n> number of virtual dice, each with"
                         " <S> number of sides and returns the result"
                         ". Example: \".roll 2d6\" rolls two six sided"
                         " dice.")}
        }
    }


def main(i, irc):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    values = args.split('d')
    if len(values) != 2:
        m = f"Usage: {prefix}roll <n>d<s>"
        irc.out.notice(msgtarget, m)
        return

    n_dice = int(values[0])
    n_sides = int(values[1])

    if n_dice > 1000 or n_sides > 1000:
        m = f"{nickname}: Too many dice or sides given."
        irc.notice(msgtarget, m)
        return

    results = [random.randint(1, n_sides) for i in range(n_dice)]

    limit = 15  # TODO: Let chanops choose the limit

    if len(results) > limit:
        results_p = ", ".join(map(str, results[:limit])) + "..."
    else:
        results_p = ", ".join(map(str, results))

    m = (f"{nickname} rolled {n_dice} {'die' if n_dice == 1 else 'dice'}"
         f" with {n_sides} sides: {results_p} (Total: {sum(results)})")

    irc.out.notice(msgtarget, m)
