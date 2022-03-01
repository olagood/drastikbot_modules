# coding=utf-8

""" binance API module for drastikbot. Get cryptocurrency prices.

drastikbot version: 2.2
module     version: 0.0

license: AGPLv3

depends: requests
"""

# Copyright (C) 2022 drastik.org
#
# This file is part of drastikbot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, version 3 only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import requests  # type: ignore


class Module:
    bot_commands = ["coin", "binance"]
    manual = {
        "desc": "Get cryptocurrency prices from https://www.binance.com",
        "bot_commands": {
            "coin": {"usage": lambda x: f"{x}coin <coin> [--in <coin>]",
                     "info": "--in: Currency for the price of the coin",
                     "alias": ["binance"]}
        }
    }


api = "https://api.binance.com"


def main(i, irc):
    msgtarget = i.msg.get_msgtarget()
    args = i.msg.get_args()
    argv = args.split()
    argc = len(argv)

    cmd = i.msg.get_botcmd()
    pfx = i.msg.get_botcmd_prefix()
    usage = f"Usage: {pfx}{cmd} <coin> [--in <coin>]"

    if not argv or (argc != 1 and argc != 3):
        irc.out.notice(msgtarget, usage)
        return

    base = argv[0]
    quote = "USDT"

    if argc == 3:
        if "--in" in argv[1]:
            quote = argv[2]
        else:
            irc.out.notice(msgtarget, usage)
            return

    if quote.upper() == "USD":
        quote = "USDT"

    code, d = api_ticker_24hr(base, quote)
    if code == 0:
        # avg = "%.2f" % float(d["avg"])
        # now = "%.2f" % float(d["now"])
        avg = d["avg"]
        now = d["now"]
        m = (f"Binance :: \x0311{d['name']}\x0F"
             f" \x02 Price (24h)\x0F: \x0311{avg} {d['quote']}\x0F"
             f" | \x02Price (Now)\x0F: \x0311{now} {d['quote']}\x0F"
             f" | \x02Change (24h)\x0F: {d['%24']}")
    else:
        m = d

    irc.out.notice(msgtarget, m)


def api_ping():
    r = requests.get(f"{api}/api/v3/ping", timeout=30)
    if r.json() == {}:
        return True, "ok"


def api_ticker_24hr(base, quote="USDT"):
    base = base.upper()
    quote = quote.upper()

    u = f"{api}/api/v3/ticker/24hr?symbol={base}{quote}"
    r = requests.get(u, timeout=20)
    j = r.json()

    if r.status_code != 200:
        if j["code"] == -1121:
            return j["code"], "Invalid symbol. Is the currency code correct?"
        else:
            return j["code"], r["msg"]

    p24 = j["priceChangePercent"]

    return 0, {
        "name": name_format(base),
        "quote": quote_format(quote),
        "avg": j["weightedAvgPrice"],
        "%24": f"\x0304{p24} %\x0F" if "-" in p24 else f"\x0303{p24} %\x0F",
        "now": j["bidPrice"]
    }


NAME_FMT = {
    "BTC": "Bitcoin",
    "LTC": "Litecoin",
    "ETH": "Etherium"
}


def name_format(code):
    name = NAME_FMT.get(code, False)
    if not name:
        return code
    else:
        return f"{name} ({code})"


QUOTE_FMT = {
    "USDT": "USD"
}


def quote_format(quote):
    return QUOTE_FMT.get(quote, quote)
