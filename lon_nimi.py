# coding=utf-8

# lon nimi is a program that  translates toki pona to english. It runs
# as a service on http://verisimilitudes.net:2001
#
# You can read more about it here: http://verisimilitudes.net/2022-06-13

# Copyright (C) 2022 drastik.org
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

import socket


class Module:
    bot_commands = ["tp", "lon-nimi", "lon_nimi", "toki-pona", "toki_pona"]

    manual = {
        "desc": ("Translate toki pona words to english using lon nimi."
                 " Read more: http://verisimilitudes.net/2022-06-13"),
        "bot_commands": {
            "lon-nimi": {"usage": lambda x: f"{x}lon-nimi <word>",
                         "info": "Translate toki pona word to english.",
                         "alias": ["lon_nimi", "toki-pona", "toki_pona"]}
        }
    }


server = "verisimilitudes.net"
port = 2001


def lon_nimi(word):
    word = word.encode("utf-8")  # lon_nimi is ascii only

    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.sendto(word, (server, port))

    try:
        udp.settimeout(3)  # 3 seconds
        data, addr = udp.recvfrom(1024)
        udp.close()
        return data
    except socket.timeout:
        return None


def main(i, irc):
    msgtarget = i.msg.get_msgtarget()
    nickname = i.msg.get_nickname()
    botcmd = i.msg.get_botcmd()
    prefix = i.msg.get_botcmd_prefix()
    args = i.msg.get_args()

    if not args:
        m = (f'Usage: {prefix}{botcmd} <word>')
        irc.out.notice(msgtarget, m)
        return

    m = lon_nimi(args)
    if m is None:
        m = (f"{nickname}: Seems like there was an error connecting to"
             " the lon nimi server. Please, try again.")
    elif m == b"suli a":
        m = ("lon nimi: Your word is too long.")
    elif m == b"ike a":
        m = ("lon nimi: Your input is not toki pona.")
    elif m == b"ala":
        m = ("lon nimi: This word is unknown but may be valid")
    else:
        m = m.decode("utf-8")
        english, tokipona = [x.strip() for x in m.split(" ", 1)]
        tokipona = ' '.join(tokipona.split())  # Remove excess whitespace
        m = f"lon nimi: {english} -> {tokipona}"

    irc.out.notice(msgtarget, m)
