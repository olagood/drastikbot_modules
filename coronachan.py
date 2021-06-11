# coding=utf-8

# Covid19 module for drastikbot2
#
# Useful stats related to 2019-nCov
#
# Depends
# -------
# pip: requests, bs4

# Copyright (C) 2019, 2021 drastik.org
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

import requests
from bs4 import BeautifulSoup


class Module:
    bot_commands = ["corona", "coronachan"]
    manual = {
        "desc": "Useful stats related to 2019-nCov",
        "bot_commands": {
            "corona": {"usage": ".corona",
                       "alias": ["coronachan"]},
            "coronachan": {"usage": ".coronachan",
                           "alias": ["corona"]}
        }
    }


def extract_from_page(text, soup):
    return soup.find(text=text).parent.parent.find(
        "div", {"class": "maincounter-number"}).find("span").text


def main(i, irc):
    msgtarget = i.msg.get_msgtarget()

    url = 'https://www.worldometers.info/coronavirus/'
    page = requests.get(url)

    soup = BeautifulSoup(page.text, "html.parser")

    cases = extract_from_page("Coronavirus Cases:", soup)
    cases_f = float(cases.replace(',', ''))

    deaths = extract_from_page("Deaths:", soup)
    deaths_f = float(deaths.replace(',', ''))

    recovered = extract_from_page("Recovered:", soup)
    recovered_f = float(recovered.replace(',', ''))

    death_rate_resolved = round(deaths_f /  (deaths_f + recovered_f) * 100, 1)
    death_rate_total = round(deaths_f / cases_f * 100, 1)

    m = (f"\x02Total cases:\x0F {cases}"
         f" | \x02Dead:\x0F \x0304{deaths}\x0F"
         f" | \x02Recovered:\x0F \x0303{recovered}\x0F"
         f" | \x02Death rate (resolved):\x0F {death_rate_resolved}%"
         f" | \x02Death rate (total):\x0F {death_rate_total}%"
         f" | \x02Source:\x0F {url}"
         " | Other resources: https://coronavirus.jhu.edu/map.html")

    irc.out.notice(msgtarget, m)
